import os
import re
import ast
import json
from typing import Any
from collections import defaultdict

from app.config import settings
from app.database import SessionLocal
from app.models.repository import Repository, RepositoryFile

EXTENSION_LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".tsx": "TypeScript (React)", ".jsx": "JavaScript (React)",
    ".java": "Java", ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".cpp": "C++", ".h": "C/C++ Header",
    ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sql": "SQL", ".sh": "Shell", ".md": "Markdown",
    ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".xml": "XML",
}

FRAMEWORK_INDICATORS = {
    "FastAPI": ["from fastapi", "import fastapi", "FastAPI()"],
    "Flask": ["from flask", "import flask", "Flask(__name__)"],
    "Django": ["django.conf", "INSTALLED_APPS", "from django"],
    "React": ["from react", "import React", "useState", "useEffect"],
    "Next.js": ["next/", "getServerSideProps", "getStaticProps"],
    "Express": ["require('express')", "from 'express'", "express()"],
    "Spring Boot": ["@SpringBootApplication", "springframework"],
    "Vue": ["from 'vue'", "createApp", "defineComponent"],
    "Angular": ["@angular/core", "@Component", "@NgModule"],
}

SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9]{16,}['\"]", "API Key", "high"),
    (r"(?i)(secret|password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{8,}['\"]", "Hardcoded Secret", "high"),
    (r"(?i)(token)\s*[=:]\s*['\"][a-zA-Z0-9_\-\.]{20,}['\"]", "Hardcoded Token", "high"),
    (r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*['\"][^'\"]+['\"]", "AWS Credential", "critical"),
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "Hardcoded IP", "low"),
    (r"(?i)(mongodb|postgres|mysql|redis)://[^\s'\"]+", "Database URL", "medium"),
]

UNSAFE_PATTERNS = [
    (r"\beval\s*\(", "Use of eval()", "high"),
    (r"\bexec\s*\(", "Use of exec()", "high"),
    (r"pickle\.loads?\s*\(", "Unsafe pickle usage", "medium"),
    (r"subprocess.*shell\s*=\s*True", "subprocess with shell=True", "medium"),
    (r"__import__\s*\(", "Dynamic import", "low"),
]


def _read_file(filepath: str) -> str | None:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except (OSError, IOError):
        return None


def _get_repo_and_files(repo_id: int) -> tuple[Repository | None, list[RepositoryFile]]:
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            return None, []
        files = db.query(RepositoryFile).filter(RepositoryFile.repo_id == repo_id).all()
        return repo, files
    finally:
        db.close()


async def get_repo_summary(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    language_dist: dict[str, int] = defaultdict(int)
    total_loc = 0
    frameworks_detected: set[str] = set()

    for f in files:
        ext = f.extension or ""
        lang = EXTENSION_LANGUAGE_MAP.get(ext, "Other")
        language_dist[lang] += 1

        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if content:
            lines = content.count("\n") + 1
            total_loc += lines
            for framework, indicators in FRAMEWORK_INDICATORS.items():
                if any(ind in content for ind in indicators):
                    frameworks_detected.add(framework)

    architecture = "unknown"
    if "FastAPI" in frameworks_detected or "Flask" in frameworks_detected:
        architecture = "Python Web API"
    elif "Django" in frameworks_detected:
        architecture = "Django MVC"
    elif "React" in frameworks_detected or "Vue" in frameworks_detected:
        architecture = "Frontend SPA"
    elif "Next.js" in frameworks_detected:
        architecture = "Full-stack (Next.js)"
    elif "Express" in frameworks_detected:
        architecture = "Node.js Backend"

    return {
        "repo_id": repo_id,
        "name": repo.name,
        "description": repo.description,
        "language_breakdown": dict(language_dist),
        "total_files": len(files),
        "total_loc": total_loc,
        "architecture_pattern": architecture,
        "frameworks_detected": sorted(frameworks_detected),
        "status": "complete",
    }


def _calculate_complexity(source: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"functions": 0, "classes": 0, "branches": 0, "max_depth": 0, "score": 0}

    functions = 0
    classes = 0
    branches = 0
    max_depth = 0

    def _walk(node: ast.AST, depth: int = 0):
        nonlocal functions, classes, branches, max_depth
        max_depth = max(max_depth, depth)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
            branches += 1

        for child in ast.iter_child_nodes(node):
            child_depth = depth + 1 if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)) else depth
            _walk(child, child_depth)

    _walk(tree)
    loc = len(source.splitlines())
    score = round(branches * 2 + max_depth * 3 + loc / 100, 2)

    return {
        "functions": functions,
        "classes": classes,
        "branches": branches,
        "max_depth": max_depth,
        "loc": loc,
        "score": score,
    }


