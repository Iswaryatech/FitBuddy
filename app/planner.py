"""Creates the 7-day plan. Gemini first, built-in planner as the fallback."""
import json

from . import ai, config

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
FULL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
KINDS = ("train", "cardio", "recovery", "rest")
KIND_LABEL = {"train": "Strength", "cardio": "Cardio", "recovery": "Recovery", "rest": "Rest"}

SCHEMES = {
    "reps": {"Low": "2 x 10", "Medium": "3 x 12", "High": "4 x 15"},
    "heavy": {"Low": "3 x 6", "Medium": "4 x 6", "High": "5 x 5"},
    "mod": {"Low": "3 x 8", "Medium": "3 x 10", "High": "4 x 10"},
    "hold": {"Low": "2 x 20 sec", "Medium": "3 x 30 sec", "High": "3 x 45 sec"},
    "cardio": {"Low": "15 min", "Medium": "25 min", "High": "35 min"},
    "aerobic": {"Low": "20 min", "Medium": "30 min", "High": "40 min"},
    "long": {"Low": "35 min", "Medium": "50 min", "High": "70 min"},
    "easy": {"Low": "10 min", "Medium": "15 min", "High": "20 min"},
    "flow": {"Low": "5 min", "Medium": "8 min", "High": "10 min"},
    "interval": {
        "Low": "6 x 30 sec hard, 90 sec easy",
        "Medium": "8 x 40 sec hard, 80 sec easy",
        "High": "10 x 45 sec hard, 75 sec easy",
    },
}

MINUTES = {
    "train": {"Low": 30, "Medium": 45, "High": 60},
    "cardio": {"Low": 30, "Medium": 45, "High": 60},
    "recovery": {"Low": 20, "Medium": 25, "High": 30},
    "rest": {"Low": 0, "Medium": 0, "High": 0},
}

WARMUP = {
    "train": [
        "3 min brisk walk or march on the spot",
        "Arm circles and hip circles, 10 each way",
        "One light practice set of your first exercise",
    ],
    "cardio": [
        "5 min at a very easy pace",
        "Leg swings, 10 per side",
        "Two 20-second pickups, then walk it off",
    ],
    "recovery": ["2 min of slow breathing", "Gentle neck and shoulder rolls"],
    "rest": [],
}
COOLDOWN = {
    "train": [
        "3 min slow walk",
        "Quad, hamstring and chest stretches, 30 sec each",
        "Five slow breaths",
    ],
    "cardio": ["5 min easy walk", "Calf and hip flexor stretch, 30 sec each"],
    "recovery": ["Two minutes of slow breathing"],
    "rest": [],
}
RECOVERY = {
    "train": "Eat a protein-rich meal within two hours and stretch anything that feels tight.",
    "cardio": "Refill fluids and rest your legs. A short walk later in the day helps.",
    "recovery": "Keep it easy. If something feels sore, ease off instead of pushing through.",
    "rest": "Full rest today. Aim for 7 to 9 hours of sleep to lock in the week's work.",
}

_SQUAT = ("Bodyweight or goblet squat", "reps")
_PUSH = ("Push-up (knees down if needed)", "reps")
_ROW = ("Bent-over dumbbell or backpack row", "reps")
_PLANK = ("Plank", "hold")
_WALK = ("Easy walk", "easy")
_FLOW = ("Full-body mobility flow", "flow")
_REST = ("Optional easy stroll", "easy")

