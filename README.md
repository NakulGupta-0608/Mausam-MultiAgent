# MausamAI — Autonomous Multi-Agent Weather Intelligence Engine

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-6.0+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)

**MausamAI** is an autonomous multi-agent decision support platform that converts complex meteorological data into personalized, actionable outdoor recommendations. Instead of simple temperature numbers, MausamAI orchestrates specialized AI agents to analyze intent, evaluate risks, suggest time windows, and curate gear checklists.

GitHub Repository: [https://github.com/NakulGupta-0608/Mausam-MultiAgent](https://github.com/NakulGupta-0608/Mausam-MultiAgent)

---

## 🌟 Key Features

- **Natural Language Question Input**: Chat-style query interface with quick prompts (e.g., *"Can I plan an alpine day trek with clear visibility and moderate winds?"*).
- **Target Location & Date Selector**: Quick presets for global cities or arbitrary locations with automatic geocoding and date scheduling.
- **Dynamic Meteorological Telemetry**: Fetches real-time, non-hardcoded forecasts (via Open-Meteo API / dynamic physics-based fallback model) covering temperature, feels like, humidity, wind speed & direction, rain probability, UV index, and AQI.
- **Analysis Progress Panel**: Real-time visual feedback tracking each stage of the multi-agent pipeline.
- **Synthesized Recommendation Card**:
  - Outdoor suitability score (0–100)
  - Clear categorical verdict (*Optimal*, *Caution*, *Unfavorable*, *Severe*)
  - Activity feasibility window and backup alternatives
  - Dynamic packing checklist with interactive checkable items
  - Categorized atmospheric hazard and mitigation warnings
- **Saved Expeditions & Plans**: Pin, review, and manage weather plans directly from the dashboard.
- **Notification Center**: Real-time severe weather advisories, seasonal warnings, and system health status.
- **Agent Execution Trace**: Full observability with millisecond duration metrics, status tags, and inspectable input/output payloads for every agent step.

---

## 🏗️ Multi-Agent Architecture

```
[ User Input: Query + Location + Date ]
                   │
                   ▼
┌──────────────────────────────────────────────┐
│       WeatherIntelligencePipeline            │
│  (Orchestration & Trace Telemetry Engine)    │
└──────────────────────┬───────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ WeatherAnalyst │ │ActivityPlanner │ │  RiskAssessor  │
│     Agent      │ │     Agent      │ │     Agent      │
└────────┬───────┘ └────────┬───────┘ └────────┬───────┘
         │                  │                  │
         │ Geocoding &      │ Feasibility,     │ Hazard alerts &│
         │ Telemetry        │ Windows & Gear   │ Final Verdict │
         └─────────────┬────┴─────────────┬────┘
                       │                  │
                       ▼                  ▼
               [ Synthesis Card ]  [ Execution Trace ]
```

### Agent Roles

1. **`WeatherAnalystAgent`** (`backend/app/agents/weather_analyst.py`):
   - Resolves geographic coordinates using `geo_service`.
   - Queries dynamic atmospheric providers and computes the baseline outdoor comfort index.
2. **`ActivityPlannerAgent`** (`backend/app/agents/activity_planner.py`):
   - Categorizes user activity intent (trekking, endurance sports, outdoor gatherings, photography, etc.).
   - Computes feasibility windows, backup alternatives, and dynamic gear requirements.
3. **`RiskAssessorAgent`** (`backend/app/agents/risk_assessor.py`):
   - Scans for adverse weather conditions (precipitation squalls, wind gusts, extreme UV, poor AQI).
   - Generates hazard mitigation advice and determines the final verdict badge.

---

## 📁 Repository Structure

```
MAUSAM/
├── .gitignore                      # Git ignore rules (Python, Node, logs, envs)
├── .env.example                    # Global environment template
├── README.md                       # Documentation & setup guide
│
├── backend/                        # Python FastAPI Backend
│   ├── .env.example                # Backend environment configuration template
│   ├── .env                        # Local development settings
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # FastAPI application entrypoint
│   └── app/
│       ├── core/
│       │   └── config.py           # Pydantic Settings configuration
│       ├── schemas/                # Pydantic data schemas
│       │   ├── weather.py          # GeoLocation, WeatherCondition, Forecast
│       │   ├── analysis.py         # AnalysisRequest, AnalysisResponse, Trace
│       │   ├── plan.py             # SavedPlan, CreatePlanRequest
│       │   └── notification.py     # NotificationItem
│       ├── tools/                  # Pluggable external tools & providers
│       │   ├── geo_service.py      # Geocoding service with online/fallback
│       │   └── weather_api.py      # Dynamic Open-Meteo & meteorological physics model
│       ├── agents/                 # Specialized autonomous agents
│       │   ├── base.py             # BaseAgent abstract class
│       │   ├── weather_analyst.py  # Atmospheric intelligence agent
│       │   ├── activity_planner.py # Activity feasibility agent
│       │   └── risk_assessor.py    # Hazard evaluation agent
│       ├── orchestration/          # Multi-agent coordination
│       │   ├── state.py            # WorkflowState shared context
│       │   └── workflow.py         # Pipeline orchestrator
│       ├── monitoring/             # Observability & tracing
│       │   ├── logger.py           # Structured logging
│       │   └── tracer.py           # Agent execution trace collector
│       ├── storage/                # Data persistence
│       │   └── memory_store.py     # Thread-safe in-memory store for plans & alerts
│       └── api/
│           ├── __init__.py         # Combined API router
│           └── routes/
│               ├── health.py       # Health check route
│               ├── weather.py      # Weather lookup route
│               ├── analysis.py     # Analysis pipeline route
│               ├── plans.py        # Saved plans CRUD routes
│               └── notifications.py# Notification center routes
│
└── frontend/                       # React + Vite + Tailwind CSS Frontend
    ├── index.html                  # HTML entrypoint with modern fonts
    ├── package.json                # Frontend dependencies & scripts
    ├── vite.config.js              # Vite config with API proxy
    ├── tailwind.config.js          # Tailwind CSS design system
    ├── postcss.config.js           # PostCSS configuration
    ├── .env.example                # Frontend environment template
    ├── .env                        # Frontend environment variables
    └── src/
        ├── main.jsx                # React DOM mounting
        ├── App.jsx                 # Main application dashboard
        ├── index.css               # Tailwind directives & glassmorphic styling
        ├── api/
        │   └── client.js           # Fetch API client connecting to backend
        └── components/
            ├── Header.jsx              # Brand, live health badge, notifications
            ├── ChatQueryInput.jsx      # Chat-style natural language query input
            ├── LocationDateForm.jsx    # Location input, date picker & analyze button
            ├── AnalysisProgress.jsx    # Real-time multi-agent progression bar
            ├── WeatherOverview.jsx     # Atmospheric metrics & 5-day forecast
            ├── RecommendationCard.jsx  # Verdict badge, score, feasibility, packing
            ├── SavedPlans.jsx          # Pinned plans & expedition cards
            ├── NotificationCenter.jsx  # Slide-over alert & advisory center
            └── AgentExecutionTrace.jsx # Collapsible step-by-step telemetry viewer
```

---

## 🚀 Quickstart Guide

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher
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
   # From the project root:
   python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
   *The backend will be available at `http://127.0.0.1:8000` with interactive API docs at `http://127.0.0.1:8000/docs`.*

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
   *The frontend dashboard will be running at `http://localhost:5173`.*

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service status, version, and active agents |
| `GET` | `/api/weather/current?location={city}&date={YYYY-MM-DD}` | Current and 5-day weather telemetry |
| `POST` | `/api/analysis` | Executes the multi-agent pipeline (`query`, `location`, `target_date`) |
| `GET` | `/api/plans` | Retrieves all saved plans |
| `POST` | `/api/plans` | Saves an expedition plan |
| `DELETE` | `/api/plans/{id}` | Deletes a saved plan |
| `GET` | `/api/notifications` | Retrieves weather advisories and notices |
| `PATCH`| `/api/notifications/{id}/read` | Marks a notification as read |
| `POST` | `/api/notifications/read-all` | Marks all notifications as read |

---

## 🧩 Next Steps & Roadmap

- [ ] Connect Gemini 1.5 / 2.0 or OpenAI LLM API to agents for advanced reasoning.
- [ ] Add vector store memory for long-term user preferences and historical weather patterns.
- [ ] Integrate radar and satellite precipitation map overlays.
- [ ] Implement push notifications / WebSockets for live severe weather updates.

---

## 📄 License

MIT License. Designed and engineered for the MausamAI Multi-Agent Ecosystem.
