from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.database.models import WorkflowRunModel
from app.services.dataset_service import dataset_service

router = APIRouter()

@router.get("")
async def list_workflows(db: AsyncSession = Depends(get_db)):
    """List all executed agent workflows."""
    result = await db.execute(select(WorkflowRunModel).order_by(WorkflowRunModel.created_at.desc()))
    runs = result.scalars().all()
    out = []
    for r in runs:
        ds = await dataset_service.get_dataset_by_id(r.dataset_id, db)
        out.append({
            "id": r.id,
            "session_id": r.session_id,
            "dataset_id": r.dataset_id,
            "dataset_name": ds.name if ds else "Unknown",
            "query": r.query,
            "status": r.status,
            "duration_ms": r.duration_ms,
            "steps_count": len(r.steps_json) if r.steps_json else 0,
            "created_at": r.created_at
        })
    return out

@router.get("/{workflow_id}")
async def get_workflow_details(workflow_id: str, db: AsyncSession = Depends(get_db)):
    """Get full execution trace of an agent workflow."""
    result = await db.execute(select(WorkflowRunModel).where(WorkflowRunModel.id == workflow_id))
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")

    ds = await dataset_service.get_dataset_by_id(run.dataset_id, db)
    return {
        "id": run.id,
        "session_id": run.session_id,
        "dataset_id": run.dataset_id,
        "dataset_name": ds.name if ds else "Unknown",
        "query": run.query,
        "status": run.status,
        "plan": run.plan_json or [],
        "steps": run.steps_json or [],
        "duration_ms": run.duration_ms,
        "error": run.error,
        "created_at": run.created_at
    }
