from fastapi import APIRouter
from app.api.endpoints import (
    health,
    datasets,
    analyst,
    workflows,
    visualizations,
    reports,
    settings_api,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(analyst.router, prefix="/analyst", tags=["AI Analyst"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(visualizations.router, prefix="/visualizations", tags=["Visualizations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(settings_api.router, prefix="/settings", tags=["Settings"])
