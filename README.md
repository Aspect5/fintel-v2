## FINTEL v2 – Modular, Config‑Driven Multi‑Agent Financial Intelligence

FINTEL v2 is a web-based, config-driven environment for designing and executing multi-agent financial analysis workflows. The system is deliberately modular and easy to reconfigure:
- **Backend is the single source of truth** for agents, tools, and workflows
- **Behavior is configured via YAML** in `backend/config/` (not hardcoded)
- **Providers are pluggable** (OpenAI, Google, Local)
- **Frontend is a thin client** that consumes backend APIs

Built on a unified, declarative workflow model using the `controlflow` library.

### Why modular and config-driven
- **Re-target different workflows/use cases** by editing YAML
- **Swap agents/tools/providers** without touching Python code
- **Validation and health checks** expose config issues early

### Repository overview (key paths)
- `backend/app.py`: Flask API and workflow execution
- `backend/config/`: system configuration (single source of truth)
  - `settings.py`: env-driven settings and provider selection
  - `agents.yaml`: agent definitions, tools, capabilities
  - `tools.yaml`: tool registry with API key requirements and examples
  - `workflow_config.yaml`: workflows (agent roles, deps, defaults)
- `backend/{agents,providers,tools,workflows,registry,utils}`: modular building blocks
- `frontend/`: Vite React app
- `docs/`: in-depth design docs (logging, SSOT, production blueprint)

## Prerequisites
- Node.js v18+
- Python 3.9+ with `pip`

## First-time setup

1) Create and activate a Python virtual environment
- macOS/Linux:
```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
```
- Windows (PowerShell):
```powershell
python -m venv backend/venv
backend\venv\Scripts\activate
```

2) Install backend dependencies
```bash
pip install -r backend/requirements.txt
```

3) Install frontend dependencies
```bash
npm install
```

4) Configure environment variables
- Create a `.env` in the repo root (preferred) or `backend/.env`.
- At least one LLM provider key is required (OpenAI or Google). For market/economic data tools, Alpha Vantage and FRED keys are used.
```env
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx
ALPHA_VANTAGE_API_KEY=xxx
FRED_API_KEY=xxx
# Optional:
# DEFAULT_PROVIDER=openai|google|local
# LOG_LEVEL=INFO|DEBUG|WARNING|ERROR|CRITICAL
# LOCAL_BASE_URL=http://127.0.0.1:8080/v1
```

## Run locally

- Start both backend and frontend:
```bash
npm run dev
```
- Start individually:
```bash
npm run dev:backend
npm run dev:frontend
```
- Default ports:
  - Backend: `http://localhost:5001`
  - Frontend: `http://localhost:9002`

## The modular, config‑driven model

- **Settings**: env-driven provider configuration and defaults (`backend/config/settings.py`).
- **Agents**: declared in `backend/config/agents.yaml` with tools and capabilities.
- **Tools**: declared in `backend/config/tools.yaml` with API key requirements, categories, and examples.
- **Workflows**: declared in `backend/config/workflow_config.yaml` with agent roles, dependencies, and defaults.

Example workflow (excerpt):
```yaml
workflows:
  quick_stock_analysis:
    name: "Quick Stock Analysis"
    description: "Fast, high-level analysis..."
    agents:
      - name: "MarketAnalyst"
        role: "market_analysis"
        required: true
        fallback: "FinancialAnalyst"
        tools: ["get_market_data", "get_company_overview", "get_mock_news"]
      - name: "RiskAssessment"
        role: "risk_assessment"
        required: true
        fallback: "FinancialAnalyst"
        tools: ["get_market_data", "get_mock_analyst_ratings"]
      - name: "Summarizer"
        role: "synthesis"
        required: true
        tools: []
        dependencies: ["market_analysis", "risk_assessment"]

settings:
  default_workflow: "quick_stock_analysis"
  enable_fallback_agents: true
```

Example agent (excerpt):
```yaml
agents:
  FinancialAnalyst:
    name: "FinancialAnalyst"
    tools:
      - "detect_stock_ticker"
      - "get_market_data"
      - "get_company_overview"
      - "get_economic_data_from_fred"
    capabilities:
      - "market_analysis"
      - "economic_analysis"
      - "risk_assessment"
    required: true
    enabled: true
```

