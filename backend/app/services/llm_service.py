import httpx
from typing import Any

from app.config import settings

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


async def query_llm(prompt: str, model: str | None = None) -> dict[str, Any]:
    model = model or settings.LLM_MODEL
    api_key = settings.GROQ_API_KEY

    if not api_key:
        return {
            "response": "GROQ_API_KEY is not set. Get a free key at https://console.groq.com",
            "model": model,
            "tokens_used": 0,
            "status": "error",
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert code analyst. You analyze codebases and answer "
                    "questions about code architecture, functionality, dependencies, and patterns. "
                    "Be concise, accurate, and helpful. Use markdown formatting."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GROQ_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return {
                "response": choice,
                "model": model,
                "tokens_used": usage.get("total_tokens", 0),
                "status": "success",
            }
    except httpx.HTTPStatusError as e:
        body = e.response.text[:300]
        return {
            "response": f"Groq API error ({e.response.status_code}): {body}",
            "model": model,
            "tokens_used": 0,
            "status": "error",
        }
    except Exception as e:
        return {
            "response": f"LLM query failed: {str(e)}",
            "model": model,
            "tokens_used": 0,
            "status": "error",
        }


async def ask_about_repo(
    repo_id: int, question: str, context: list[dict] | None = None
) -> dict[str, Any]:
    from app.services.rag_service import build_prompt, retrieve_context

    if context is None:
        context = await retrieve_context(repo_id, question)

    prompt = await build_prompt(question, context)
    result = await query_llm(prompt)

    return {
        "question": question,
        "answer": result["response"],
        "sources": [c["file_path"] for c in context],
        "model": result["model"],
    }


async def generate_readme(repo_id: int, repo_info: dict) -> str:
    file_tree = repo_info.get("file_tree", "")
    languages = repo_info.get("languages", {})
    description = repo_info.get("description", "")
    name = repo_info.get("name", "Project")

    prompt = (
        f"Generate a professional README.md for a project called '{name}'.\n\n"
        f"Description: {description}\n"
        f"Languages: {languages}\n"
        f"File structure:\n{file_tree}\n\n"
        "Include sections: Title, Description, Features, Installation, Usage, "
        "Project Structure, Contributing, and License. "
        "Use proper markdown formatting. Be concise but informative."
    )

    result = await query_llm(prompt)
    if result["status"] != "success":
        return f"# {name}\n\n{description or 'README generation failed.'}\n"
    return result["response"]


async def explain_code(code: str, language: str = "python") -> str:
    prompt = (
        f"Explain the following {language} code clearly and concisely. "
        f"Describe what it does, its key logic, and any notable patterns:\n\n"
        f"```{language}\n{code}\n```"
    )

    result = await query_llm(prompt)
    return result["response"]
