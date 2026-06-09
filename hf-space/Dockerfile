FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=7860 \
    DATABASE_URL=sqlite:////data/github_intel.db \
    CHROMA_PERSIST_DIR=/data/chroma_data \
    REPOS_DIR=/data/repos

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 7860"]
