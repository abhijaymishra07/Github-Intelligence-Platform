import logging
import os
from typing import Any

from app.config import settings
from app.services import embedding_service

logger = logging.getLogger(__name__)

MAX_FILE_LINES = 300
MAX_CONTEXT_CHARS = 12000


def _read_file_from_repo(repo_name: str, file_path: str) -> str | None:
    """Read a source file from the cloned repo on disk."""
    full_path = os.path.join(settings.REPOS_DIR, repo_name, file_path)
    try:
        with open(full_path, "r", errors="replace") as f:
            lines = f.readlines()
        if len(lines) > MAX_FILE_LINES:
            return "".join(lines[:MAX_FILE_LINES]) + f"\n... (truncated, {len(lines)} total lines)"
        return "".join(lines)
    except Exception:
        return None


def _get_repo_name(repo_id: int) -> str | None:
    """Look up the repository name from the database."""
    try:
        from app.database import SessionLocal
        from app.models.repository import Repository
        db = SessionLocal()
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        db.close()
        return repo.name if repo else None
    except Exception:
        return None


async def retrieve_context(
    repo_id: int, query: str, top_k: int = 8
) -> list[dict[str, Any]]:
    """Retrieve relevant code chunks, then expand them with full file content.

    Fetches extra candidates, deduplicates by file, and reads the actual
    source files from disk so the LLM gets complete file context.
    """
    try:
        candidates = await embedding_service.search_similar(
            repo_id, query, top_k=top_k * 4
        )

        seen_files: dict[str, int] = {}
        max_per_file = 2
        context_chunks: list[dict[str, Any]] = []

        for hit in candidates:
            fp = hit["file_path"]
            if seen_files.get(fp, 0) >= max_per_file:
                continue
            seen_files[fp] = seen_files.get(fp, 0) + 1

            meta = hit.get("metadata", {})
            context_chunks.append({
                "file_path": fp,
                "content": hit["content"],
                "score": hit["score"],
                "start_line": meta.get("start_line"),
                "end_line": meta.get("end_line"),
                "chunk_type": meta.get("chunk_type"),
                "language": meta.get("language"),
            })

            if len(context_chunks) >= top_k:
                break

        repo_name = _get_repo_name(repo_id)
        if repo_name:
            expanded = _expand_with_full_files(context_chunks, repo_name)
            return expanded

        return context_chunks
    except Exception:
        logger.exception("Context retrieval failed for repo %s", repo_id)
        return []


def _expand_with_full_files(
    chunks: list[dict[str, Any]], repo_name: str
) -> list[dict[str, Any]]:
    """Replace small chunks with full file content for better LLM context.

    Only expands files that fit within the character budget.
    """
    expanded: list[dict[str, Any]] = []
    files_expanded: set[str] = set()
    total_chars = 0

    for chunk in chunks:
        fp = chunk["file_path"]

        if fp in files_expanded:
            continue

        full_content = _read_file_from_repo(repo_name, fp)
        if full_content and total_chars + len(full_content) <= MAX_CONTEXT_CHARS:
            line_count = full_content.count("\n") + 1
            expanded.append({
                "file_path": fp,
                "content": full_content,
                "score": chunk["score"],
                "start_line": 1,
                "end_line": line_count,
                "chunk_type": "full_file",
                "language": chunk.get("language"),
            })
            files_expanded.add(fp)
            total_chars += len(full_content)
        else:
            if total_chars + len(chunk["content"]) <= MAX_CONTEXT_CHARS:
                expanded.append(chunk)
                total_chars += len(chunk["content"])

    return expanded


def _format_code_block(chunk: dict[str, Any]) -> str:
    """Format a single chunk as a labelled code block for the prompt."""
    file_path = chunk.get("file_path", "unknown")
    start = chunk.get("start_line", "?")
    end = chunk.get("end_line", "?")
    lang = chunk.get("language", "")
    content = chunk.get("content", "")
    chunk_type = chunk.get("chunk_type", "")

    if chunk_type == "full_file":
        header = f"File: {file_path}  (complete file, {end} lines)"
    else:
        header = f"File: {file_path}  (lines {start}-{end})"

    fence = f"```{lang}" if lang else "```"
    return f"{header}\n{fence}\n{content}\n```"


async def build_prompt(
    query: str,
    context_chunks: list[dict[str, Any]],
    repo_name: str = "",
) -> str:
    """Build a well-structured prompt for the LLM from query and retrieved context."""
    repo_label = f" for the **{repo_name}** repository" if repo_name else ""

    system_section = (
        "You are an expert code analysis assistant{repo_label}. "
        "You have access to the COMPLETE source files from the repository. "
        "Use the code context provided below to answer the user's question thoroughly. "
        "When referencing code, cite the file path and line numbers. "
        "You CAN and SHOULD read and explain any part of the provided files."
    ).format(repo_label=repo_label)

    if context_chunks:
        formatted = "\n\n".join(_format_code_block(c) for c in context_chunks)
        context_section = f"## Source Code Context\n\n{formatted}"
    else:
        context_section = (
            "## Code Context\n\n"
            "No relevant code chunks were found for this query. "
            "Answer based on general knowledge if possible, "
            "and note that repository-specific context is unavailable."
        )

    prompt = (
        f"{system_section}\n\n"
        f"{context_section}\n\n"
        f"## Question\n\n{query}"
    )

    return prompt
