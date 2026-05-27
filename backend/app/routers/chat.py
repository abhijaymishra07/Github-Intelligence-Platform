from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.repository import Repository
from app.services.llm_service import ask_about_repo

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    sources: list[str]
    model: str


@router.post("/{repo_id}/ask", response_model=ChatResponse)
async def ask_question(
    repo_id: int, payload: ChatRequest, db: Session = Depends(get_db)
):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not ready for queries (status: {repo.status})",
        )

    result = await ask_about_repo(repo_id, payload.question)
    return ChatResponse(**result)
