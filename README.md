# GlitchAgent - AI-Powered Browser Automation

GlitchAgent is an AI-powered agent that automates browser workflows using natural language commands. It translates natural language instructions into browser actions using Cloudflare's LLM service and executes them using Playwright.

## Features

- **Natural Language Commands**: Control your browser with simple English instructions
- **Browser Automation**: Automatically navigate, click, fill forms, and more
- **Error Handling**: Robust error handling for browser automation
- **Screenshot Capture**: Capture screenshots of the browser state
- **Execution History**: Track and review past automation tasks

## Backend

### Requirements

- Python 3.12
- MongoDB and Redis (`MONGO_URI`, `REDIS_URI`)
- Cloudflare Workers AI credentials (optional at boot; command endpoints return 503 without them)

### Run locally

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # fill in MONGO_URI, REDIS_URI, CLOUDFLARE_*
python main.py         # http://localhost:8000, /health, /docs in development
```

Or `docker compose up` in `backend/` (Mongo + Redis + the API with reload).

Tests (offline, mocked Mongo/Redis/JWKS): `pip install -r tests/requirements-test.txt && pytest tests`

### Auth and per-user data

Every `/v1/glitch-agent/*` endpoint requires `Authorization: Bearer <Clerk session JWT>`, verified (RS256) against `{CLERK_JWT_ISSUER}/.well-known/jwks.json`. Runs and history are stored with the caller's Clerk `sub` and are only visible to that user (404 otherwise). `/stop-browser` is global but still needs auth. If `CLERK_JWT_ISSUER` is unset, auth is disabled and everyone is user `local` (a warning is logged at startup). `/health` is always public.

### Deploy (Render)

`backend/render.yaml` defines a Docker web service (the image installs Playwright Chromium; Render's native Python runtime cannot). It runs gunicorn with one uvicorn worker, because the browser and in-memory results are per-process.

1. Create a Blueprint from the repo and point it at `backend/render.yaml`.
2. Set the `sync: false` env vars in the dashboard (below). MongoDB must be external (e.g. Atlas); Redis can be Render Key Value.
3. Health check: `/health`.

### Environment variables

| Var | Required | Notes |
| --- | --- | --- |
| `MONGO_URI`, `REDIS_URI` | yes | app fails to start without them |
| `CLOUDFLARE_API_KEY`, `CLOUDFLARE_ACCOUNT_ID` | for commands | missing -> 503 on command endpoints |
| `CLERK_JWT_ISSUER` | for auth | unset disables auth |
| `CLERK_JWKS_TTL_SECONDS` | no | JWKS cache, default 3600 |
| `ALLOWED_ORIGINS` | no | comma-separated CORS origins, default `http://localhost:5173` |
| `ENVIRONMENT` | no | `development` enables `/docs` |
| `PORT`, `HEADLESS` | no | default 8000 / true |

## API Endpoints

- `POST /v1/glitch-agent/interact`: Same as `command`, taking `command`/`context` as query params
- `POST /v1/glitch-agent/command`: Process a natural language command
- `GET /v1/glitch-agent/execution/{request_id}`: Get the result of a command execution
- `GET /v1/glitch-agent/history`: Get history of command executions
- `POST /v1/glitch-agent/stop-browser`: Stop all browser instances

## Example Usage

You can use the included test script to see GlitchAgent in action:

```bash
cd backend
python tests/test_glitch_agent.py
```

This will demonstrate a workflow of:
1. Logging into GitHub
2. Searching for "playwright python"
3. Clicking on the first search result

## Sample Commands

GlitchAgent can understand commands like:

- "Log into GitHub using my credentials"
- "Search for 'playwright python' on GitHub"
- "Click on the first search result"
- "Fill out the contact form on example.com"
- "Navigate to amazon.com and search for headphones"

## Project Structure

```
GlitchAgent/
├── backend/
│   ├── main.py                  # FastAPI application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── src/
│   │   ├── models/              # Pydantic models
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── utils/               # Utility functions
│   │   └── settings/            # Application settings
│   ├── Dockerfile, render.yaml  # Deploy
│   └── tests/                   # pytest suite + demo script
└── README.md                    # This file
```

## Level 1 Implementation

This implementation satisfies the Level 1 requirements of the Crustdata Build Challenge:
- Implements the Interact API to execute commands
- Handles errors (timeouts, invalid selectors)
- Demonstrates the Login → Search → Interact workflow

## Future Enhancements (Level 2+)

- Extract API for data scraping
- Support for proxies and extensions
- Scheduled tasks
- Conversational memory
- Cross-platform support

## License

MIT
