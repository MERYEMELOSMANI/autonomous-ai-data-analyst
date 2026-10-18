from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.database.models import AnalysisMessageModel, AnalysisSessionModel
from app.services.dataset_service import dataset_service

router = APIRouter()

@router.get("")
async def list_all_visualizations(db: AsyncSession = Depends(get_db)):
    """Retrieve all Plotly visualizations generated across sessions."""
    result = await db.execute(
        select(AnalysisMessageModel)
        .where(AnalysisMessageModel.visualizations_json.isnot(None))
        .order_by(AnalysisMessageModel.created_at.desc())
    )
    messages = result.scalars().all()
    all_viz = []
    for m in messages:
        if m.visualizations_json:
            for viz in m.visualizations_json:
                viz_copy = dict(viz)
                viz_copy["session_id"] = m.session_id
                viz_copy["created_at"] = m.created_at.isoformat()
                all_viz.append(viz_copy)
    return all_viz
