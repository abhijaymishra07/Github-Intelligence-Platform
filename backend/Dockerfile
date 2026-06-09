FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-render.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CHROMA_PERSIST_DIR=/tmp/chroma_data \
    REPOS_DIR=/tmp/repos \
    DATABASE_URL=sqlite:////tmp/github_intel.db

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
