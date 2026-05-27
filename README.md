# GitHub Intelligence Platform

**AI-powered platform for understanding, analyzing, and querying GitHub repositories.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

---

## Features

- **Repository Ingestion** — Clone and index any public GitHub repository for analysis
- **Code Parsing** — Deep AST-level parsing with Tree-sitter for accurate code understanding
- **Semantic Search** — Find relevant code snippets using natural language queries
- **AI Chat** — Ask questions about a repository and get context-aware answers
- **Dependency Visualization** — Interactive graphs of module and package dependencies
- **Complexity Analysis** — Heatmaps and metrics for cyclomatic and cognitive complexity
- **Security Scanning** — Detect common vulnerability patterns and hardcoded secrets
- **Auto Documentation** — Generate summaries and documentation for functions and modules

---

## Tech Stack

| Layer          | Technology              | Purpose                          |
|----------------|-------------------------|----------------------------------|
| Backend API    | FastAPI                 | High-performance async REST API  |
| Frontend       | Next.js (React)         | Server-rendered interactive UI   |
| Vector Store   | ChromaDB                | Semantic search & embeddings     |
| Code Parsing   | Tree-sitter             | AST extraction & analysis        |
| Embeddings     | Sentence Transformers   | Code & text embedding generation |
| Database       | PostgreSQL              | Relational data persistence      |
| Containerization | Docker & Docker Compose | Reproducible deployments       |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend (:3000)                    │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  ┌────────────┐  │
│  │ Dashboard  │  │  Chat UI   │  │  Graphs   │  │  Explorer  │  │
│  └───────────┘  └────────────┘  └───────────┘  └────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (:8000)                       │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ Repo API │  │  Chat API │  │ Analysis  │  │  Auth / JWT  │  │
│  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  └──────────────┘  │
│       │              │              │                            │
│  ┌────▼──────────────▼──────────────▼────────────────────────┐  │
│  │                  Core Services Layer                       │  │
│  │  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐ │  │
│  │  │ Git Ops │  │ Embedding │  │ Parsing  │  │ Security  │ │  │
│  │  └─────────┘  └───────────┘  └──────────┘  └───────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────┬──────────────┬──────────────┬───────────────────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │PostgreSQL│   │ ChromaDB │   │  Repos   │
   │  (:5432) │   │ (Vector) │   │  (Disk)  │
   └─────────┘   └──────────┘   └──────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 22+
- PostgreSQL 16+
- Git

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/github-intelligence-platform.git
cd github-intelligence-platform

# Start all services
docker compose -f docker/docker-compose.yml up --build
```

The frontend will be available at `http://localhost:3000` and the API at `http://localhost:8000`.

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Run the development server
npm run dev
```

---

## API Endpoints

| Method   | Endpoint                              | Description                        |
|----------|---------------------------------------|------------------------------------|
| `POST`   | `/api/v1/repo/upload`                 | Upload / clone a repository        |
| `GET`    | `/api/v1/repo/{id}/status`            | Check ingestion status             |
| `GET`    | `/api/v1/repo/{id}/files`             | List repository files              |
| `GET`    | `/api/v1/repo/`                       | List all repositories              |
| `DELETE` | `/api/v1/repo/{id}`                   | Delete a repository                |
| `POST`   | `/api/v1/chat/{repo_id}/ask`          | Ask a question about a repository  |
| `GET`    | `/api/v1/analysis/{repo_id}/summary`  | Get repository summary             |
| `GET`    | `/api/v1/analysis/{repo_id}/complexity` | Get complexity metrics           |
| `GET`    | `/api/v1/analysis/{repo_id}/dependencies` | Get dependency analysis        |
| `GET`    | `/api/v1/viz/{repo_id}/dependency-graph` | Dependency graph visualization  |
| `GET`    | `/api/v1/viz/{repo_id}/complexity-heatmap` | Complexity heatmap data       |
| `POST`   | `/api/v1/auth/register`               | Register a new user                |
| `POST`   | `/api/v1/auth/login`                  | Authenticate and get JWT token     |

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI) when the backend is running, or see [`docs/API.md`](docs/API.md).

---

## Project Structure

```
SMART GITHUB AI/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── main.py           # Application entry point
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Configuration & security
│   │   ├── models/           # SQLAlchemy / Pydantic models
│   │   ├── services/         # Business logic
│   │   │   ├── git_service.py
│   │   │   ├── parser_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── chat_service.py
│   │   │   └── analysis_service.py
│   │   └── utils/            # Shared utilities
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/              # App router pages
│   │   ├── components/       # React components
│   │   └── lib/              # Utilities & API client
│   ├── package.json
│   └── .env.example
├── docker/                   # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docs/                     # Documentation
│   └── API.md
├── .gitignore
├── LICENSE
└── README.md
```

---

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

Please make sure to:
- Write tests for new features
- Follow the existing code style
- Update documentation as needed

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with purpose by contributors who believe in open-source intelligence.</p>
