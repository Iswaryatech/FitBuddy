# MoveMap: your week, mapped out

MoveMap is a FastAPI + Jinja2 web app that builds a personalised 7-day plan of strength, cardio and recovery, adds a nutrition and recovery tip, and reshapes the plan when you give feedback. It uses Gemini when a key is configured and falls back to a built-in planner otherwise, so it always works.

It has the same features as FitBuddy, with a new name, new interface and new content:

| | |
|---|---|
| **Route view** | The week is drawn as a path with seven stops. Click a day to open its warm-up, main set, cool-down and recovery note. |
| **Plan versions** | Feedback creates an "Updated" plan next to the "Original". A "What changed" list explains each edit. |
| **Coach view** | Expandable member rows with a week overview, fuel tip, latest feedback, open plan and delete. |
| **API** | `/docs` shows a JSON API for creating, reading, revising and deleting plans. |
| **Health check** | `/health` reports status and whether Gemini is connected. |

## Run it (Windows)

```cmd
setup_windows.bat
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Or manually:

```cmd
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 (also `/coach`, `/docs`, `/health`).

## Turn on Gemini (optional)

Edit `.env`:

```env
GEMINI_API_KEY=your_real_key
FITNESS_MODEL=gemini-3.8-flash
TIP_MODEL=gemini-3.8-flash
```

Check the model names against Google's current model list; they are plain settings, so changing them needs no code edits. If a Gemini call fails or returns something unusable, MoveMap silently uses the built-in planner for that request.

## Project structure

```text
movemap/
├── app/
│   ├── main.py        app + startup (creates tables)
│   ├── routes.py      pages (HTML) and JSON API
│   ├── services.py    create plan, apply feedback, payloads
│   ├── planner.py     7-day plan: Gemini + built-in planner + validation
│   ├── tips.py        nutrition / recovery tip: Gemini + built-in
│   ├── revise.py      feedback revision: Gemini + keyword rules
│   ├── ai.py          safe Gemini wrapper (returns None on any failure)
│   ├── models.py      SQLAlchemy: Member, WeekPlan
│   ├── schemas.py     Pydantic validation
│   ├── database.py    engine / session
│   ├── config.py      environment settings
│   └── templating.py  Jinja2 setup
├── templates/         base, index, plan, coach, message
├── static/            css/app.css, js/app.js
├── tests/test_app.py  28 tests (pytest)
├── requirements.txt / requirements-dev.txt
├── render.yaml        Render deployment
└── setup_windows.bat
```

## Tests

```cmd
venv\Scripts\python.exe -m pip install -r requirements-dev.txt
venv\Scripts\python.exe -m pytest -q
```

## How feedback works

Feedback is always applied to the **original** plan, so a new round replaces the last one instead of stacking edits. The original is never overwritten. Without Gemini, the built-in reviser understands requests about cardio, rest or recovery, shorter or easier or harder sessions, core work and stretching. Anything else is saved but leaves the plan unchanged, and the app says so.

## Deployment (Render)

`render.yaml` builds with `pip install -r requirements.txt` and starts Uvicorn with `/health` as the health check. Add `GEMINI_API_KEY` as a secret environment variable. SQLite on Render's free tier is reset on redeploy; for permanent data, set `DATABASE_URL` to a PostgreSQL URL and add `psycopg2-binary` to requirements.

## Safety note

MoveMap is a demonstration and general wellness app. It is not medical advice, diagnosis or treatment. Anyone with an injury, medical condition, pregnancy or pain should check with a qualified professional first.
