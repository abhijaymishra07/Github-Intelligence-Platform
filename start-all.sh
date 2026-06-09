#!/usr/bin/env bash
# Start backend + Cloudflare tunnel + Streamlit (free local deploy)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BIN="$ROOT/bin/cloudflared"
PORT=8000

if [[ ! -x "$BIN" ]]; then
  echo "Downloading cloudflared..."
  mkdir -p "$ROOT/bin"
  python3 -c "
import urllib.request, os, stat
urllib.request.urlretrieve(
  'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64',
  '$BIN'
)
os.chmod('$BIN', os.stat('$BIN').st_mode | stat.S_IEXEC)
"
fi

echo "Starting backend on :$PORT ..."
cd "$ROOT/backend"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port "$PORT" &
BACKEND_PID=$!

sleep 2

echo "Starting Cloudflare tunnel..."
"$BIN" tunnel --url "http://127.0.0.1:$PORT" 2>&1 | tee /tmp/cloudflared.log &
TUNNEL_PID=$!

echo "Waiting for tunnel URL..."
for i in $(seq 1 30); do
  URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log | head -1 || true)
  if [[ -n "$URL" ]]; then
    mkdir -p "$ROOT/.streamlit"
    echo "API_BASE_URL = \"${URL}/api/v1\"" > "$ROOT/.streamlit/secrets.toml"
    echo ""
    echo "============================================"
    echo "  Backend tunnel: $URL"
    echo "  API URL:        ${URL}/api/v1"
    echo "  Streamlit:      http://localhost:8501"
    echo ""
    echo "  Streamlit Cloud secrets (paste this):"
    echo "  API_BASE_URL = \"${URL}/api/v1\""
    echo "============================================"
    break
  fi
  sleep 1
done

cd "$ROOT"
streamlit run streamlit_app.py --server.port 8501

kill $BACKEND_PID $TUNNEL_PID 2>/dev/null || true