async def get_complexity_analysis(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    file_complexities = []
    for f in files:
        if f.extension != ".py":
            continue
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        metrics = _calculate_complexity(content)
        if metrics["score"] == 0 and metrics["functions"] == 0:
            continue

        risk = "low" if metrics["score"] < 15 else "medium" if metrics["score"] < 40 else "high"
        file_complexities.append({
            "path": f.path,
            "risk_level": risk,
            **metrics,
        })

    file_complexities.sort(key=lambda x: x["score"], reverse=True)
    avg = round(sum(fc["score"] for fc in file_complexities) / max(len(file_complexities), 1), 2)

    distribution = {"low": 0, "medium": 0, "high": 0}
    for fc in file_complexities:
        distribution[fc["risk_level"]] += 1

    return {
        "repo_id": repo_id,
        "average_complexity": avg,
        "most_complex_files": file_complexities[:10],
        "complexity_distribution": distribution,
        "total_analyzed": len(file_complexities),
        "status": "complete",
    }


async def get_dependency_analysis(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    dep_files = {
        "requirements.txt": "pip",
        "setup.py": "pip",
        "pyproject.toml": "pip",
        "package.json": "npm",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "bundler",
        "pom.xml": "maven",
        "build.gradle": "gradle",
    }

    dependencies: list[dict[str, Any]] = []

    for f in files:
        if f.filename not in dep_files:
            continue
        manager = dep_files[f.filename]
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        deps = _parse_dependencies(content, f.filename, manager)
        dependencies.append({
            "file": f.path,
            "package_manager": manager,
            "dependencies": deps,
            "count": len(deps),
        })

    total = sum(d["count"] for d in dependencies)
    return {
        "repo_id": repo_id,
        "dependency_files": dependencies,
        "total_dependencies": total,
        "status": "complete",
    }


def _parse_dependencies(content: str, filename: str, manager: str) -> list[dict[str, str]]:
    deps: list[dict[str, str]] = []

    if filename == "requirements.txt":
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([><=!~]+.+)?", line)
            if match:
                deps.append({"name": match.group(1), "version": (match.group(2) or "").strip()})

    elif filename == "package.json":
        try:
            data = json.loads(content)
            for section in ("dependencies", "devDependencies"):
                for name, version in data.get(section, {}).items():
                    deps.append({"name": name, "version": version, "type": section})
        except json.JSONDecodeError:
            pass

    elif filename == "go.mod":
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("require") or line in (")", "("):
                continue
            match = re.match(r"^([^\s]+)\s+(v[^\s]+)", line)
            if match:
                deps.append({"name": match.group(1), "version": match.group(2)})

    elif filename == "Cargo.toml":
        in_deps = False
        for line in content.splitlines():
            if re.match(r"^\[.*dependencies.*\]", line):
                in_deps = True
                continue
            elif line.startswith("["):
                in_deps = False
                continue
            if in_deps:
                match = re.match(r'^([a-zA-Z0-9_\-]+)\s*=\s*"([^"]+)"', line)
                if match:
                    deps.append({"name": match.group(1), "version": match.group(2)})

    return deps


async def get_dependency_graph(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    nodes: list[dict[str, str]] = []
    edges: list[dict[str, str]] = []
    file_paths = {f.path for f in files if f.extension == ".py"}
    module_map: dict[str, str] = {}

    for path in file_paths:
        module = path.replace("/", ".").replace("\\", ".").removesuffix(".py")
        module_map[module] = path
        directory = os.path.dirname(path) or "root"
        nodes.append({"id": path, "label": os.path.basename(path), "group": directory})

    for f in files:
        if f.extension != ".py":
            continue
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            imported_module = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_module = alias.name
            elif isinstance(node, ast.ImportFrom):
                imported_module = node.module or ""

            if imported_module:
                for mod_path, file_path in module_map.items():
                    if imported_module == mod_path or mod_path.endswith(f".{imported_module}"):
                        if file_path != f.path:
                            edges.append({"source": f.path, "target": file_path, "type": "import"})
                        break

    return {
        "repo_id": repo_id,
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "status": "complete",
    }


async def get_complexity_heatmap(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    heatmap_data: list[dict[str, Any]] = []

    for f in files:
        if f.extension != ".py":
            continue
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        metrics = _calculate_complexity(content)
        risk = "low" if metrics["score"] < 15 else "medium" if metrics["score"] < 40 else "high"
        heatmap_data.append({
            "path": f.path,
            "score": metrics["score"],
            "risk_level": risk,
            "size": f.size,
            "loc": metrics["loc"],
        })

    heatmap_data.sort(key=lambda x: x["score"], reverse=True)
    scores = [h["score"] for h in heatmap_data]

    return {
        "repo_id": repo_id,
        "heatmap_data": heatmap_data,
        "max_complexity": max(scores, default=0),
        "min_complexity": min(scores, default=0),
        "total_files_analyzed": len(heatmap_data),
        "status": "complete",
    }


async def detect_security_issues(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    findings: list[dict[str, Any]] = []
    skip_extensions = {".md", ".txt", ".json", ".yaml", ".yml", ".lock", ".svg", ".png", ".jpg"}

    for f in files:
        if f.extension in skip_extensions:
            continue
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        for line_num, line in enumerate(content.splitlines(), 1):
            for pattern, issue_type, severity in SECRET_PATTERNS + UNSAFE_PATTERNS:
                if re.search(pattern, line):
                    findings.append({
                        "file": f.path,
                        "line": line_num,
                        "type": issue_type,
                        "severity": severity,
                        "snippet": line.strip()[:120],
                    })

    severity_counts = defaultdict(int)
    for finding in findings:
        severity_counts[finding["severity"]] += 1

    return {
        "repo_id": repo_id,
        "findings": findings[:100],
        "total_issues": len(findings),
        "severity_breakdown": dict(severity_counts),
        "status": "complete",
    }


async def find_dead_code(repo_id: int) -> dict[str, Any]:
    repo, files = _get_repo_and_files(repo_id)
    if not repo:
        return {"error": "Repository not found", "repo_id": repo_id}

    defined_functions: list[dict[str, Any]] = []
    all_references: set[str] = set()

    for f in files:
        if f.extension != ".py":
            continue
        filepath = os.path.join(settings.REPOS_DIR, repo.name, f.path)
        content = _read_file(filepath)
        if not content:
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    defined_functions.append({
                        "name": node.name,
                        "file": f.path,
                        "line": node.lineno,
                    })
            elif isinstance(node, ast.Name):
                all_references.add(node.id)
            elif isinstance(node, ast.Attribute):
                all_references.add(node.attr)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    all_references.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    all_references.add(node.func.attr)

    skip_names = {
        "main", "setup", "teardown", "setUp", "tearDown",
        "test_", "conftest", "__init__",
    }
    potentially_unused = [
        func for func in defined_functions
        if func["name"] not in all_references
        and not any(func["name"].startswith(s) for s in skip_names)
    ]

    return {
        "repo_id": repo_id,
        "potentially_unused": potentially_unused,
        "total_functions_analyzed": len(defined_functions),
        "total_potentially_unused": len(potentially_unused),
        "status": "complete",
    }
