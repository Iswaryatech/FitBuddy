from typing import Literal

from pydantic import BaseModel, Field, field_validator

GOALS = [
    "Weight loss",
    "Muscle gain",
    "General wellness",
    "Strength",
    "Flexibility",
    "Cardio fitness",
]
INTENSITIES = ["Low", "Medium", "High"]

Goal = Literal[
    "Weight loss", "Muscle gain", "General wellness", "Strength", "Flexibility", "Cardio fitness"
]
Intensity = Literal["Low", "Medium", "High"]


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    handle: str = Field(pattern=r"^[A-Za-z0-9_-]{2,40}$", description="Unique username")
    age: int = Field(ge=14, le=90)
    weight: float = Field(ge=25, le=300, description="Body weight in kg")
    goal: Goal
    intensity: Intensity

    @field_validator("name", "handle", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


class FeedbackIn(BaseModel):
    feedback: str = Field(min_length=3, max_length=600)

    @field_validator("feedback", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


FIELD_HELP = {
    "name": "Enter your name.",
    "handle": "Use 2 to 40 letters, numbers, dashes or underscores.",
    "age": "Age should be between 14 and 90.",
    "weight": "Weight should be between 25 and 300 kg.",
    "goal": "Pick a goal.",
    "intensity": "Pick how hard you want to train.",
}
