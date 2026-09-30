from pathlib import Path

from fastapi.templating import Jinja2Templates

from .planner import FULL_DAYS, KIND_LABEL

BASE = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
templates.env.filters["date"] = lambda v: v.strftime("%d %b %Y") if v else ""
templates.env.globals.update(KIND_LABEL=KIND_LABEL, FULL_DAYS=FULL_DAYS)
