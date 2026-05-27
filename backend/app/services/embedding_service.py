import hashlib
import logging
import os
import re
from typing import Any

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_chroma_client = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def _get_chroma():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _chroma_client


def _get_collection(repo_id: int):
    client = _get_chroma()
    return client.get_or_create_collection(
        name=f"repo_{repo_id}",
        metadata={"hnsw:space": "cosine"},
    )


_BOUNDARY_RE = re.compile(
    r"^(class |def |async def )", re.MULTILINE
)

_LANG_BY_EXT: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".jsx": "javascript", ".java": "java",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".cpp": "cpp",
    ".c": "c", ".h": "c", ".cs": "csharp", ".php": "php",
    ".sh": "shell", ".md": "markdown", ".yml": "yaml", ".yaml": "yaml",
    ".json": "json", ".html": "html", ".css": "css",
}


def _detect_language(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    return _LANG_BY_EXT.get(ext, "text")


def _make_doc_id(file_path: str, start_line: int, end_line: int) -> str:
    raw = f"{file_path}:{start_line}-{end_line}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def chunk_code(
    content: str,
    file_path: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> list[dict[str, Any]]:
    """Split code into chunks by function/class boundaries where possible,
    falling back to line-based chunking."""
    if not content.strip():
        return []

    lines = content.splitlines(keepends=True)

    boundary_indices: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("class "):
            boundary_indices.append((idx, "class"))
        elif stripped.startswith(("def ", "async def ")):
            boundary_indices.append((idx, "function"))

    chunks: list[dict[str, Any]] = []

    if boundary_indices:
        if boundary_indices[0][0] > 0:
            preamble = "".join(lines[: boundary_indices[0][0]])
            if preamble.strip():
                chunks.append({
                    "content": preamble,
                    "file_path": file_path,
                    "start_line": 1,
                    "end_line": boundary_indices[0][0],
                    "chunk_type": "module",
                })

        for i, (start_idx, kind) in enumerate(boundary_indices):
            end_idx = (
                boundary_indices[i + 1][0]
                if i + 1 < len(boundary_indices)
                else len(lines)
            )
            block = "".join(lines[start_idx:end_idx])

            if len(block) <= chunk_size:
                chunks.append({
                    "content": block,
                    "file_path": file_path,
                    "start_line": start_idx + 1,
                    "end_line": end_idx,
                    "chunk_type": kind,
                })
            else:
                sub_chunks = _line_chunk(
                    lines[start_idx:end_idx],
                    file_path,
                    offset=start_idx,
                    chunk_size=chunk_size,
                    overlap=overlap,
                    chunk_type=kind,
                )
                chunks.extend(sub_chunks)
    else:
        chunks = _line_chunk(
            lines, file_path, offset=0,
            chunk_size=chunk_size, overlap=overlap, chunk_type="module",
        )

    return chunks


def _line_chunk(
    lines: list[str],
    file_path: str,
    offset: int,
    chunk_size: int,
    overlap: int,
    chunk_type: str,
) -> list[dict[str, Any]]:
    """Fall-back line-based chunker with overlap."""
    chunks: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        end = i
        size = 0
        while end < len(lines) and size + len(lines[end]) <= chunk_size:
            size += len(lines[end])
            end += 1
        if end == i:
            end = i + 1

        block = "".join(lines[i:end])
        chunks.append({
            "content": block,
            "file_path": file_path,
            "start_line": offset + i + 1,
            "end_line": offset + end,
            "chunk_type": chunk_type,
        })
        i = max(i + 1, end - overlap)
    return chunks


async def generate_embeddings(
    repo_id: int, chunks: list[dict[str, Any]]
) -> dict[str, Any]:
    """Generate embeddings for code chunks and store in ChromaDB.

    Processes in batches of 100 for memory efficiency.
    """
    if not chunks:
        return {
            "repo_id": repo_id,
            "chunks_processed": 0,
            "status": "completed",
            "message": "No chunks to embed",
        }

    model = _get_model()
    collection = _get_collection(repo_id)
    batch_size = 100
    total_stored = 0

    try:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]

            texts = [c["content"] for c in batch]
            embeddings = model.encode(texts, show_progress_bar=False).tolist()

            ids: list[str] = []
            documents: list[str] = []
            metadatas: list[dict[str, Any]] = []
            emb_list: list[list[float]] = []

            for chunk, emb in zip(batch, embeddings):
                doc_id = _make_doc_id(
                    chunk["file_path"], chunk["start_line"], chunk["end_line"]
                )
                ids.append(doc_id)
                documents.append(chunk["content"])
                emb_list.append(emb)
                metadatas.append({
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "chunk_type": chunk.get("chunk_type", "module"),
                    "language": _detect_language(chunk["file_path"]),
                })

            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=emb_list,
                metadatas=metadatas,
            )
            total_stored += len(batch)
            logger.info(
                "Repo %s: embedded %d / %d chunks",
                repo_id, total_stored, len(chunks),
            )

        return {
            "repo_id": repo_id,
            "chunks_processed": total_stored,
            "status": "completed",
            "message": f"Successfully embedded {total_stored} chunks",
        }
    except Exception as exc:
        logger.exception("Embedding generation failed for repo %s", repo_id)
        return {
            "repo_id": repo_id,
            "chunks_processed": total_stored,
            "status": "failed",
            "message": str(exc),
        }


async def get_embedding_status(repo_id: int) -> dict[str, Any]:
    """Check how many chunks are stored for a repo in ChromaDB."""
    try:
        collection = _get_collection(repo_id)
        count = collection.count()
        return {
            "repo_id": repo_id,
            "total_chunks": count,
            "embedded_chunks": count,
            "status": "completed" if count > 0 else "pending",
        }
    except Exception:
        return {
            "repo_id": repo_id,
            "total_chunks": 0,
            "embedded_chunks": 0,
            "status": "pending",
        }


async def search_similar(
    repo_id: int, query: str, top_k: int = 5
) -> list[dict[str, Any]]:
    """Encode query and search ChromaDB for the most similar chunks."""
    try:
        client = _get_chroma()
        try:
            collection = client.get_collection(name=f"repo_{repo_id}")
        except Exception:
            logger.warning("No embeddings collection found for repo %s", repo_id)
            return []

        count = collection.count()
        if count == 0:
            return []

        model = _get_model()
        query_embedding = model.encode([query], show_progress_bar=False).tolist()[0]

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict[str, Any]] = []
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = 1.0 - distance
            hits.append({
                "file_path": meta.get("file_path", ""),
                "content": doc,
                "score": round(score, 4),
                "metadata": {
                    "start_line": meta.get("start_line"),
                    "end_line": meta.get("end_line"),
                    "chunk_type": meta.get("chunk_type"),
                    "language": meta.get("language"),
                },
            })

        return hits
    except Exception:
        logger.exception("Similarity search failed for repo %s", repo_id)
        return []


async def delete_repo_embeddings(repo_id: int) -> bool:
    """Delete the ChromaDB collection for a repo."""
    try:
        client = _get_chroma()
        client.delete_collection(name=f"repo_{repo_id}")
        logger.info("Deleted embeddings collection for repo %s", repo_id)
        return True
    except Exception:
        logger.exception("Failed to delete collection for repo %s", repo_id)
        return False
