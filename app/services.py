import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from . import planner, revise, tips
from .models import Member, WeekPlan
from .schemas import FeedbackIn, ProfileIn


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_member(db: Session, handle: str) -> Member | None:
    return db.query(Member).filter(Member.handle == handle).first()


def create_or_replace(db: Session, profile: ProfileIn) -> Member:
    """Saves the member and generates a fresh plan. Re-using a username replaces the old plan."""
    data = profile.model_dump()
    days, plan_source = planner.create_plan(data)
    tip, tip_source = tips.create_tip(data)

    member = get_member(db, profile.handle)
    if member is None:
        member = Member(**data)
        db.add(member)
        db.flush()
    else:
        for key, value in data.items():
            setattr(member, key, value)
        if member.plan:
            db.delete(member.plan)
            db.flush()

    db.add(
        WeekPlan(
            member_id=member.id,
            original_plan=planner.dump(days),
            original_source=plan_source,
            nutrition_tip=tip,
            tip_source=tip_source,
        )
    )
    db.commit()
    db.refresh(member)
    return member


def apply_feedback(db: Session, member: Member, body: FeedbackIn) -> WeekPlan:
    """Revises the plan. The original is never touched."""
    plan = member.plan
    profile = {
        "age": member.age,
        "weight": member.weight,
        "goal": member.goal,
        "intensity": member.intensity,
    }
    # Always revise the original so repeated feedback replaces, not stacks, changes.
    base = json.loads(plan.original_plan)
    days, changes, source = revise.revise_plan(profile, base, body.feedback)
    plan.feedback = body.feedback
    plan.updated_plan = planner.dump(days)
    plan.updated_source = source
    plan.change_summary = json.dumps(changes, ensure_ascii=False)
    plan.updated_at = _now()
    db.commit()
    return plan


def plan_payload(member: Member) -> dict:
    plan = member.plan
    return {
        "member": {
            "handle": member.handle,
            "name": member.name,
            "age": member.age,
            "weight": member.weight,
            "goal": member.goal,
            "intensity": member.intensity,
        },
        "original_plan": json.loads(plan.original_plan),
        "original_source": plan.original_source,
        "nutrition_tip": plan.nutrition_tip,
        "feedback": plan.feedback,
        "updated_plan": json.loads(plan.updated_plan) if plan.updated_plan else None,
        "updated_source": plan.updated_source,
        "changes": json.loads(plan.change_summary) if plan.change_summary else [],
    }
