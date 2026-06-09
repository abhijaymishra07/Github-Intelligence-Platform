from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import analysis, auth, chat, repository, visualization


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="GitHub Intelligence Platform API",
    description="AI-powered platform for ingesting GitHub repos, parsing code, creating embeddings, and enabling natural language querying.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository.router, prefix="/api/v1/repo", tags=["Repositories"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(visualization.router, prefix="/api/v1/viz", tags=["Visualization"])


@app.get("/", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "GitHub Intelligence Platform API",
        "version": "0.1.0",
    }
