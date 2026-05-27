import os
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.repository import Repository, RepositoryFile
from app.schemas.repository import FileInfo, RepoCreate, RepoResponse, RepoStatus
from app.services.git_service import (
    clone_repository,
    delete_repository,
    get_file_tree,
    get_repo_metadata,
)

router = APIRouter()


def _process_repo_background(repo_id: int, url: str, branch: str) -> None:
    """Clone, parse, and index a repo in a background thread."""
    import asyncio
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return

        repo.status = "cloning"
        db.commit()

        result = clone_repository(url, branch)
        repo_path = result["path"]

        repo.status = "parsing"
        repo.branch = result["branch"]
        repo.description = result.get("description")
        db.commit()

        files = get_file_tree(repo_path)
        metadata = get_repo_metadata(repo_path)

        for f in files:
            db_file = RepositoryFile(
                repo_id=repo_id,
                path=f["path"],
                filename=f["filename"],
                extension=f["extension"],
                size=f["size"],
                language=f["language"],
                content_hash=f["content_hash"],
            )
            db.add(db_file)

        repo.file_count = metadata["file_count"]
        repo.total_size = metadata["total_size"]
        repo.language = metadata.get("primary_language")
        db.commit()

        repo.status = "embedding"
        db.commit()

        try:
            from app.services.parser_service import parse_repository
            from app.services.embedding_service import chunk_code, generate_embeddings

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            parse_result = loop.run_until_complete(parse_repository(repo_path))

            all_chunks = []
            for file_info in files:
                file_full_path = os.path.join(repo_path, file_info["path"])
                try:
                    with open(file_full_path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if content.strip():
                        chunks = chunk_code(content, file_info["path"])
                        all_chunks.extend(chunks)
                except (OSError, UnicodeDecodeError):
                    continue

            if all_chunks:
                loop.run_until_complete(generate_embeddings(repo_id, all_chunks))

            loop.close()
        except Exception:
            pass

        repo.status = "ready"
        db.commit()

    except Exception as e:
        db.rollback()
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if repo:
            repo.status = "error"
            repo.description = str(e)[:500]
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=RepoResponse, status_code=201)
def upload_repository(payload: RepoCreate, db: Session = Depends(get_db)):
    url = str(payload.url).rstrip("/")

    existing = db.query(Repository).filter(Repository.url == url).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Repository already exists"
        )

    repo_name = url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    repo = Repository(
        name=repo_name,
        url=url,
        branch=payload.branch,
        status="cloning",
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)

    thread = Thread(
        target=_process_repo_background,
        args=(repo.id, url, payload.branch),
        daemon=True,
    )
    thread.start()

    return repo


@router.get("/", response_model=list[RepoResponse])
def list_repositories(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    return db.query(Repository).offset(skip).limit(limit).all()


@router.get("/{repo_id}/status", response_model=RepoStatus)
def get_repository_status(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/files", response_model=list[FileInfo])
def get_repository_files(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo.files


@router.delete("/{repo_id}", status_code=204)
def remove_repository(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_path = os.path.join(
        settings.REPOS_DIR, repo.name
    )
    delete_repository(repo_path)

    db.delete(repo)
    db.commit()
