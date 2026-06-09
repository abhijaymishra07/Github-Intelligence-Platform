"""
GitHub Intelligence Platform — Streamlit UI

Calls the FastAPI backend. Set API_BASE_URL in .streamlit/secrets.toml or env.

Local dev:
  1. Start backend:  cd backend && uvicorn app.main:app --reload --port 8000
  2. Run Streamlit:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import time
from typing import Any

import requests
import streamlit as st

DEFAULT_API_URL = "http://localhost:8000/api/v1"
READY_STATUSES = {"ready"}
TERMINAL_STATUSES = {"ready", "error", "failed"}


def get_api_base_url() -> str:
    if override := st.session_state.get("api_base_url_override"):
        return override.rstrip("/")
    if env_url := os.getenv("API_BASE_URL"):
        return env_url.rstrip("/")
    try:
        if "API_BASE_URL" in st.secrets:
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except (FileNotFoundError, AttributeError, RuntimeError):
        pass
    return DEFAULT_API_URL


def api_request(
    method: str,
    path: str,
    *,
    json: dict | None = None,
    timeout: int = 120,
) -> tuple[Any | None, str | None]:
    base = get_api_base_url()
    url = f"{base}{path}"
    try:
        response = requests.request(method, url, json=json, timeout=timeout)
        if response.status_code == 204:
            return None, None
        if not response.ok:
            detail = response.json().get("detail", response.text) if response.text else response.reason
            return None, str(detail)
        if not response.text:
            return None, None
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot reach backend at {base}. Start the FastAPI server first."
    except requests.exceptions.Timeout:
        return None, "Request timed out. Large repos can take several minutes."
    except requests.exceptions.RequestException as exc:
        return None, str(exc)


def check_backend_health() -> tuple[bool, str]:
    base = get_api_base_url().removesuffix("/api/v1")
    try:
        response = requests.get(f"{base}/", timeout=5)
        if response.ok:
            return True, "Connected"
        return False, f"Backend returned {response.status_code}"
    except requests.exceptions.RequestException as exc:
        return False, str(exc)


def status_badge(status: str) -> str:
    colors = {
        "ready": "🟢",
        "cloning": "🔵",
        "parsing": "🔵",
        "embedding": "🔵",
        "analyzing": "🔵",
        "error": "🔴",
        "failed": "🔴",
    }
    return f"{colors.get(status, '⚪')} {status}"


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def render_sidebar() -> str:
    st.sidebar.title("GitHub Intelligence")
    st.sidebar.caption("AI-powered repository analysis & chat")

    api_url = st.sidebar.text_input("API base URL", value=get_api_base_url(), key="api_url_input")
    st.session_state["api_base_url_override"] = api_url.rstrip("/")

    healthy, health_msg = check_backend_health()
    if healthy:
        st.sidebar.success(f"Backend: {health_msg}")
    else:
        st.sidebar.error(f"Backend: {health_msg}")

    st.sidebar.divider()
    return st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Add Repository", "Repository Chat", "Analysis"],
        label_visibility="collapsed",
    )


def render_dashboard() -> None:
    st.header("Dashboard")
    repos, err = api_request("GET", "/repo/")
    if err:
        st.error(err)
        return
    if not repos:
        st.info("No repositories yet. Use **Add Repository** to ingest your first repo.")
        return

    ready = sum(1 for r in repos if r.get("status") == "ready")
    processing = len(repos) - ready

    c1, c2, c3 = st.columns(3)
    c1.metric("Total repositories", len(repos))
    c2.metric("Ready", ready)
    c3.metric("Processing", processing)

    st.subheader("Repositories")
    for repo in repos:
        with st.expander(f"{repo['name']} — {status_badge(repo['status'])}"):
            st.markdown(f"**URL:** [{repo['url']}]({repo['url']})")
            st.markdown(f"**Branch:** `{repo.get('branch', 'main')}`")
            st.markdown(f"**Files:** {repo.get('file_count', 0)} · **Size:** {format_bytes(repo.get('total_size', 0))}")
            if repo.get("language"):
                st.markdown(f"**Language:** {repo['language']}")
            if repo.get("description"):
                st.caption(repo["description"])

            col_refresh, col_delete = st.columns([1, 1])
            if col_refresh.button("Refresh status", key=f"refresh-{repo['id']}"):
                status, err = api_request("GET", f"/repo/{repo['id']}/status")
                if err:
                    st.error(err)
                else:
                    st.success(f"Status: {status['status']}")
                    st.rerun()

            if col_delete.button("Delete", key=f"delete-{repo['id']}", type="secondary"):
                _, err = api_request("DELETE", f"/repo/{repo['id']}")
                if err:
                    st.error(err)
                else:
                    st.success("Repository deleted.")
                    st.rerun()


def render_add_repo() -> None:
    st.header("Add Repository")
    st.caption("Paste a public GitHub URL. Ingestion runs in the background (clone → parse → embed).")

    with st.form("add_repo_form"):
        url = st.text_input(
            "Repository URL",
            placeholder="https://github.com/owner/repo",
        )
        branch = st.text_input("Branch", value="main")
        submitted = st.form_submit_button("Add Repository", type="primary")

    if submitted:
        if not url.strip():
            st.warning("Enter a repository URL.")
            return

        with st.spinner("Starting ingestion..."):
            repo, err = api_request(
                "POST",
                "/repo/upload",
                json={"url": url.strip(), "branch": branch.strip() or "main"},
                timeout=30,
            )

        if err:
            st.error(err)
            return

        st.success(f"Added **{repo['name']}** (ID {repo['id']}). Status: `{repo['status']}`")

        progress = st.progress(0, text="Waiting for ingestion...")
        status = repo["status"]
        for attempt in range(60):
            if status in TERMINAL_STATUSES:
                break
            time.sleep(2)
            updated, err = api_request("GET", f"/repo/{repo['id']}/status")
            if err:
                st.error(err)
                return
            status = updated["status"]
            step_map = {"cloning": 20, "parsing": 45, "embedding": 70, "analyzing": 85, "ready": 100}
            progress.progress(step_map.get(status, 10), text=f"Status: {status}")

        progress.progress(100, text=f"Status: {status}")
        if status == "ready":
            st.success("Repository is ready for chat and analysis.")
        elif status in {"error", "failed"}:
            st.error("Ingestion failed. Check backend logs for details.")
        else:
            st.info("Still processing. Check the Dashboard for updates.")


def get_repo_options() -> list[dict]:
    repos, err = api_request("GET", "/repo/")
    if err:
        st.error(err)
        return []
    return repos or []


def render_chat() -> None:
    st.header("Repository Chat")
    repos = get_repo_options()
    if not repos:
        st.info("Add a repository first.")
        return

    ready_repos = [r for r in repos if r.get("status") == "ready"]
    if not ready_repos:
        st.warning("No repositories are ready yet. Wait for ingestion to finish.")
        return

    labels = {f"{r['name']} (ID {r['id']})": r["id"] for r in ready_repos}
    selected = st.selectbox("Repository", list(labels.keys()))
    repo_id = labels[selected]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if repo_id not in st.session_state.chat_history:
        st.session_state.chat_history[repo_id] = []

    for message in st.session_state.chat_history[repo_id]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander("Sources"):
                    for source in message["sources"]:
                        st.code(source)

    question = st.chat_input("Ask about this repository...")
    if question:
        st.session_state.chat_history[repo_id].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result, err = api_request(
                    "POST",
                    f"/chat/{repo_id}/ask",
                    json={"question": question},
                    timeout=180,
                )
            if err:
                st.error(err)
                answer = f"Error: {err}"
                sources = []
            else:
                answer = result.get("answer", "No answer returned.")
                sources = result.get("sources", [])
                st.markdown(answer)
                if sources:
                    with st.expander("Sources"):
                        for source in sources:
                            st.code(source)

        st.session_state.chat_history[repo_id].append(
            {"role": "assistant", "content": answer, "sources": sources}
        )


def render_analysis() -> None:
    st.header("Analysis")
    repos = get_repo_options()
    if not repos:
        st.info("Add a repository first.")
        return

    labels = {f"{r['name']} ({r['status']})": r["id"] for r in repos}
    selected = st.selectbox("Repository", list(labels.keys()))
    repo_id = labels[selected]

    tab_summary, tab_complexity, tab_deps, tab_security, tab_files = st.tabs(
        ["Summary", "Complexity", "Dependencies", "Security", "Files"]
    )

    with tab_summary:
        if st.button("Load summary", key="load-summary"):
            with st.spinner("Analyzing..."):
                data, err = api_request("GET", f"/analysis/{repo_id}/summary", timeout=120)
            if err:
                st.error(err)
            elif data.get("error"):
                st.error(data["error"])
            else:
                st.json(data)

    with tab_complexity:
        if st.button("Load complexity", key="load-complexity"):
            with st.spinner("Computing complexity..."):
                data, err = api_request("GET", f"/analysis/{repo_id}/complexity", timeout=120)
            if err:
                st.error(err)
            elif data.get("error"):
                st.error(data["error"])
            else:
                st.json(data)

    with tab_deps:
        if st.button("Load dependencies", key="load-deps"):
            with st.spinner("Scanning dependencies..."):
                data, err = api_request("GET", f"/analysis/{repo_id}/dependencies", timeout=120)
            if err:
                st.error(err)
            elif data.get("error"):
                st.error(data["error"])
            else:
                st.json(data)

    with tab_security:
        if st.button("Scan security", key="load-security"):
            with st.spinner("Scanning for issues..."):
                data, err = api_request("GET", f"/analysis/{repo_id}/security", timeout=120)
            if err:
                st.error(err)
            elif data.get("error"):
                st.error(data["error"])
            else:
                st.json(data)

    with tab_files:
        if st.button("List files", key="load-files"):
            files, err = api_request("GET", f"/repo/{repo_id}/files", timeout=60)
            if err:
                st.error(err)
            elif not files:
                st.info("No files indexed yet.")
            else:
                st.dataframe(
                    [
                        {
                            "path": f["path"],
                            "language": f.get("language") or "—",
                            "size": format_bytes(f.get("size", 0)),
                        }
                        for f in files
                    ],
                    use_container_width=True,
                    hide_index=True,
                )


def main() -> None:
    st.set_page_config(
        page_title="GitHub Intelligence",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    page = render_sidebar()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Add Repository":
        render_add_repo()
    elif page == "Repository Chat":
        render_chat()
    elif page == "Analysis":
        render_analysis()


if __name__ == "__main__":
    main()
