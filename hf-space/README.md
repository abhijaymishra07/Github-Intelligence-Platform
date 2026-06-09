---
title: GitHub Intelligence API
emoji: 🧠
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# GitHub Intelligence API

Free FastAPI backend for the [GitHub Intelligence Platform](https://github.com/abhijaymishra07/Github-Intelligence-Platform).

## Required secret

In **Settings → Repository secrets** add:

| Name | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (`gsk_...`) |

## Endpoints

- Health: `GET /`
- API base: `/api/v1`
- Docs: `/docs`

## Streamlit Cloud

```toml
API_BASE_URL = "https://abhijaymishra07-github-intel-api.hf.space/api/v1"
```

Replace username/space name if yours differ.
