from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    handle: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(40))
    intensity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    plan: Mapped["WeekPlan"] = relationship(
        back_populates="member", uselist=False, cascade="all, delete-orphan"
    )


class WeekPlan(Base):
    __tablename__ = "week_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), unique=True)
    original_plan: Mapped[str] = mapped_column(Text)  # JSON list of 7 days
    original_source: Mapped[str] = mapped_column(String(20), default="builtin")
    nutrition_tip: Mapped[str] = mapped_column(Text)
    tip_source: Mapped[str] = mapped_column(String(20), default="builtin")
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    member: Mapped[Member] = relationship(back_populates="plan")
