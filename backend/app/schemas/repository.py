from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RepoCreate(BaseModel):
    url: HttpUrl
    branch: str = "main"


class RepoResponse(BaseModel):
    id: int
    name: str
    url: str
    branch: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    status: str
    file_count: int = 0
    total_size: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepoStatus(BaseModel):
    id: int
    name: str
    status: str
    file_count: int = 0
    total_size: int = 0

    model_config = {"from_attributes": True}


class FileInfo(BaseModel):
    id: int
    path: str
    filename: str
    extension: str | None = None
    size: int = 0
    language: str | None = None
    parsed: bool = False

    model_config = {"from_attributes": True}
