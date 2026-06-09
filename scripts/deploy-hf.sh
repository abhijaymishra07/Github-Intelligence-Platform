#!/usr/bin/env bash
# Deploy backend to Hugging Face Spaces (FREE, no credit card)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/.hf-space-build"
SPACE_NAME="${HF_SPACE_NAME:-github-intel-api}"

echo "=== Hugging Face Spaces deploy (free) ==="

if [[ -z "${HF_TOKEN:-}" ]]; then
  TOKEN_FILE="$HOME/.cache/huggingface/token"
  if [[ -f "$TOKEN_FILE" ]]; then
    HF_TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
  fi
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo ""
  echo "HF token required. Run:"
  echo "  export HF_TOKEN=hf_your_token_here"
  echo "  ./scripts/deploy-hf.sh"
  echo ""
  echo "Create token: https://huggingface.co/settings/tokens"
  echo "  → Token type: Fine-grained  OR  Classic"
  echo "  → Permissions: Write (must allow creating/uploading repos)"
  exit 1
fi

export HF_TOKEN ROOT BUILD SPACE_NAME
python3 <<'PY'
import os
import shutil
import sys
from pathlib import Path

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

root = Path(os.environ["ROOT"])
build = Path(os.environ["BUILD"])
space_name = os.environ["SPACE_NAME"]
token = os.environ["HF_TOKEN"]

api = HfApi(token=token)
who = api.whoami()
user = who["name"]
repo_id = f"{user}/{space_name}"

print(f"Logged in as: {user}")
print(f"Space: {repo_id}")

if build.exists():
    shutil.rmtree(build)
build.mkdir(parents=True)
(build / "app").mkdir()

shutil.copytree(root / "backend" / "app", build / "app", dirs_exist_ok=True)
shutil.copy(root / "backend" / "requirements-render.txt", build / "requirements.txt")
shutil.copy(root / "hf-space" / "Dockerfile", build / "Dockerfile")
shutil.copy(root / "hf-space" / "README.md", build / "README.md")

space_exists = False
try:
    api.repo_info(repo_id=repo_id, repo_type="space")
    space_exists = True
    print("Space already exists — uploading files...")
except Exception:
    print("Space not found — creating...")

if not space_exists:
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            exist_ok=True,
        )
        print("Space created.")
    except HfHubHTTPError as e:
        if "403" in str(e):
            print()
            print("ERROR: 403 Forbidden — cannot create Space with this token.")
            print()
            print("Fix (pick ONE):")
            print()
            print("A) Create a new token with WRITE access:")
            print("   https://huggingface.co/settings/tokens")
            print("   Fine-grained → Repositories: Read + Write, Create repos: ON")
            print("   OR Classic token → Role: Write")
            print("   Then: export HF_TOKEN=hf_new_token && ./scripts/deploy-hf.sh")
            print()
            print("B) Create the Space manually in browser (2 min), then re-run this script:")
            print(f"   https://huggingface.co/new-space?sdk=docker&name={space_name}")
            print("   → SDK: Docker")
            print(f"   → Name: {space_name}")
            print("   → Visibility: Public")
            print("   → Create, then run ./scripts/deploy-hf.sh again")
            print()
            print("Also verify your HF email is confirmed (check inbox).")
            sys.exit(1)
        raise

api.upload_folder(
    folder_path=str(build),
    repo_id=repo_id,
    repo_type="space",
    commit_message="Deploy GitHub Intelligence API",
    create_pr=True,
)

api_url = f"https://{user}-{space_name}.hf.space/api/v1"
space_url = f"https://huggingface.co/spaces/{repo_id}"

secrets = f"""# Paste into Streamlit Cloud → Settings → Secrets → Reboot

API_BASE_URL = "{api_url}"
"""
(root / "STREAMLIT_CLOUD_SECRETS.toml").write_text(secrets)

print()
print("============================================")
print("  Uploaded! HF is building (5-15 min)...")
print(f"  Space:    {space_url}")
print(f"  API URL:  {api_url}")
print()
print(f"  1. Open {space_url}/settings")
print("  2. Repository secrets → GROQ_API_KEY = gsk_...")
print("  3. Streamlit Cloud secrets:")
print(f'     API_BASE_URL = "{api_url}"')
print("============================================")
print("Saved: STREAMLIT_CLOUD_SECRETS.toml")
PY
