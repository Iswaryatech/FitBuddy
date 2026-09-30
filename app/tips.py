"""Nutrition and recovery tip. Gemini first, built-in text as the fallback."""
from . import ai, config

PROTEIN_PER_KG = {
    "Weight loss": 1.6,
    "Muscle gain": 1.8,
    "Strength": 1.8,
    "Cardio fitness": 1.4,
    "General wellness": 1.2,
    "Flexibility": 1.2,
}

FOCUS = {
    "Weight loss": "Build each plate around vegetables and lean protein first, and keep a steady eating rhythm so evenings don't turn into a catch-up meal.",
    "Muscle gain": "Spread protein across three or four meals and add a carbohydrate-rich snack near your hardest sessions.",
    "Strength": "Eat a proper meal two to three hours before lifting, and pair protein with carbohydrates afterwards.",
    "Cardio fitness": "Carbohydrates fuel your interval and long days, so eat something light before those and refill afterwards.",
    "General wellness": "Aim for colour and variety on the plate, and treat sleep as part of the plan.",
    "Flexibility": "Stay well hydrated, since tissues stretch more comfortably when you are, and add a short evening wind-down.",
}


def builtin_tip(profile: dict) -> str:
    grams = int(round(profile["weight"] * PROTEIN_PER_KG[profile["goal"]] / 5.0) * 5)
    litres = round(profile["weight"] * 0.035, 1)
    return (
        f"A good starting point is about {grams} g of protein and {litres} L of water a day. "
        f"{FOCUS[profile['goal']]} On rest days, sleep 7 to 9 hours and keep moving gently."
    )


def create_tip(profile: dict) -> tuple[str, str]:
    """Returns (tip, source)."""
    prompt = (
        "Write one practical nutrition and recovery tip in under 70 words, plain text, no lists, "
        f"for a {profile['age']}-year-old weighing {profile['weight']} kg whose goal is "
        f"{profile['goal']} at {profile['intensity']} intensity. Keep it general wellness advice."
    )
    text = ai.ask_text(prompt, config.TIP_MODEL)
    if text:
        return text.strip(), "gemini"
    return builtin_tip(profile), "builtin"