PATTERNS = {
    "Weight loss": [
        ("Full-body circuit", "train", [_SQUAT, _PUSH, _ROW, _PLANK]),
        ("Steady cardio", "cardio", [("Brisk walk, jog or cycle at a talking pace", "cardio"), ("High knees, easy pace", "hold")]),
        ("Lower body and core", "train", [("Chair or goblet squat", "reps"), ("Reverse lunge", "reps"), ("Glute bridge", "reps"), ("Dead bug", "reps")]),
        ("Active recovery", "recovery", [_WALK, _FLOW]),
        ("Interval day", "cardio", [("Intervals: jog, cycle or stair climb", "interval"), ("Mountain climber", "hold"), ("Easy cool-down walk", "easy")]),
        ("Upper body and core", "train", [("Incline or standard push-up", "reps"), ("Dumbbell shoulder press", "reps"), ("Superman hold", "hold"), ("Bicycle crunch", "reps")]),
        ("Rest day", "rest", [_REST]),
    ],
    "Muscle gain": [
        ("Push", "train", [("Push-up or bench press", "heavy"), ("Dumbbell shoulder press", "reps"), ("Triceps dip on a chair", "reps"), ("Lateral raise", "reps")]),
        ("Pull", "train", [("Bent-over row", "heavy"), ("Band or cable pull-down", "reps"), ("Biceps curl", "reps"), ("Rear-delt fly", "reps")]),
        ("Legs", "train", [("Back or goblet squat", "heavy"), ("Romanian deadlift", "reps"), ("Walking lunge", "reps"), ("Calf raise", "reps")]),
        ("Active recovery", "recovery", [_WALK, _FLOW]),
        ("Upper body", "train", [("Incline press or push-up variation", "reps"), ("Pull-up or assisted row", "reps"), ("Arnold press", "reps"), ("Hammer curl", "reps")]),
        ("Lower body and core", "train", [("Split squat", "reps"), ("Hip thrust", "heavy"), ("Step-up", "reps"), ("Hanging knee raise or plank", "hold")]),
        ("Rest day", "rest", [_REST]),
    ],
    "General wellness": [
        ("Full-body basics", "train", [_SQUAT, _PUSH, _ROW, _PLANK]),
        ("Easy cardio", "cardio", [("Brisk walk, cycle or swim", "cardio"), ("Arm circles and shoulder rolls", "flow")]),
        ("Mobility and balance", "recovery", [("Single-leg balance", "hold"), ("Cat-cow and thread the needle", "flow"), _WALK]),
        ("Full-body strength", "train", [("Goblet squat", "reps"), ("Overhead press", "reps"), ("Glute bridge", "reps"), ("Bird dog", "reps")]),
        ("Fun cardio", "cardio", [("Dance, hike or a sport you enjoy", "cardio"), ("Jumping jack or step jack", "hold")]),
        ("Outdoor movement", "recovery", [("Long relaxed walk or gentle bike ride", "easy"), ("Stretch flow", "flow")]),
        ("Rest day", "rest", [_REST]),
    ],
    "Strength": [
        ("Squat day", "train", [("Back or goblet squat", "heavy"), ("Romanian deadlift", "reps"), ("Split squat", "reps"), _PLANK]),
        ("Press day", "train", [("Bench or floor press", "heavy"), ("Overhead press", "reps"), ("Triceps extension", "reps"), ("Face pull or band pull-apart", "reps")]),
        ("Recovery", "recovery", [_WALK, _FLOW]),
        ("Hinge day", "train", [("Deadlift or kettlebell deadlift", "heavy"), ("Hip thrust", "reps"), ("Bent-over row", "reps"), ("Farmer carry", "hold")]),
        ("Pull day", "train", [("Pull-up or assisted pull-up", "heavy"), ("One-arm dumbbell row", "reps"), ("Biceps curl", "reps"), ("Hollow hold", "hold")]),
        ("Full-body power", "train", [("Kettlebell swing", "reps"), ("Push press", "reps"), ("Box or step jump", "reps"), ("Side plank", "hold")]),
        ("Rest day", "rest", [_REST]),
    ],
    "Flexibility": [
        ("Hips", "train", [("90/90 hip switch", "reps"), ("Pigeon pose", "hold"), ("Low lunge with reach", "hold"), ("Cossack squat", "reps")]),
        ("Spine and core", "train", [("Cat-cow", "flow"), ("Thread the needle", "reps"), ("Bird dog", "reps"), ("Cobra to child's pose", "reps")]),
        ("Shoulders and upper back", "train", [("Wall angels", "reps"), ("Doorway chest stretch", "hold"), ("Puppy pose", "hold"), ("Band shoulder pass-through", "reps")]),
        ("Easy recovery", "recovery", [_WALK, ("Foam roll or self-massage", "flow")]),
        ("Legs and hamstrings", "train", [("Standing forward fold", "hold"), ("Seated hamstring reach", "hold"), ("Couch stretch", "hold"), ("Deep squat hold", "hold")]),
        ("Full-body flow", "train", [("Sun salutation flow", "flow"), ("World's greatest stretch", "reps"), ("Happy baby pose", "hold")]),
        ("Rest day", "rest", [_REST]),
    ],
    "Cardio fitness": [
        ("Easy aerobic base", "cardio", [("Jog, cycle or row at a conversational pace", "aerobic"), ("Easy walk to cool down", "easy")]),
        ("Intervals", "cardio", [("Intervals: run, cycle or row", "interval"), ("Easy spin or jog", "easy")]),
        ("Strength support", "train", [_SQUAT, ("Reverse lunge", "reps"), ("Glute bridge", "reps"), _PLANK]),
        ("Tempo effort", "cardio", [("Comfortably hard tempo effort", "aerobic"), ("High knees", "hold")]),
        ("Recovery", "recovery", [_WALK, _FLOW]),
        ("Long steady session", "cardio", [("Long steady ride, run or hike", "long"), ("Easy walk to cool down", "easy")]),
        ("Rest day", "rest", [_REST]),
    ],
}

