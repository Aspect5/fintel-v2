# Fintel v2

Fintel is a multi-agent financial analysis platform. You ask it a question like "Should I invest in Palantir?", it assembles a team of LLM agents (market analyst, risk assessment, news sentiment, economic analyst, summarizer), runs them against live market and economic data, and streams the workflow back to a React UI that renders the agents and their dependencies as a live graph. The output is a structured investment report with the tool calls each agent made.

The design goal is that agents, tools, and workflows are data, not code. All three are declared in YAML under `backend/config/`, validated at startup by a registry manager, and served to the frontend through the API. Adding a new workflow or rewiring which agent uses which tool is a YAML edit, not a Python change.

## How it works

Three YAML files are the single source of truth:

- `backend/config/agents.yaml` defines six agents (FinancialAnalyst, MarketAnalyst, EconomicAnalyst, RiskAssessment, NewsSentimentAnalyst, Summarizer), each with its instructions, tools, and capabilities.
- `backend/config/tools.yaml` registers around 38 tools (Alpha Vantage market data, fundamentals, technical indicators, FRED economic series, plus utilities) with their categories, API key requirements, and call examples.
- `backend/config/workflow_config.yaml` composes agents into workflows with roles, dependencies, and fallbacks.

A workflow declaration looks like this (from `workflow_config.yaml`):

```yaml
macroeconomic_outlook:
  name: "Macroeconomic Outlook"
  description: "Assesses the overall economic climate using key indicators like GDP, inflation, and unemployment."
  agents:
    - name: "EconomicAnalyst"
      role: "economic_data_analysis"
      required: true
      tools: ["get_economic_data_from_fred"]
    - name: "RiskAssessment"
      role: "macro_risk_assessment"
      required: false
      fallback: "EconomicAnalyst"
      tools: ["get_economic_data_from_fred"]
    - name: "Summarizer"
      role: "economic_summary"
      required: true
      tools: []
      dependencies: ["economic_data_analysis", "macro_risk_assessment"]
```

`dependencies` controls execution order: the Summarizer waits for the analysis roles to finish. `fallback` lets a workflow degrade instead of failing when an optional agent is disabled or missing keys. At startup the `RegistryManager` (`backend/registry/manager.py`) cross-validates the three files, so a workflow referencing a tool that no agent has, or a tool missing its API key, surfaces as a validation error on `/api/registry/validation` rather than a runtime failure.

Execution is built on the `controlflow` library (Prefect-based). `backend/workflows/config_driven_workflow.py` turns a YAML workflow into ControlFlow tasks, runs them, and pushes status events that the frontend consumes via polling (`/api/workflow-status/{id}`) and SSE (`/api/workflow-stream/{id}`).

Three workflows ship today: `quick_stock_analysis`, `competitor_deep_dive`, and `macroeconomic_outlook`.

## Stack

- Backend: Python, Flask, ControlFlow, Pydantic. Providers are pluggable: OpenAI, Google Gemini, or a local OpenAI-compatible endpoint (`LOCAL_BASE_URL`), selected per request or via `DEFAULT_PROVIDER`.
- Data: Alpha Vantage (quotes, fundamentals, news sentiment, insider transactions, technicals) and FRED (economic series). Tools fall back to clearly labeled mock data when keys are absent, so the system runs end to end without paid keys.
- Frontend: React 18, Vite, TypeScript, Zustand, ReactFlow for the workflow graph, Tailwind.
- Modeling: there is a small quantitative layer in `backend/tools/` (`feature_builder.py`, `model_inference.py`, `backtesting.py`) that engineers features from price/news/insider data, trains a scikit-learn baseline classifier, and runs walk-forward backtests. These are registered as agent tools (`build_features`, `train_model`, etc.) and covered by the pytest suite in `tests/`.

## Running it

Requires Node 18+ and Python 3.9+.

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
npm install
```

Create a `.env` in the repo root (see `backend/.env.example`). At least one LLM key is required:

```env
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
ALPHA_VANTAGE_API_KEY=...   # optional, mock data without it
FRED_API_KEY=...            # optional, mock data without it
```

Then:

```bash
npm run dev
```

This starts the Flask backend on port 5001, waits for `/api/health`, and starts the Vite frontend on port 9002. Or hit the API directly:

```bash
curl -X POST http://localhost:5001/api/run-workflow \
  -H 'Content-Type: application/json' \
  -d '{"query":"Analyze AAPL for a quick go/no-go","provider":"openai","workflow_type":"quick_stock_analysis"}'
```

Useful endpoints: `/api/health`, `/api/workflows`, `/api/registry/tools`, `/api/registry/validation`, `/api/workflow-metrics`.

## Extending it

To add a tool: implement the function in `backend/tools/`, declare it in `tools.yaml` (with `function`, `api_key_required`, `examples`), and reference it from an agent in `agents.yaml`. To add a workflow: add an entry in `workflow_config.yaml` listing agent roles, dependencies, and fallbacks. The registry validation will tell you if you wired something wrong.

## Status and caveats

This is a working prototype, not a production service. Known limitations:

- Free-tier Alpha Vantage rate limits are low; some tools return labeled mock data when limits or keys block real calls.
- Workflow state is held in memory in the Flask process; there is no persistence or auth. `docs/ARCHITECTURAL_BLUEPRINT_FOR_PRODUCTION.md` covers what productionizing would take (BFF, security, state).
- The baseline model is intentionally simple (StandardScaler plus class-weighted logistic regression); the point is the plumbing from features to walk-forward evaluation, not alpha.

Dev tooling: `make -C backend lint-py` (ruff), `npm run check:js` (ts-prune + depcheck), `pytest` for the modeling layer.

## Further reading

- `docs/SINGLE_SOURCE_OF_TRUTH_ARCHITECTURE.md` for the registry/validation design
- `docs/LOGGING_SYSTEM.md` for structured logging
