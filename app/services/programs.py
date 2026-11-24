"""Programme catalogue and business rules migrated from the Tkinter versions.

Calorie factors (22/35/26) come from v1.1; programme names and day-based
variants from v2.2.4; workout/diet text from v1.0; generator from v3.1.2.
"""
import random

FAT_LOSS_WORKOUT = (
    "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\n"
    "Wed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\n"
    "Fri: 30min Active Recovery"
)
FAT_LOSS_DIET = (
    "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\n"
    "D: Fish Curry + Millet Roti\nTarget: 2,000 kcal"
)

PROGRAMS = {
    "Fat Loss (FL) - 3 day": {
        "factor": 22, "color": "#e74c3c", "desc": "3-day full-body fat loss",
        "workout": FAT_LOSS_WORKOUT, "diet": FAT_LOSS_DIET, "focus": "Conditioning",
    },
    "Fat Loss (FL) - 5 day": {
        "factor": 24, "color": "#e74c3c", "desc": "5-day split, higher volume fat loss",
        "workout": FAT_LOSS_WORKOUT, "diet": FAT_LOSS_DIET, "focus": "Conditioning",
    },
    "Muscle Gain (MG) - PPL": {
        "factor": 35, "color": "#2ecc71", "desc": "Push/Pull/Legs hypertrophy",
        "workout": (
            "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\n"
            "Thu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10"
        ),
        "diet": (
            "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\n"
            "D: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal"
        ),
        "focus": "Hypertrophy",
    },
    "Beginner (BG)": {
        "factor": 26, "color": "#3498db", "desc": "3-day simple beginner full-body",
        "workout": (
            "Circuit Training: Air Squats, Ring Rows, Push-ups.\n"
            "Focus: Technique Mastery & Form (90% Threshold)"
        ),
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
        "focus": "Full Body",
    },
}

WORKOUT_TYPES = ["Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility"]

EXERCISE_POOL = {
    "Strength": ["Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row"],
    "Hypertrophy": ["Leg Press", "Incline Dumbbell Press", "Lat Pulldown",
                    "Lateral Raise", "Bicep Curl", "Tricep Extension"],
    "Conditioning": ["Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings"],
    "Full Body": ["Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press"],
}

LEVELS = {  # level: (sets range, reps range, days)
    "beginner": ((2, 3), (8, 12), 3),
    "intermediate": ((3, 4), (8, 15), 4),
    "advanced": ((4, 5), (6, 15), 5),
}
WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def calculate_calories(weight, program):
    """Estimated daily calories = weight (kg) x programme factor. None if unknown."""
    if not weight or weight <= 0 or program not in PROGRAMS:
        return None
    return int(weight * PROGRAMS[program]["factor"])


def calculate_bmi(height_cm, weight_kg):
    """Return (bmi, category, risk note) using the v2.2.4 thresholds."""
    if not height_cm or not weight_kg or height_cm <= 0 or weight_kg <= 0:
        return None
    bmi = round(weight_kg / ((height_cm / 100.0) ** 2), 1)
    if bmi < 18.5:
        return bmi, "Underweight", "Potential nutrient deficiency, low energy."
    if bmi < 25:
        return bmi, "Normal", "Low risk if active and strong."
    if bmi < 30:
        return bmi, "Overweight", "Moderate risk; focus on adherence and progressive activity."
    return bmi, "Obese", "Higher risk; prioritize fat loss, consistency, and supervision."


def generate_program(program, level, rng=None):
    """Random 'AI-style' weekly plan (v3.1.2 behaviour). Extension: seedable rng."""
    level = (level or "").lower()
    if level not in LEVELS or program not in PROGRAMS:
        raise ValueError("Invalid programme or experience level")
    rng = rng or random.Random()
    (s_lo, s_hi), (r_lo, r_hi), days = LEVELS[level]
    pool = EXERCISE_POOL[PROGRAMS[program]["focus"]]
    plan = []
    for day in WEEK_DAYS[:days]:
        for ex in rng.sample(pool, k=3 if days < 4 else 4):
            plan.append({"day": day, "exercise": ex,
                         "sets": rng.randint(s_lo, s_hi), "reps": rng.randint(r_lo, r_hi)})
    return plan
