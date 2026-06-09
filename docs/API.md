# GitHub Intelligence Platform — API Reference

Base URL: `http://localhost:8000/api/v1`

All endpoints return JSON. Authenticated endpoints require a `Bearer` token in the `Authorization` header.

---

## Table of Contents

- [Repository](#repository)
- [Chat](#chat)
- [Analysis](#analysis)
- [Visualization](#visualization)
- [Authentication](#authentication)

---

## Repository

### Upload / Clone a Repository

**`POST /repo/upload`**

Clone a GitHub repository and begin ingestion (parsing, embedding, analysis).

**Request Body**

```json
{
  "url": "https://github.com/owner/repo",
  "branch": "main"
}
```

| Field    | Type   | Required | Description                          |
|----------|--------|----------|--------------------------------------|
| `url`    | string | Yes      | GitHub repository URL                |
| `branch` | string | No       | Branch to clone (default: `main`)    |

**Response** `201 Created`

```json
{
  "id": "uuid",
  "name": "owner/repo",
  "status": "cloning",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

### Get Repository Status

**`GET /repo/{id}/status`**

Check the current ingestion status of a repository.

**Path Parameters**

| Parameter | Type | Description          |
|-----------|------|----------------------|
| `id`      | UUID | Repository identifier |

**Response** `200 OK`

```json
{
  "id": "uuid",
  "status": "ready",
  "progress": 100,
  "steps": {
    "cloning": "completed",
    "parsing": "completed",
    "embedding": "completed",
    "analysis": "completed"
  }
}
```

**Status Values:** `cloning` | `parsing` | `embedding` | `analyzing` | `ready` | `failed`

---

### List Repository Files

**`GET /repo/{id}/files`**

Return the file tree for an ingested repository.

**Path Parameters**

| Parameter | Type | Description          |
|-----------|------|----------------------|
| `id`      | UUID | Repository identifier |

**Query Parameters**

| Parameter | Type   | Required | Description                     |
|-----------|--------|----------|---------------------------------|
| `path`    | string | No       | Subdirectory path to list       |

**Response** `200 OK`

```json
{
  "repo_id": "uuid",
  "path": "/",
  "files": [
    {
      "name": "src/main.py",
      "type": "file",
      "language": "python",
      "size": 2048
    },
    {
      "name": "src/utils/",
      "type": "directory",
      "children_count": 5
    }
  ]
}
```

---

### List All Repositories

**`GET /repo/`**

Return all repositories belonging to the authenticated user.

**Query Parameters**

| Parameter | Type   | Required | Description                         |
|-----------|--------|----------|-------------------------------------|
| `skip`    | int    | No       | Pagination offset (default: `0`)    |
| `limit`   | int    | No       | Page size (default: `20`, max: `100`) |

**Response** `200 OK`

```json
{
  "total": 5,
  "repositories": [
    {
      "id": "uuid",
      "name": "owner/repo",
      "status": "ready",
      "created_at": "2026-01-01T00:00:00Z",
      "file_count": 142,
      "languages": ["python", "javascript"]
    }
  ]
}
```

---

### Delete a Repository

**`DELETE /repo/{id}`**

Remove a repository and all associated data (files, embeddings, analysis results).

**Path Parameters**

| Parameter | Type | Description          |
|-----------|------|----------------------|
| `id`      | UUID | Repository identifier |

**Response** `204 No Content`

---

## Chat

### Ask a Question

**`POST /chat/{repo_id}/ask`**

Ask a natural-language question about a repository. The system retrieves relevant code context via semantic search and generates an answer.

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Request Body**

```json
{
  "question": "How does the authentication middleware work?",
  "max_context_chunks": 5
}
```

| Field                | Type   | Required | Description                                  |
|----------------------|--------|----------|----------------------------------------------|
| `question`           | string | Yes      | Natural-language question                    |
| `max_context_chunks` | int    | No       | Number of code chunks for context (default: `5`) |

**Response** `200 OK`

```json
{
  "answer": "The authentication middleware uses JWT tokens to...",
  "sources": [
    {
      "file": "src/middleware/auth.py",
      "start_line": 12,
      "end_line": 45,
      "relevance_score": 0.92
    }
  ]
}
```

---

## Analysis

### Repository Summary

**`GET /analysis/{repo_id}/summary`**

Get a high-level summary of the repository including language breakdown, structure, and key metrics.

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Response** `200 OK`

```json
{
  "repo_id": "uuid",
  "total_files": 142,
  "total_lines": 28500,
  "languages": {
    "python": { "files": 85, "lines": 18200 },
    "javascript": { "files": 42, "lines": 8300 },
    "other": { "files": 15, "lines": 2000 }
  },
  "top_modules": ["src/api", "src/services", "src/models"],
  "summary": "A web application with a Python backend and JavaScript frontend..."
}
```

---

### Complexity Metrics

**`GET /analysis/{repo_id}/complexity`**

Return cyclomatic and cognitive complexity scores for each file and function.

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Query Parameters**

| Parameter  | Type   | Required | Description                                |
|------------|--------|----------|--------------------------------------------|
| `sort_by`  | string | No       | Sort field: `cyclomatic` or `cognitive` (default: `cyclomatic`) |
| `limit`    | int    | No       | Max results (default: `50`)                |

**Response** `200 OK`

```json
{
  "repo_id": "uuid",
  "average_complexity": 4.2,
  "files": [
    {
      "path": "src/services/parser.py",
      "cyclomatic": 12,
      "cognitive": 8,
      "functions": [
        {
          "name": "parse_ast",
          "line": 45,
          "cyclomatic": 8,
          "cognitive": 6
        }
      ]
    }
  ]
}
```

---

### Dependency Analysis

**`GET /analysis/{repo_id}/dependencies`**

Return the internal and external dependency graph for the repository.

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Response** `200 OK`

```json
{
  "repo_id": "uuid",
  "internal": [
    { "source": "src/api/routes.py", "target": "src/services/repo_service.py" }
  ],
  "external": [
    { "package": "fastapi", "version": "0.115.0", "used_by": ["src/api/routes.py"] }
  ]
}
```

---

## Visualization

### Dependency Graph

**`GET /viz/{repo_id}/dependency-graph`**

Return graph data formatted for frontend rendering (nodes and edges).

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Query Parameters**

| Parameter | Type   | Required | Description                            |
|-----------|--------|----------|----------------------------------------|
| `format`  | string | No       | Output format: `d3` or `cytoscape` (default: `d3`) |

**Response** `200 OK`

```json
{
  "nodes": [
    { "id": "src/api/routes.py", "group": "api", "size": 1200 }
  ],
  "edges": [
    { "source": "src/api/routes.py", "target": "src/services/repo_service.py", "weight": 3 }
  ]
}
```

---

### Complexity Heatmap

**`GET /viz/{repo_id}/complexity-heatmap`**

Return heatmap data for visualizing code complexity across the repository.

**Path Parameters**

| Parameter  | Type | Description          |
|------------|------|----------------------|
| `repo_id`  | UUID | Repository identifier |

**Response** `200 OK`

```json
{
  "cells": [
    {
      "path": "src/services/parser.py",
      "complexity": 12,
      "lines": 340,
      "color": "#e74c3c"
    },
    {
      "path": "src/utils/helpers.py",
      "complexity": 2,
      "lines": 85,
      "color": "#2ecc71"
    }
  ]
}
```

---

## Authentication

### Register

**`POST /auth/register`**

Create a new user account.

**Request Body**

```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securepassword123"
}
```

| Field      | Type   | Required | Description              |
|------------|--------|----------|--------------------------|
| `email`    | string | Yes      | Valid email address       |
| `username` | string | Yes      | Unique username           |
| `password` | string | Yes      | Minimum 8 characters      |

**Response** `201 Created`

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

### Login

**`POST /auth/login`**

Authenticate and receive a JWT access token.

**Request Body**

```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

| Field      | Type   | Required | Description       |
|------------|--------|----------|-------------------|
| `email`    | string | Yes      | Registered email  |
| `password` | string | Yes      | Account password  |

**Response** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Error Responses

All endpoints may return the following error formats:

**`400 Bad Request`**

```json
{
  "detail": "Invalid repository URL format"
}
```

**`401 Unauthorized`**

```json
{
  "detail": "Invalid or expired token"
}
```

**`404 Not Found`**

```json
{
  "detail": "Repository not found"
}
```

**`500 Internal Server Error`**

```json
{
  "detail": "An unexpected error occurred"
}
```

---

## Rate Limiting

API requests are rate-limited to **100 requests per minute** per authenticated user. Rate limit headers are included in every response:

| Header                  | Description                    |
|-------------------------|--------------------------------|
| `X-RateLimit-Limit`     | Max requests per window        |
| `X-RateLimit-Remaining` | Remaining requests in window   |
| `X-RateLimit-Reset`     | Seconds until window resets    |
