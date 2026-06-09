import hashlib
import os
import shutil
from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, Repo

from app.config import settings

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", ".eggs", "dist", "build", ".mypy_cache", ".pytest_cache",
}

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".vue", ".svelte", ".html", ".css", ".scss",
    ".sql", ".sh", ".bash", ".yaml", ".yml", ".json", ".toml",
    ".xml", ".md", ".txt", ".rst", ".cfg", ".ini", ".env",
}

EXTENSION_LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "JavaScript", ".tsx": "TypeScript", ".java": "Java",
    ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
    ".h": "C", ".hpp": "C++", ".cs": "C#", ".rb": "Ruby",
    ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
    ".scala": "Scala", ".vue": "Vue", ".svelte": "Svelte",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".toml": "TOML", ".xml": "XML", ".md": "Markdown",
}


def _extract_repo_name(url: str) -> str:
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def clone_repository(
    url: str, branch: str = "main", target_dir: str | None = None
) -> dict:
    repo_name = _extract_repo_name(url)
    if target_dir is None:
        target_dir = os.path.join(settings.REPOS_DIR, repo_name)

    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    os.makedirs(target_dir, exist_ok=True)

    try:
        repo = Repo.clone_from(url, target_dir, branch=branch)
    except GitCommandError as e:
        # Retry without explicit branch (some repos use master)
        if "not found" in str(e).lower() or "couldn't find" in str(e).lower():
            repo = Repo.clone_from(url, target_dir)
        else:
            raise

    return {
        "name": repo_name,
        "path": target_dir,
        "branch": str(repo.active_branch),
        "commit": str(repo.head.commit.hexsha[:12]),
        "description": (
            repo.description if repo.description != "Unnamed repository" else None
        ),
    }


def get_file_tree(repo_path: str) -> list[dict]:
    files: list[dict] = []
    base = Path(repo_path)

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in filenames:
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                stat = filepath.stat()
                content_hash = _hash_file(filepath)
            except OSError:
                continue

            files.append({
                "path": str(filepath.relative_to(base)),
                "filename": filename,
                "extension": ext,
                "size": stat.st_size,
                "language": EXTENSION_LANGUAGE_MAP.get(ext),
                "content_hash": content_hash,
            })

    return files


def get_repo_metadata(repo_path: str) -> dict:
    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        return {"error": "Not a valid git repository"}

    files = get_file_tree(repo_path)
    language_counts: dict[str, int] = {}
    for f in files:
        lang = f.get("language")
        if lang:
            language_counts[lang] = language_counts.get(lang, 0) + 1

    primary_language = (
        max(language_counts, key=language_counts.get) if language_counts else None
    )

    return {
        "branch": str(repo.active_branch),
        "commit_count": sum(1 for _ in repo.iter_commits()),
        "file_count": len(files),
        "total_size": sum(f["size"] for f in files),
        "primary_language": primary_language,
        "language_breakdown": language_counts,
    }


def delete_repository(repo_path: str) -> bool:
    if os.path.exists(repo_path):
        shutil.rmtree(repo_path)
        return True
    return False


def _hash_file(filepath: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except OSError:
        return ""
    return h.hexdigest()
