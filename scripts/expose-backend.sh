#!/usr/bin/env bash
# Expose your local FastAPI backend to the internet (FREE, no Render payment).
# Use the printed URL in Streamlit Cloud secrets as API_BASE_URL + /api/v1
#
# Prereqs: backend running on port 8000
#   cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000

set -euo pipefail

PORT="${PORT:-8000}"

if ! python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${PORT}/', timeout=3)" 2>/dev/null; then
  echo "ERROR: Backend not reachable at http://127.0.0.1:${PORT}/"
  echo "Start it first:"
  echo "  cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port ${PORT}"
  exit 1
fi

if command -v cloudflared >/dev/null 2>&1; then
  echo ""
  echo "Starting Cloudflare tunnel (free)..."
  echo "Copy the https://*.trycloudflare.com URL into Streamlit secrets:"
  echo '  API_BASE_URL = "https://YOUR-TUNNEL-URL.trycloudflare.com/api/v1"'
  echo ""
  exec cloudflared tunnel --url "http://127.0.0.1:${PORT}"
fi

if command -v ngrok >/dev/null 2>&1; then
  echo ""
  echo "Starting ngrok tunnel..."
  echo 'Set Streamlit secret: API_BASE_URL = "https://YOUR-NGROK-URL/api/v1"'
  echo ""
  exec ngrok http "${PORT}"
fi

echo "Install a free tunnel tool, then re-run this script:"
echo ""
echo "  # Option A — Cloudflare (recommended, no account)"
echo "  curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared"
echo "  chmod +x cloudflared && sudo mv cloudflared /usr/local/bin/"
echo ""
echo "  # Option B — ngrok"
echo "  sudo snap install ngrok"
echo ""
exit 1
