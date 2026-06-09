import os
import re
from datetime import datetime, timezone


def sanitize_repo_name(name: str) -> str:
    """Remove special characters and normalize a repository name."""
    name = re.sub(r"[^\w\-.]", "_", name)
    return name.strip("_").lower()


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_directory(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
