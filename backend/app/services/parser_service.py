import ast
import os
import re
from pathlib import Path
from typing import Any

from app.config import settings

MAX_FILE_SIZE = 1_000_000  # 1MB

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tox", ".eggs", "dist", "build", ".mypy_cache", ".pytest_cache",
    ".next", ".nuxt", "coverage", ".cache", "target", "vendor",
}

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala",
}

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".cpp": "cpp", ".c": "c",
    ".h": "c", ".hpp": "cpp", ".cs": "csharp", ".rb": "ruby",
    ".php": "php", ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
}

API_DECORATOR_PATTERNS = re.compile(
    r"@(?:app|router|api|blueprint|bp)\."
    r"(?:route|get|post|put|patch|delete|head|options)\s*\("
)

JS_FUNCTION_PATTERN = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)"
    r"|(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\("
    r"|(\w+)\s*\(.*?\)\s*\{"
)

JS_CLASS_PATTERN = re.compile(
    r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?"
)

JS_IMPORT_PATTERN = re.compile(
    r"import\s+.*?\s+from\s+['\"](.+?)['\"]"
    r"|require\s*\(\s*['\"](.+?)['\"]\s*\)"
)

JS_EXPORT_PATTERN = re.compile(
    r"export\s+(?:default\s+)?(?:class|function|const|let|var|async\s+function)\s+(\w+)"
    r"|export\s*\{([^}]+)\}"
)

GENERIC_FUNCTION_PATTERN = re.compile(
    r"(?:def|func|fn|function|fun|sub|proc|method)\s+(\w+)"
)

GENERIC_IMPORT_PATTERN = re.compile(
    r"(?:import|use|require|include|using|from)\s+(.+?)(?:\s*;|\s*$)", re.MULTILINE
)


def _detect_language(file_path: str, language: str | None) -> str:
    if language:
        return language.lower()
    ext = Path(file_path).suffix.lower()
    return EXTENSION_LANGUAGE_MAP.get(ext, "unknown")


def _read_file_safe(file_path: str) -> str | None:
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        if path.stat().st_size > MAX_FILE_SIZE:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _count_loc(source: str) -> int:
    count = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            count += 1
    return count


def _parse_python(source: str, file_path: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return _parse_generic(source)

    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    imports: list[str] = []
    endpoints: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            func_info = _extract_function_info(node)
            functions.append(func_info)
            endpoint = _detect_endpoint(node)
            if endpoint:
                endpoints.append(endpoint)

        elif isinstance(node, ast.ClassDef):
            class_info = _extract_class_info(node)
            classes.append(class_info)
            for item in ast.iter_child_nodes(node):
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    endpoint = _detect_endpoint(item)
                    if endpoint:
                        endpoints.append(endpoint)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "exports": [],
        "endpoints": endpoints,
        "loc": _count_loc(source),
    }


def _extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
    args = []
    for arg in node.args.args:
        args.append(arg.arg)

    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(ast.unparse(dec))
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Attribute):
                decorators.append(ast.unparse(dec.func))
            elif isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)

    docstring = ast.get_docstring(node)

    return {
        "name": node.name,
        "args": args,
        "decorators": decorators,
        "lineno": node.lineno,
        "docstring": docstring,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }


def _extract_class_info(node: ast.ClassDef) -> dict[str, Any]:
    methods: list[dict[str, Any]] = []
    for item in ast.iter_child_nodes(node):
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            methods.append(_extract_function_info(item))

    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(ast.unparse(base))

    docstring = ast.get_docstring(node)

    return {
        "name": node.name,
        "methods": methods,
        "bases": bases,
        "lineno": node.lineno,
        "docstring": docstring,
    }


