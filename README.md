# MausamAI — Autonomous Multi-Agent Weather Intelligence Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Pytest](https://img.shields.io/badge/Pytest-22%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](https://pytest.org)

**MausamAI** is an autonomous multi-agent decision support platform that converts complex meteorological data into personalized, actionable outdoor recommendations. Instead of simple temperature numbers or synthetic approximations, MausamAI orchestrates 5 specialized AI agents to plan tasks, acquire verified real-world telemetry, evaluate configurable transparent risk rules, synthesize comparative operational options with stated limitations, and validate decisions through an adversarial critic with bounded review loops.

GitHub Repository: [https://github.com/NakulGupta-0608/Mausam-MultiAgent](https://github.com/NakulGupta-0608/Mausam-MultiAgent)

---

## 🌟 Implemented Tasks & Features

### 1. Initial Full-Stack Foundation (Task 1)
- **FastAPI Modular Backend**: Structured cleanly into `agents/`, `orchestration/`, `tools/`, `monitoring/`, `storage/`, and `api/routes/`.
- **Modern Responsive Dashboard**: React + Vite + Tailwind CSS featuring natural-language chat input, location and date selection, progress ticker, recommendation cards, saved plans, notification drawer, and agent trace.
- **Environment Management**: Robust Pydantic settings with `.env.example` templates.

### 2. Empirical Weather API Integration (Task 2)
- **Zero Synthetic Fabrication**: Live Open-Meteo telemetry querying with strict Pydantic schema validation. Never invents values or substitutes unverified mock numbers.
- **Resilience & Bounded Retries**: Max 2 retries with exponential backoff on HTTP/network timeouts.
- **Domain Exceptions**: Distinct typed error classes (`LocationNotFoundException`, `WeatherApiTimeoutException`, `WeatherApiErrorException`, `MalformedResponseException`).
- **Visible Degraded State**: Displays actionable UI (`WeatherDegradedState.jsx`) on failure with error codes, retried counts, and fallback suggestions.

### 3. Multi-Agent 5-Component Architecture (Task 3 & 4)
- **Shared State Orchestrator**: `WeatherIntelligencePipeline` coordinates state across all 5 agents.
- **Review Capping at 2 Cycles**: Critic review loops are strictly capped at 2 iterations to eliminate infinite loops.
- **Budget & Stopping Conditions**: Hard budget ceilings on execution steps, time duration, and cost estimation.
- **Audit Trace**: Every agent records action, input, output, duration in ms, and explicit reasoning.

### 4. User Experience & Real-Time SSE Streaming (Task 5)
- **Server-Sent Events (SSE)**: `POST /api/analysis/stream` streams live task dispatches directly from the backend to the frontend.
- **Genuine Progress Bar**: Replaced client-side `setTimeout` timers with actual agent lifecycle events.
- **Decision Output Synthesis**:
  - Suitability score ($0-100$) and verdict badges (*Optimal*, *Caution*, *Unfavorable*, *Severe*).
  - Grounded empirical evidence citations linking decision points to observed telemetry.
  - Comparative operational options (Primary Window, Dawn Window, Sheltered/Indoor Backup) with pros/cons.
  - Stated forecast limitations disclosing meteorological horizon boundaries.
- **Expandable Decision Trace**: Displays agent name, action, status, review decision, retries, duration, and reasoning.
- **Insufficient-Data UI**: Dedicated `InsufficientDataState.jsx` when Critic halts on `NEEDS_MORE_DATA`.
- **Zero Mock Results**: Pre-seeded fake plans purged; saved plans only contain genuine user-saved records.

### 5. Smart Monitoring for Saved Plans (Task 6)
- **Persistent SQLite Database**: Thread-safe storage storing plan subject, location, action, target date, original weather snapshot, initial recommendation, and notification preferences.
- **Background Scheduler**: Periodic background loop polling active plans with configurable intervals (30s, 60s, 120s, etc.) and rate-limiting safeguards against excessive external API calls.
- **Configurable Meaningful Change Detection**: Filters out minor fluctuations (e.g. $\pm 0.3^\circ\text{C}$ jitter) and triggers exclusively on significant shifts ($\ge 15\%$ rain prob, $\ge 12\text{ km/h}$ wind delta, severe condition transitions).
- **Automated Agent Re-Triggering**: On significant change, automatically re-runs `RiskAnalysisAgent`, `RecommendationAgent`, and `CriticAgent`, updating the plan's score, verdict, options, and change history.
- **Repeat Notification Deduplication**: Composite state signature hashing suppresses duplicate alert spam while ensuring genuine shifts are dispatched immediately.
- **Automatic Stopping Condition**: Once a plan's target date passes, monitoring concludes automatically and transitions the plan to `expired`.
- **Interactive Monitoring Dashboard**: Live status indicator, relative last-checked timestamps, detected change diffs, before-and-after recommendation comparisons, manual re-check triggers, and simulated change test controls.

---

## 🏗️ 5-Component Multi-Agent Architecture

```
[ User Input: Query + Location + Target Date ]
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 WeatherIntelligencePipeline                 │
│         (Central Orchestrator, Budget & Stopping Engine)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 1. ┌──────────────┐                       2. ┌──────────────┐
    │ PlannerAgent │                          │  DataAgent   │
    │  (Intent &   │                          │(Real Weather │
    │ Constraints) │                          │  Validation) │
    └───────┬──────┘                          └───────┬──────┘
            │ Structured Plan                         │ Verified Telemetry
            └──────────────────┬──────────────────────┘
                               │
                               ▼
                        3. ┌──────────────┐
                           │ RiskAnalysis │
                           │    Agent     │
                           │(Rule Engine) │
                           └───────┬──────┘
                                   │ Penalties & Suitability Score
                                   ▼
                        4. ┌──────────────┐
                           │Recommendation│ ◄────────────────┐
                           │    Agent     │                  │ Revisions
                           │ (3 Options)  │                  │ (Capped at 2)
                           └───────┬──────┘                  │
                                   │ Draft Decision          │
                                   ▼                         │
                        5. ┌──────────────┐                  │
                           │ CriticAgent  │                  │
                           │(Verification)│ ──[ REJECT ]─────┘
                           └───────┬──────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │                           │
              [ APPROVE ]               [ NEEDS_MORE_DATA ]
                     │                           │
                     ▼                           ▼
          [ Final Decision Card ]     [ Insufficient Data State ]
```

### Agent Roles & Responsibilities

| Agent Name | Primary Action | Responsibility |
|---|---|---|
| **PlannerAgent** | `DECONSTRUCT_USER_REQUEST` | Deconstructs natural-language queries into structured task plans (activity, sub-goals, environmental thresholds). |
| **DataAgent** | `ACQUIRE_VERIFIED_TELEMETRY` | Geocodes target coordinates and queries real-world Open-Meteo models with schema validation and bounded retries. |
| **RiskAnalysisAgent** | `EVALUATE_CONFIGURABLE_RULES` | Evaluates transparent, configurable risk rules against empirical precipitation, wind, UV, and thermal comfort. |
| **RecommendationAgent** | `SYNTHESIZE_DECISION_AND_COMPARE_OPTIONS` | Formulates 3 comparative operational options, cites grounded telemetry evidence, and articulates stated limitations. |
| **CriticAgent** | `VALIDATE_RECOMMENDATION_AGAINST_SOURCE_DATA` | Adversarially fact-checks recommendations against source data; returns `APPROVE`, `REJECT` (with correction request), or `NEEDS_MORE_DATA`. |

---

## 📁 Repository Structure

```
MAUSAM/
├── .gitignore                      # Git ignore rules (Python, Node, logs, envs)
├── .env.example                    # Global environment template
├── pytest.ini                      # Pytest configuration
├── README.md                       # Comprehensive project documentation
│
├── backend/                        # Python FastAPI Backend
│   ├── .env.example                # Backend environment configuration template
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # FastAPI application entrypoint
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings configuration
│   │   │   └── exceptions.py       # Domain-specific typed exceptions
│   │   ├── schemas/                # Pydantic data schemas
│   │   │   ├── weather.py          # GeoLocation, WeatherCondition, Forecast
│   │   │   ├── analysis.py         # StructuredPlan, RuleEvaluation, Trace, etc.
│   │   │   ├── plan.py             # SavedPlan, CreatePlanRequest
│   │   │   └── notification.py     # NotificationItem
│   │   ├── tools/                  # Pluggable external tools & providers
│   │   │   ├── geo_service.py      # Geocoding service with bounded retries
│   │   │   └── weather_api.py      # Open-Meteo client with Pydantic validation
│   │   ├── agents/                 # Specialized autonomous agents
│   │   │   ├── base.py             # BaseAgent abstract class
│   │   │   ├── planner.py          # PlannerAgent: intent decomposition
│   │   │   ├── data_agent.py       # DataAgent: empirical telemetry
│   │   │   ├── risk_analyst.py     # RiskAnalysisAgent: transparent rules
│   │   │   ├── recommendation.py   # RecommendationAgent: options & evidence
│   │   │   └── critic.py           # CriticAgent: adversarial critique
│   │   ├── orchestration/          # Multi-agent coordination
│   │   │   ├── state.py            # WorkflowState shared context
│   │   │   └── workflow.py         # Pipeline orchestrator & SSE generator
│   │   ├── monitoring/             # Observability & tracing
│   │   │   ├── logger.py           # Structured logging
│   │   │   └── tracer.py           # Agent execution trace collector
│   │   ├── storage/                # Data persistence
│   │   │   └── memory_store.py     # Thread-safe in-memory store
│   │   └── api/
│   │       ├── __init__.py         # Combined API router
│   │       └── routes/
│   │           ├── health.py       # Health check route
│   │           ├── weather.py      # Weather lookup route
│   │           ├── analysis.py     # Synchronous & SSE streaming analysis
│   │           ├── plans.py        # Saved plans CRUD routes
│   │           └── notifications.py# Notification center routes
│   └── tests/                      # Automated test suite
│       ├── test_weather_agent.py   # Weather API, retries, and error handling tests
│       └── test_multi_agent_workflow.py # Approval, critique, budget & SSE tests
│
└── frontend/                       # React + Vite + Tailwind CSS Frontend
    ├── index.html                  # HTML entrypoint
    ├── package.json                # Frontend dependencies & scripts
    ├── vite.config.js              # Vite config with API proxy
    ├── tailwind.config.js          # Tailwind CSS design system
    ├── src/
        ├── main.jsx                # React DOM mounting
        ├── App.jsx                 # Dashboard with live SSE integration
        ├── index.css               # Tailwind directives & glassmorphic styles
        ├── api/
        │   └── client.js           # API client with analyzeWeatherStream
        └── components/
            ├── Header.jsx              # Brand, live health badge, notifications
            ├── ChatQueryInput.jsx      # Chat-style natural language query input
            ├── LocationDateForm.jsx    # Location input, date picker & analyze button
            ├── AnalysisProgress.jsx    # Real-time multi-agent progression bar
            ├── WeatherOverview.jsx     # Verified atmospheric telemetry overview
            ├── WeatherDegradedState.jsx# Graceful degraded/error state display
            ├── InsufficientDataState.jsx# Critic NEEDS_MORE_DATA state display
            ├── RecommendationCard.jsx  # Verdict badge, score, 3 options, evidence
            ├── SavedPlans.jsx          # Pinned plans & expedition cards
            ├── NotificationCenter.jsx  # Slide-over alert & advisory center
            └── AgentExecutionTrace.jsx # Expandable decision trace & budget audit
```

---

## 🚀 Quickstart Guide

### Prerequisites

- **Python**: 3.10+ (tested on Python 3.13)
- **Node.js**: 18.0+
- **npm** or **yarn**

---

### Step 1: Backend Setup (FastAPI)

1. Open a terminal in the project root:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *Interactive API docs available at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Frontend Setup (React + Vite + Tailwind)

1. Open a second terminal and navigate to the frontend:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Dashboard available at `http://127.0.0.1:5173`.*

---

## 🧪 Testing Suite

MausamAI includes 22 automated tests covering unit tools, resilience retries, multi-agent approval/rejection loops, budget enforcement, SSE streaming, SQLite plan persistence, configurable threshold change detection, agent re-triggering, and notification deduplication.

Run all tests:
```bash
# From the project root:
.\backend\.venv\Scripts\pytest
```

### Test Coverage Highlights
- `test_weather_agent_success`: Real Open-Meteo telemetry fetch and Pydantic validation.
- `test_invalid_location_raises_typed_exception`: Verified `LocationNotFoundException`.
- `test_weather_api_timeout_bounded_retries`: Exponential backoff retries on timeouts.
- `test_multi_agent_approval_path`: Full 5-agent execution with Critic `APPROVE`.
- `test_critic_rejection_and_correction_cycle`: Flawed draft triggers Critic `REJECT` and correction loop.
- `test_critic_insufficient_data_rejection`: Incomplete telemetry triggers `NEEDS_MORE_DATA`.
- `test_orchestrator_review_capping_at_two`: Enforces review cap at 2 iterations.
- `test_multi_agent_streaming_workflow_e2e`: E2E Server-Sent Events (SSE) stream validation.
- `test_zero_hardcoded_plans_on_startup`: Verifies clean initial state with zero mock data.
- `test_database_plan_persistence_and_retrieval`: Persistent SQLite plan storage with snapshot and preferences.
- `test_minor_fluctuations_not_flagged_as_significant`: Verifies minor jitter (0.3°C temp, 2% rain) is filtered out.
- `test_meaningful_rain_and_wind_shift_flagged_as_significant`: Verifies significant shifts trigger change flags.
- `test_scheduler_re_triggers_agents_on_significant_change`: Automated re-trigger of Risk, Recommendation, and Critic agents.
- `test_scheduler_stops_monitoring_past_target_date`: Automatic expiration stopping condition when target date passes.
- `test_real_weather_live_plan_check`: Live Open-Meteo check on active saved plan.

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service status, version, and active agents |
| `GET` | `/api/weather?location={city}&date={YYYY-MM-DD}` | Live verified weather telemetry |
| `POST` | `/api/analysis` | Synchronous 5-agent pipeline execution |
| `POST` | `/api/analysis/stream` | Real-time Server-Sent Events (SSE) streaming pipeline |
| `GET` | `/api/plans` | Retrieves user-saved plans (`?status=active`) |
| `POST` | `/api/plans` | Saves a verified plan with snapshot & notification preferences |
| `GET` | `/api/plans/{id}` | Retrieves plan details with detected change audit history |
| `DELETE` | `/api/plans/{id}` | Deletes a saved plan |
| `POST` | `/api/plans/{id}/check` | Triggers immediate plan re-check (live or simulated) |
| `PATCH`| `/api/plans/{id}/status` | Toggles monitoring status (`active`, `paused`) |
| `GET` | `/api/monitoring/status` | Background scheduler status & polling configuration |
| `POST` | `/api/monitoring/trigger` | Triggers immediate monitoring pass across all active plans |
| `POST` | `/api/monitoring/interval` | Dynamically updates polling interval |
| `GET` | `/api/notifications` | Retrieves system advisories and deduplicated plan alerts |
| `PATCH`| `/api/notifications/{id}/read` | Marks notification as read |
| `POST` | `/api/notifications/read-all` | Marks all notifications as read |

---

## 📄 License

MIT License. Designed and engineered for the MausamAI Multi-Agent Ecosystem.
