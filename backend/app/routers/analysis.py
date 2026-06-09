from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.repository import Repository
from app.services.analysis_service import (
    get_complexity_analysis,
    get_dependency_analysis,
    get_repo_summary,
    detect_security_issues,
    find_dead_code,
)

router = APIRouter()


def _get_repo_or_404(repo_id: int, db: Session) -> Repository:
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/summary")
async def repo_summary(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await get_repo_summary(repo_id)


@router.get("/{repo_id}/complexity")
async def repo_complexity(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await get_complexity_analysis(repo_id)


@router.get("/{repo_id}/dependencies")
async def repo_dependencies(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await get_dependency_analysis(repo_id)


@router.get("/{repo_id}/security")
async def repo_security(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await detect_security_issues(repo_id)


@router.get("/{repo_id}/dead-code")
async def repo_dead_code(repo_id: int, db: Session = Depends(get_db)):
    _get_repo_or_404(repo_id, db)
    return await find_dead_code(repo_id)
