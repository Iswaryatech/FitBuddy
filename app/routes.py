import json

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from . import services
from .config import gemini_enabled
from .database import get_db
from .models import Member
from .schemas import FIELD_HELP, GOALS, INTENSITIES, FeedbackIn, ProfileIn
from .templating import templates

router = APIRouter()
SOURCE_LABEL = {"gemini": "Written by Gemini", "builtin": "Built-in planner"}


def _message(request: Request, title: str, body: str, status: int):
    return templates.TemplateResponse(
        request, "message.html", {"title": title, "body": body}, status_code=status
    )


def _form_page(request: Request, values: dict | None = None, errors: dict | None = None, status: int = 200):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "goals": GOALS,
            "intensities": INTENSITIES,
            "values": values or {},
            "errors": errors or {},
            "ai_on": gemini_enabled(),
        },
        status_code=status,
    )


# ----------------------------- pages -----------------------------
@router.get("/", include_in_schema=False)
def home(request: Request):
    return _form_page(request)


@router.post("/generate", include_in_schema=False)
def generate(
    request: Request,
    name: str = Form(""),
    handle: str = Form(""),
    age: str = Form(""),
    weight: str = Form(""),
    goal: str = Form(""),
    intensity: str = Form(""),
    db: Session = Depends(get_db),
):
    raw = dict(name=name, handle=handle, age=age, weight=weight, goal=goal, intensity=intensity)
    try:
        profile = ProfileIn(**raw)
    except ValidationError as exc:
        errors = {str(e["loc"][0]): FIELD_HELP.get(str(e["loc"][0]), e["msg"]) for e in exc.errors()}
        return _form_page(request, raw, errors, status=422)
    member = services.create_or_replace(db, profile)
    return RedirectResponse(f"/plan/{member.handle}", status_code=303)


@router.get("/plan/{handle}", include_in_schema=False)
def plan_page(request: Request, handle: str, version: str = "auto", db: Session = Depends(get_db)):
    member = services.get_member(db, handle)
    if member is None or member.plan is None:
        return _message(request, "No plan found", f"There is no plan for “{handle}” yet. Build one to get started.", 404)
    plan = member.plan
    has_update = plan.updated_plan is not None
    if version not in ("original", "updated"):
        version = "updated" if has_update else "original"
    if version == "updated" and not has_update:
        version = "original"
    raw = plan.updated_plan if version == "updated" else plan.original_plan
    source = plan.updated_source if version == "updated" else plan.original_source
    days = json.loads(raw)
    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "member": member,
            "plan": plan,
            "days": days,
            "version": version,
            "has_update": has_update,
            "changes": json.loads(plan.change_summary) if plan.change_summary and version == "updated" else [],
            "source_label": SOURCE_LABEL.get(source, "Built-in planner"),
            "total_minutes": sum(d["minutes"] for d in days),
            "active_days": sum(1 for d in days if d["kind"] in ("train", "cardio")),
            "error": None,
        },
    )


@router.post("/plan/{handle}/feedback", include_in_schema=False)
def feedback_form(
    request: Request, handle: str, feedback: str = Form(""), db: Session = Depends(get_db)
):
    member = services.get_member(db, handle)
    if member is None or member.plan is None:
        return _message(request, "No plan found", "Build a plan before sending feedback.", 404)
    try:
        body = FeedbackIn(feedback=feedback)
    except ValidationError:
        return _message(request, "Feedback is too short", "Write at least a few words about what to change.", 422)
    services.apply_feedback(db, member, body)
    return RedirectResponse(f"/plan/{handle}?version=updated", status_code=303)


@router.get("/coach", include_in_schema=False)
def coach(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.created_at.desc()).all()
    rows = []
    for m in members:
        if m.plan is None:
            continue
        days = json.loads(m.plan.updated_plan or m.plan.original_plan)
        rows.append({"member": m, "plan": m.plan, "days": days, "revised": m.plan.updated_plan is not None})
    return templates.TemplateResponse(
        request,
        "coach.html",
        {"rows": rows, "revised_count": sum(1 for r in rows if r["revised"])},
    )


@router.post("/coach/{handle}/delete", include_in_schema=False)
def delete_member(handle: str, db: Session = Depends(get_db)):
    member = services.get_member(db, handle)
    if member:
        db.delete(member)
        db.commit()
    return RedirectResponse("/coach", status_code=303)


# ------------------------------ API ------------------------------
@router.get("/health", tags=["system"])
def health():
    return {"status": "ok", "gemini": gemini_enabled()}


@router.post("/api/plans", tags=["plans"], summary="Create (or replace) a member's 7-day plan")
def api_create(profile: ProfileIn, db: Session = Depends(get_db)):
    return services.plan_payload(services.create_or_replace(db, profile))


@router.get("/api/plans/{handle}", tags=["plans"], summary="Read a member's plans")
def api_read(handle: str, db: Session = Depends(get_db)):
    member = services.get_member(db, handle)
    if member is None or member.plan is None:
        raise HTTPException(404, "No plan for this username")
    return services.plan_payload(member)


@router.post("/api/plans/{handle}/feedback", tags=["plans"], summary="Revise a plan from feedback")
def api_feedback(handle: str, body: FeedbackIn, db: Session = Depends(get_db)):
    member = services.get_member(db, handle)
    if member is None or member.plan is None:
        raise HTTPException(404, "No plan for this username")
    services.apply_feedback(db, member, body)
    return services.plan_payload(member)


@router.delete("/api/plans/{handle}", tags=["plans"], summary="Delete a member and their plans")
def api_delete(handle: str, db: Session = Depends(get_db)):
    member = services.get_member(db, handle)
    if member is None:
        raise HTTPException(404, "No member with this username")
    db.delete(member)
    db.commit()
    return {"deleted": handle}
