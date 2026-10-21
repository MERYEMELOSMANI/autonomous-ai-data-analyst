import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.database.models import AnalysisSessionModel, AnalysisMessageModel, WorkflowRunModel
from app.services.dataset_service import dataset_service
from app.schemas.analysis import AnalysisQueryRequest, AnalysisSessionResponse, AnalysisMessageResponse
from app.agents.graph import stream_agent_workflow
from app.core.security import check_prompt_injection

router = APIRouter()

@router.post("/sessions", response_model=AnalysisSessionResponse)
async def create_session(dataset_id: str = Query(...), title: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    """Create a new conversational analysis session for a dataset."""
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    session = AnalysisSessionModel(
        id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        title=title or f"Analysis of {dataset.name}"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return AnalysisSessionResponse(
        id=session.id,
        dataset_id=session.dataset_id,
        dataset_name=dataset.name,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[]
    )

@router.get("/sessions", response_model=List[AnalysisSessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all previous analysis sessions with dataset names."""
    result = await db.execute(
        select(AnalysisSessionModel).order_by(AnalysisSessionModel.updated_at.desc())
    )
    sessions = result.scalars().all()
    out = []
    for s in sessions:
        ds = await dataset_service.get_dataset_by_id(s.dataset_id, db)
        out.append(AnalysisSessionResponse(
            id=s.id,
            dataset_id=s.dataset_id,
            dataset_name=ds.name if ds else "Unknown Dataset",
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            messages=[]
        ))
    return out

@router.get("/sessions/{session_id}", response_model=AnalysisSessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get analysis session with all messages, verifiable evidence, and charts."""
    result = await db.execute(select(AnalysisSessionModel).where(AnalysisSessionModel.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ds = await dataset_service.get_dataset_by_id(session.dataset_id, db)
    
    # Load messages
    msg_result = await db.execute(
        select(AnalysisMessageModel).where(AnalysisMessageModel.session_id == session_id).order_by(AnalysisMessageModel.created_at.asc())
    )
    messages = msg_result.scalars().all()

    formatted_msgs = []
    for m in messages:
        formatted_msgs.append(AnalysisMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            evidence=m.evidence_json or [],
            visualizations=m.visualizations_json or [],
            timeline=m.timeline_json or [],
            status=m.status,
            workflow_id=m.workflow_id,
            created_at=m.created_at
        ))

    return AnalysisSessionResponse(
        id=session.id,
        dataset_id=session.dataset_id,
        dataset_name=ds.name if ds else "Unknown Dataset",
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=formatted_msgs
    )

@router.get("/stream")
async def stream_analysis(
    dataset_id: str = Query(...),
    query: str = Query(...),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Server-Sent Events (SSE) live streaming endpoint.
    Streams real-time agent execution events, active tool calls, verification diffs,
    and saves the completed response to the session history.
    """
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if session_id:
        session = await db.get(AnalysisSessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Analysis session not found")
        if session.dataset_id != dataset_id:
            raise HTTPException(status_code=400, detail="Analysis session belongs to another dataset")

    is_injection, injection_msg = check_prompt_injection(query)
    if is_injection:
        raise HTTPException(status_code=400, detail=injection_msg)

    dataset_service.ensure_duckdb_registered(dataset)

    # Ensure session exists
    if not session_id:
        new_session = AnalysisSessionModel(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            title=f"Analysis: {query[:30]}..."
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.id

    # Record User Message
    user_msg = AnalysisMessageModel(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=query,
        status="completed"
    )
    db.add(user_msg)
    await db.commit()

    workflow_id = str(uuid.uuid4())

    initial_state = {
        "session_id": session_id,
        "workflow_id": workflow_id,
        "query": query,
        "dataset_id": dataset.id,
        "table_name": dataset.duckdb_table_name,
        "dataset_name": dataset.name,
        "schema_info": dataset.columns_json or [],
        "sample_rows": [],
        "quality_summary": dataset.quality_report_json or {},
    }

    async def event_generator():
        final_workflow_data = None
        try:
            async for update in stream_agent_workflow(initial_state):
                if update.get("event") == "workflow_finished":
                    final_workflow_data = update
                yield f"data: {json.dumps(update)}\n\n"

            # Persist assistant response and workflow run in database
            if final_workflow_data:
                assistant_msg = AnalysisMessageModel(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="assistant",
                    content=final_workflow_data.get("final_response", ""),
                    evidence_json=final_workflow_data.get("evidence", []),
                    visualizations_json=final_workflow_data.get("visualizations", []),
                    timeline_json=final_workflow_data.get("timeline", []),
                    status="completed",
                    workflow_id=workflow_id
                )
                db.add(assistant_msg)

                wf_run = WorkflowRunModel(
                    id=workflow_id,
                    session_id=session_id,
                    dataset_id=dataset_id,
                    query=query,
                    status="completed",
                    plan_json=initial_state.get("plan", []),
                    steps_json=final_workflow_data.get("timeline", []),
                    duration_ms=sum([s.get("duration_ms", 0) for s in final_workflow_data.get("timeline", [])])
                )
                db.add(wf_run)
                await db.commit()

        except Exception as e:
            error_payload = {
                "event": "workflow_error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
