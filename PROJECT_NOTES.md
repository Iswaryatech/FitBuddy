# MoveMap Project Notes

## Requirement to implementation

- 7-day personalised plan with offline fallback: `app/planner.py`
- Nutrition and recovery tip with offline fallback: `app/tips.py`
- Feedback update with local fallback: `app/revise.py`
- Persistence: `app/database.py` + `app/models.py` (SQLite, SQLAlchemy)
- Routing and API: `app/routes.py`
- UI: `templates/` + `static/`
- Coach view: `templates/coach.html`
- Local run: Uvicorn. Cloud: `render.yaml`

## Architecture

```text
Browser (Jinja2 pages + a little JS)
   |
FastAPI routes.py -- validation (Pydantic)
   |
services.py
   |-- planner.py / tips.py / revise.py --> Gemini (ai.py) or built-in fallback
   |
SQLite via SQLAlchemy (Member, WeekPlan)
```

## Viva explanation

"When a user submits their details, FastAPI validates them. If Gemini is configured, it writes the 7-day plan and nutrition tip as structured JSON, which the app validates before using; if Gemini is unavailable or returns something unusable, the built-in planner produces the plan, so users always get one. The plan is saved with SQLAlchemy in SQLite and shown as a week route, where each day opens its warm-up, main set, cool-down and recovery. Feedback is applied to the original plan by Gemini or by local rules, and saved separately so the original is preserved and both versions can be compared."

## Presentation screens

1. Home with the route illustration and the form
2. Week route with a day open
3. Fuel and recovery tip
4. Feedback and quick suggestions
5. Updated plan with "What changed"
6. Coach view
7. `/docs`
8. Architecture diagram above

## Future improvements

Login for the coach view, feedback history, progress tracking, exercise library with images, charts, PDF export, PostgreSQL, rate limiting, multilingual UI.