LOW_IMPACT = {
    "High knees": "Marching in place",
    "Mountain climber": "Slow incline mountain climber",
    "Jumping jack or step jack": "Step jack",
    "Box or step jump": "Step-up with a knee drive",
}


def phase_defaults(kind: str) -> dict:
    return {
        "warmup": list(WARMUP[kind]),
        "cooldown": list(COOLDOWN[kind]),
        "recovery": RECOVERY[kind],
    }


def builtin_plan(profile: dict) -> list[dict]:
    goal, level = profile["goal"], profile["intensity"]
    gentle = profile["age"] >= 50 or profile["weight"] >= 110
    days = []
    for i, (focus, kind, exercises) in enumerate(PATTERNS[goal]):
        main = []
        for name, scheme in exercises:
            if scheme == "reps" and goal in ("Strength", "Muscle gain"):
                scheme = "mod"
            if gentle:
                name = LOW_IMPACT.get(name, name)
            main.append({"name": name, "dose": SCHEMES[scheme][level]})
        days.append(
            {
                "day": DAYS[i],
                "focus": focus,
                "kind": kind,
                "minutes": MINUTES[kind][level],
                "main": main,
                **phase_defaults(kind),
            }
        )
    return days


def normalize_plan(data) -> list[dict]:
    """Validate and clean a plan (from Gemini). Raises ValueError if unusable."""
    days = data.get("days") if isinstance(data, dict) else data
    if not isinstance(days, list) or len(days) != 7:
        raise ValueError("plan must contain exactly 7 days")
    clean = []
    for i, d in enumerate(days):
        if not isinstance(d, dict):
            raise ValueError("bad day entry")
        kind = d.get("kind") if d.get("kind") in KINDS else "train"
        main = []
        for item in d.get("main") or []:
            if isinstance(item, dict) and item.get("name"):
                main.append({"name": str(item["name"])[:120], "dose": str(item.get("dose", ""))[:80]})
            elif isinstance(item, str):
                main.append({"name": item[:120], "dose": ""})
        if kind != "rest" and not main:
            raise ValueError("training day without exercises")
        try:
            minutes = max(0, min(150, int(d.get("minutes", 0))))
        except (TypeError, ValueError):
            minutes = 0
        defaults = phase_defaults(kind)
        clean.append(
            {
                "day": DAYS[i],
                "focus": str(d.get("focus") or "Session")[:60],
                "kind": kind,
                "minutes": 0 if kind == "rest" else minutes,
                "main": main,
                "warmup": [str(x)[:140] for x in d.get("warmup") or defaults["warmup"]][:6],
                "cooldown": [str(x)[:140] for x in d.get("cooldown") or defaults["cooldown"]][:6],
                "recovery": str(d.get("recovery") or defaults["recovery"])[:220],
            }
        )
    return clean


SCHEMA_HINT = (
    '{"days":[{"day":"Mon","focus":"Legs","kind":"train|cardio|recovery|rest","minutes":45,'
    '"warmup":["..."],"main":[{"name":"Goblet squat","dose":"3 x 12"}],'
    '"cooldown":["..."],"recovery":"one sentence"}]}'
)


def create_plan(profile: dict) -> tuple[list[dict], str]:
    """Returns (days, source) where source is 'gemini' or 'builtin'."""
    prompt = (
        "You are a careful, encouraging fitness coach. Create a 7-day workout plan "
        f"(Mon to Sun) for {profile['name']}, age {profile['age']}, weight {profile['weight']} kg. "
        f"Goal: {profile['goal']}. Intensity: {profile['intensity']}. "
        "Include at least one rest day and one recovery day, keep exercises equipment-light, "
        "and prefer low-impact options for older or heavier people. "
        f"Reply with JSON only, in exactly this shape: {SCHEMA_HINT}"
    )
    data = ai.ask_json(prompt, config.FITNESS_MODEL)
    if data is not None:
        try:
            return normalize_plan(data), "gemini"
        except ValueError:
            pass
    return builtin_plan(profile), "builtin"


def dump(days: list[dict]) -> str:
    return json.dumps(days, ensure_ascii=False)
