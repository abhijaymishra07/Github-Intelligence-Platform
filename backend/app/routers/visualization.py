from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.repository import Repository
from app.services.analysis_service import get_complexity_heatmap, get_dependency_graph

router = APIRouter()


def _get_repo_or_404(repo_id: int, db: Session) -> Repository:
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/dependency-graph")
async def dependency_graph(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await get_dependency_graph(repo_id)


@router.get("/{repo_id}/complexity-heatmap")
async def complexity_heatmap(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await get_complexity_heatmap(repo_id)
