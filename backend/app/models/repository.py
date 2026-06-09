from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(String(500), unique=True)
    branch: Mapped[str] = mapped_column(String(100), default="main")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    stars: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(
        String(20), default="cloning", index=True
    )
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    files: Mapped[list["RepositoryFile"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), index=True
    )
    path: Mapped[str] = mapped_column(String(1000))
    filename: Mapped[str] = mapped_column(String(255))
    extension: Mapped[str | None] = mapped_column(String(20), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    parsed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    repository: Mapped["Repository"] = relationship(back_populates="files")