def _detect_endpoint(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any] | None:
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            dec_str = ast.unparse(dec)
            if API_DECORATOR_PATTERNS.match(f"@{ast.unparse(dec.func)}("):
                method = dec.func.attr.upper()
                if method == "ROUTE":
                    method = "GET"
                path = ""
                if dec.args:
                    try:
                        path = ast.literal_eval(dec.args[0])
                    except (ValueError, TypeError):
                        path = ast.unparse(dec.args[0])
                return {
                    "function": node.name,
                    "method": method,
                    "path": path,
                    "lineno": node.lineno,
                }
    return None


def _parse_javascript(source: str) -> dict[str, Any]:
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    imports: list[str] = []
    exports: list[str] = []

    for match in JS_IMPORT_PATTERN.finditer(source):
        module = match.group(1) or match.group(2)
        if module:
            imports.append(module)

    for match in JS_EXPORT_PATTERN.finditer(source):
        if match.group(1):
            exports.append(match.group(1))
        elif match.group(2):
            for name in match.group(2).split(","):
                name = name.strip().split(" as ")[0].strip()
                if name:
                    exports.append(name)

    lines = source.splitlines()
    seen_functions: set[str] = set()
    for i, line in enumerate(lines, 1):
        match = JS_FUNCTION_PATTERN.search(line)
        if match:
            name = match.group(1) or match.group(2) or match.group(3)
            if name and name not in seen_functions and not name[0].isupper():
                seen_functions.add(name)
                functions.append({"name": name, "lineno": i})

    for match in JS_CLASS_PATTERN.finditer(source):
        class_info: dict[str, Any] = {"name": match.group(1)}
        if match.group(2):
            class_info["bases"] = [match.group(2)]
        else:
            class_info["bases"] = []
        classes.append(class_info)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "exports": exports,
        "endpoints": [],
        "loc": _count_loc(source),
    }


def _parse_generic(source: str) -> dict[str, Any]:
    functions: list[dict[str, Any]] = []
    imports: list[str] = []

    for match in GENERIC_FUNCTION_PATTERN.finditer(source):
        functions.append({"name": match.group(1)})

    for match in GENERIC_IMPORT_PATTERN.finditer(source):
        imports.append(match.group(1).strip())

    return {
        "functions": functions,
        "classes": [],
        "imports": imports,
        "exports": [],
        "endpoints": [],
        "loc": _count_loc(source),
    }


async def parse_file(file_path: str, language: str | None = None) -> dict[str, Any]:
    lang = _detect_language(file_path, language)
    source = _read_file_safe(file_path)

    if source is None:
        return {
            "file_path": file_path,
            "language": lang,
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "endpoints": [],
            "loc": 0,
            "parsed": False,
            "error": "Unable to read file (missing, too large, or encoding error)",
        }

    if lang == "python":
        result = _parse_python(source, file_path)
    elif lang in ("javascript", "typescript"):
        result = _parse_javascript(source)
    else:
        result = _parse_generic(source)

    return {
        "file_path": file_path,
        "language": lang,
        "parsed": True,
        **result,
    }


async def parse_repository(repo_path: str) -> dict[str, Any]:
    base = Path(repo_path)
    if not base.exists() or not base.is_dir():
        return {
            "repo_path": repo_path,
            "total_files_parsed": 0,
            "files": [],
            "statistics": {},
            "error": "Repository path does not exist or is not a directory",
        }

    files_results: list[dict[str, Any]] = []
    language_stats: dict[str, int] = {}
    total_loc = 0
    total_functions = 0
    total_classes = 0
    errors = 0

    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in filenames:
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            result = await parse_file(str(filepath))
            files_results.append(result)

            if result.get("parsed"):
                lang = result.get("language", "unknown")
                language_stats[lang] = language_stats.get(lang, 0) + 1
                total_loc += result.get("loc", 0)
                total_functions += len(result.get("functions", []))
                total_classes += len(result.get("classes", []))
            else:
                errors += 1

    return {
        "repo_path": repo_path,
        "total_files_parsed": len(files_results) - errors,
        "total_files_skipped": errors,
        "files": files_results,
        "statistics": {
            "total_loc": total_loc,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "languages": language_stats,
        },
    }
