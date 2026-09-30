"""Revises a plan from free-text feedback. Gemini first, keyword rules as the fallback."""
import copy
import json
import re

from . import ai, config
from .planner import SCHEMA_HINT, normalize_plan, phase_defaults


def _has(text: str, *words: str) -> bool:
    return any(w in text for w in words)


def revise_builtin(days: list[dict], feedback: str) -> tuple[list[dict], list[str]]:
    text = feedback.lower()
    days = copy.deepcopy(days)
    changes: list[str] = []

    def active():
        return [d for d in days if d["kind"] in ("train", "cardio")]

    if _has(text, "easier", "too hard", "too tough", "beginner", "lighter", "gentle"):
        for d in active():
            if len(d["main"]) > 2:
                d["main"].pop()
            d["minutes"] = max(20, d["minutes"] - 10)
        changes.append("Made sessions easier: one fewer exercise and 10 fewer minutes on training days.")

    if _has(text, "harder", "more intense", "intensity", "challeng", "tougher"):
        for d in active():
            d["main"].append({"name": "Finisher: fast squats, then push-ups", "dose": "3 rounds of 40 sec on, 20 sec off"})
            d["minutes"] += 10
        changes.append("Added a finisher round to every training and cardio day.")

    if _has(text, "shorter", "less time", "quick", "short on time", "busy", "20 min", "30 min"):
        for d in active():
            d["minutes"] = max(15, int(round(d["minutes"] * 0.7 / 5.0) * 5))
            d["main"] = d["main"][:3]
        changes.append("Shortened sessions to roughly 70% of their length, keeping the top three exercises.")

    if "cardio" in text:
        added = 0
        for d in days:
            if d["kind"] == "train" and added < 3:
                d["main"].append({"name": "Cardio finisher: brisk incline walk, bike or rower", "dose": "10 min"})
                d["minutes"] += 10
                added += 1
        if added:
            changes.append(f"Added a 10-minute cardio finisher to {added} strength days.")

    if _has(text, "rest day", "more rest", "extra rest", "recover", "sore", "tired", "exhausted", "fatigue"):
        n = 2 if re.search(r"\b(two|2)\b", text) else 1
        converted = 0
        for d in reversed(days[:6]):
            if d["kind"] == "train" and converted < n and len([x for x in days if x["kind"] == "train"]) > 2:
                d.update(
                    focus="Extra recovery",
                    kind="recovery",
                    minutes=25,
                    main=[{"name": "Easy walk", "dose": "20 min"}, {"name": "Full-body mobility flow", "dose": "8 min"}],
                    **phase_defaults("recovery"),
                )
                converted += 1
        if converted:
            changes.append(f"Swapped {converted} strength day{'s' if converted > 1 else ''} for recovery.")

    if _has(text, "core", "abs", "abdominal"):
        added = 0
        for d in days:
            if d["kind"] == "train" and added < 3 and not any("plank" in m["name"].lower() for m in d["main"]):
                d["main"].append({"name": "Plank", "dose": "3 x 40 sec"})
                added += 1
        if added:
            changes.append(f"Added planks to {added} training days for extra core work.")

    if _has(text, "stretch", "mobility", "flexib", "stiff"):
        for d in active():
            d["cooldown"].append("Extra mobility: 8 min of hip, hamstring and shoulder stretches")
        changes.append("Added an 8-minute mobility block to every cool-down.")

    return days, changes


def revise_plan(profile: dict, days: list[dict], feedback: str) -> tuple[list[dict], list[str], str]:
    """Returns (days, changes, source)."""
    prompt = (
        "You are a careful fitness coach. Here is a member's current 7-day plan as JSON:\n"
        f"{json.dumps(days)}\n\n"
        f"Member: age {profile['age']}, weight {profile['weight']} kg, goal {profile['goal']}, "
        f"intensity {profile['intensity']}.\nTheir feedback: \"{feedback}\"\n\n"
        "Revise the plan to reflect the feedback while keeping it safe and balanced (keep 7 days, "
        "at least one rest day). Reply with JSON only: "
        '{"days": [...same shape as the input...], "changes": ["short sentence per change"]}. '
        f"Day shape: {SCHEMA_HINT}"
    )
    data = ai.ask_json(prompt, config.FITNESS_MODEL)
    if isinstance(data, dict):
        try:
            new_days = normalize_plan(data)
            changes = [str(c)[:200] for c in (data.get("changes") or [])][:6]
            return new_days, changes or ["Plan updated from your feedback."], "gemini"
        except ValueError:
            pass
    new_days, changes = revise_builtin(days, feedback)
    return new_days, changes, "builtin"
