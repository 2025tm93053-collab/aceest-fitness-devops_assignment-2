import random
from datetime import date

import pytest

from app.services.charts import line_chart
from app.services.membership import membership_status
from app.services.programs import calculate_bmi, calculate_calories, generate_program


@pytest.mark.parametrize("weight,program,expected", [
    (80, "Fat Loss (FL) - 3 day", 1760), (80, "Fat Loss (FL) - 5 day", 1920),
    (80, "Muscle Gain (MG) - PPL", 2800), (80, "Beginner (BG)", 2080),
    (0, "Beginner (BG)", None), (None, "Beginner (BG)", None), (80, "Unknown", None)])
def test_calories(weight, program, expected):
    assert calculate_calories(weight, program) == expected


@pytest.mark.parametrize("h,w,cat", [
    (180, 55, "Underweight"), (175, 70, "Normal"),
    (170, 80, "Overweight"), (165, 100, "Obese")])
def test_bmi_categories(h, w, cat):
    assert calculate_bmi(h, w)[1] == cat


def test_bmi_missing_data():
    assert calculate_bmi(0, 70) is None and calculate_bmi(170, None) is None


def test_generate_program_shape_and_determinism():
    a = generate_program("Muscle Gain (MG) - PPL", "advanced", random.Random(1))
    b = generate_program("Muscle Gain (MG) - PPL", "advanced", random.Random(1))
    assert a == b and len({p["day"] for p in a}) == 5 and len(a) == 20
    assert all(4 <= p["sets"] <= 5 and 6 <= p["reps"] <= 15 for p in a)


def test_generate_program_beginner_three_days():
    plan = generate_program("Beginner (BG)", "Beginner")
    assert len({p["day"] for p in plan}) == 3 and len(plan) == 9


def test_generate_program_invalid():
    with pytest.raises(ValueError):
        generate_program("Beginner (BG)", "expert")
    with pytest.raises(ValueError):
        generate_program("Nope", "beginner")


def test_membership_status():
    today = date(2026, 6, 1)
    assert membership_status(None) == "No membership"
    assert membership_status("2026-05-31", today) == "Expired"
    assert membership_status("2026-06-10", today) == "Expiring soon"
    assert membership_status("2026-12-01", today) == "Active"


def test_chart_empty_and_single_point():
    assert str(line_chart([], [])) == ""
    assert "<circle" in str(line_chart(["w1"], [50]))


def test_chart_escapes_labels():
    assert "<script>" not in str(line_chart(["<script>"], [1]))
