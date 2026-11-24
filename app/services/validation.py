"""Server-side input validation (the Tkinter versions had none)."""
from datetime import date

from .programs import PROGRAMS, WORKOUT_TYPES


def _num(value, kind, lo, hi, label, errors, required=False):
    value = (value or "").strip()
    if value == "":
        if required:
            errors.append(f"{label} is required")
        return None
    try:
        number = kind(value)
    except ValueError:
        errors.append(f"{label} must be a number")
        return None
    if not lo <= number <= hi:
        errors.append(f"{label} must be between {lo} and {hi}")
        return None
    return number


def _date(value, label, errors, required=False):
    value = (value or "").strip()
    if not value:
        if required:
            errors.append(f"{label} is required")
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        errors.append(f"{label} must be YYYY-MM-DD")
        return None
    return value


def validate_client(form):
    errors = []
    name = (form.get("name") or "").strip()
    if not name:
        errors.append("Name is required")
    elif len(name) > 80:
        errors.append("Name must be at most 80 characters")
    program = form.get("program", "")
    if program not in PROGRAMS:
        errors.append("A valid programme is required")
    data = {
        "name": name,
        "program": program,
        "age": _num(form.get("age"), int, 10, 100, "Age", errors),
        "height": _num(form.get("height"), float, 100, 250, "Height (cm)", errors),
        "weight": _num(form.get("weight"), float, 20, 400, "Weight (kg)", errors),
        "target_weight": _num(form.get("target_weight"), float, 20, 400, "Target weight", errors),
        "target_adherence": _num(form.get("target_adherence"), int, 0, 100,
                                 "Target adherence", errors),
        "membership_expiry": _date(form.get("membership_expiry"), "Membership expiry", errors),
        "notes": (form.get("notes") or "").strip()[:500],
    }
    return data, errors


def validate_progress(form):
    errors = []
    adherence = _num(form.get("adherence"), int, 0, 100, "Adherence", errors, required=True)
    week = _date(form.get("week_start"), "Week start", errors) or date.today().isoformat()
    return {"adherence": adherence, "week_start": week}, errors


def validate_workout(form):
    errors = []
    w_type = form.get("workout_type", "")
    if w_type not in WORKOUT_TYPES:
        errors.append("A valid workout type is required")
    data = {
        "date": _date(form.get("date"), "Date", errors) or date.today().isoformat(),
        "workout_type": w_type,
        "duration_min": _num(form.get("duration_min"), int, 1, 600, "Duration", errors,
                             required=True),
        "notes": (form.get("notes") or "").strip()[:500],
    }
    exercises = []
    names = form.getlist("ex_name")
    for i, raw in enumerate(names):
        name = raw.strip()
        if not name:
            continue
        sets = _num(form.getlist("ex_sets")[i], int, 1, 50, "Sets", errors)
        reps = _num(form.getlist("ex_reps")[i], int, 1, 500, "Reps", errors)
        weight = _num(form.getlist("ex_weight")[i], float, 0, 1000, "Exercise weight", errors)
        exercises.append({"name": name[:80], "sets": sets, "reps": reps, "weight": weight})
    return data, exercises, errors


def validate_metrics(form):
    errors = []
    data = {
        "date": _date(form.get("date"), "Date", errors) or date.today().isoformat(),
        "weight": _num(form.get("weight"), float, 20, 400, "Weight (kg)", errors),
        "waist": _num(form.get("waist"), float, 30, 250, "Waist (cm)", errors),
        "bodyfat": _num(form.get("bodyfat"), float, 2, 70, "Body fat (%)", errors),
    }
    if not errors and all(data[k] is None for k in ("weight", "waist", "bodyfat")):
        errors.append("Enter at least one of weight, waist or body fat")
    return data, errors