Example tool (excerpt):
```yaml
tools:
  get_economic_data_from_fred:
    name: "get_economic_data_from_fred"
    description: "Get economic data from FRED..."
    category: "economic_data"
    function: "get_economic_data_from_fred"
    class: "EconomicDataTool"
    api_key_required: "fred"
    enabled: true
    examples:
      - "get_economic_data_from_fred(series_id='GDP')"
```

## Extending the system

- **Add a tool**
  1) Implement or reuse a function in `backend/tools/` (e.g., `market_data.py`, `economic_data.py`).
  2) Declare it in `backend/config/tools.yaml` with `function`, optional `class`, `api_key_required`, `examples`.
  3) If it needs an API key, add the key to `.env`.
  4) Reference the tool from agents in `agents.yaml` and workflows in `workflow_config.yaml`.

- **Add an agent**
  1) Add a new agent under `agents:` in `backend/config/agents.yaml` with `tools`, `capabilities`, and `enabled`.
  2) Optionally add templates/logic in `backend/agents/` if needed.
  3) Reference the agent in a workflow via `workflow_config.yaml` with `role`, `required`, and `fallback`.

- **Add a workflow**
  1) Add a new entry in `backend/config/workflow_config.yaml` under `workflows:`.
  2) List agent roles, required flags, fallbacks, dependencies.
  3) Optionally update `settings.default_workflow`.

- **Switch providers (OpenAI, Google, Local)**
  - Configure keys or `LOCAL_BASE_URL` in `.env`.
  - The selected provider can be passed by the client or defaults to `DEFAULT_PROVIDER`.
  - Provider settings live in `backend/config/settings.py`.

## Core APIs (selected)

- **Health and status**
  - `GET /api/health`
  - `GET /api/providers`
  - `GET /api/agents`
  - `GET /api/registry/{health|status|validation|summary}`

- **Tools and workflows**
  - `GET /api/registry/tools`
  - `GET /api/workflows`
  - `GET /api/workflow-configs`

- **Execute a workflow**
  - `POST /api/run-workflow`
    - body: `{ "query": "Analyze Apple", "provider": "openai", "workflow_type": "quick_stock_analysis" }`
  - `GET /api/workflow-status/{workflow_id}`
  - `GET /api/workflow-stream/{workflow_id}` (SSE)

Example:
```bash
curl -X POST http://localhost:5001/api/run-workflow \
  -H 'Content-Type: application/json' \
  -d '{"query":"Analyze AAPL for a quick go/no-go","provider":"openai","workflow_type":"quick_stock_analysis"}'
```

## Frontend usage
- Open `http://localhost:9002`.
- Choose provider and submit a query. The UI visualizes nodes/edges and polls `GET /api/workflow-status/{id}` for progress.

## Observability and logs
- Backend logs to console and `logs/` (see `docs/LOGGING_SYSTEM.md`).
- Workflow metrics: `GET /api/workflow-metrics`.
- Health checks and validation endpoints expose configuration issues.

## Developer workflow
- Python lint: `make -C backend lint-py`
- Python dead code: `make -C backend deadcode-py`
- JS/TS dead code: `npm run check:js` (runs ts-prune + depcheck)
- Clean dev processes: `npm run clean`

## Troubleshooting
- **Backend not ready**: hit `GET /api/health`. Ensure venv is active and `.env` keys exist.
- **Missing data tools**: set `ALPHA_VANTAGE_API_KEY` / `FRED_API_KEY`.
- **Provider errors**: verify `OPENAI_API_KEY` or `GOOGLE_API_KEY`; check `DEFAULT_PROVIDER`.
- **Port conflicts**: adjust `BACKEND_PORT` or Vite port.

## Further reading
- Single Source of Truth: `docs/SINGLE_SOURCE_OF_TRUTH_ARCHITECTURE.md`
- Logging: `docs/LOGGING_SYSTEM.md`
- Production blueprint (BFF, security): `docs/ARCHITECTURAL_BLUEPRINT_FOR_PRODUCTION.md`
