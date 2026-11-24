from app import repository as repo


def test_progress_saved_and_charted(make_client, admin):
    cid = make_client()
    r = admin.post(f"/clients/{cid}/progress", data={"adherence": "80", "week_start": "2026-01-05"})
    assert r.status_code == 302
    admin.post(f"/clients/{cid}/progress", data={"adherence": "90", "week_start": "2026-01-12"})
    assert b"<svg" in admin.get(f"/clients/{cid}").data


def test_progress_same_week_updates(make_client, admin, app):
    cid = make_client()
    for val in ("50", "70"):
        admin.post(f"/clients/{cid}/progress", data={"adherence": val, "week_start": "2026-01-05"})
    with app.app_context():
        rows = repo.list_progress(cid)
    assert len(rows) == 1 and rows[0]["adherence"] == 70


def test_progress_invalid(make_client, admin, app):
    cid = make_client()
    for bad in ("", "abc", "101", "-1"):
        admin.post(f"/clients/{cid}/progress", data={"adherence": bad})
    with app.app_context():
        assert repo.list_progress(cid) == []


def test_progress_unknown_client(admin):
    assert admin.post("/clients/999/progress", data={"adherence": "5"}).status_code == 404


def test_workout_with_exercises(make_client, admin, app):
    cid = make_client()
    r = admin.post(f"/clients/{cid}/workouts", data={
        "date": "2026-02-01", "workout_type": "Strength", "duration_min": "45",
        "ex_name": ["Squat", "", "Bench Press"], "ex_sets": ["5", "", "3"],
        "ex_reps": ["5", "", "8"], "ex_weight": ["100", "", "60"]})
    assert r.status_code == 302
    with app.app_context():
        items = repo.list_workouts(cid)
    assert len(items) == 1
    assert [e["name"] for e in items[0]["exercises"]] == ["Squat", "Bench Press"]
    assert items[0]["exercises"][0]["weight"] == 100
    assert b"Squat" in admin.get(f"/clients/{cid}").data


def test_workout_without_exercise(make_client, admin, app):
    cid = make_client()
    admin.post(f"/clients/{cid}/workouts", data={"workout_type": "Mobility", "duration_min": "20"})
    with app.app_context():
        assert repo.list_workouts(cid)[0]["exercises"] == []


def test_workout_validation(make_client, admin, app):
    cid = make_client()
    bad = [{"workout_type": "Nope", "duration_min": "30"},
           {"workout_type": "Strength", "duration_min": "0"},
           {"workout_type": "Strength", "duration_min": "x"},
           {"workout_type": "Strength", "duration_min": "30", "date": "bad"},
           {"workout_type": "Strength", "duration_min": "30", "ex_name": "Sq", "ex_sets": "0",
            "ex_reps": "5", "ex_weight": "1"}]
    for data in bad:
        admin.post(f"/clients/{cid}/workouts", data=data)
    with app.app_context():
        assert repo.list_workouts(cid) == []


def test_metrics_update_client_weight_and_calories(make_client, admin, app):
    cid = make_client()
    r = admin.post(f"/clients/{cid}/metrics", data={
        "date": "2026-03-01", "weight": "75", "waist": "85", "bodyfat": "20"})
    assert r.status_code == 302
    with app.app_context():
        c = repo.get_client(cid)
        assert c["weight"] == 75 and c["calories"] == 1650
        assert len(repo.list_metrics(cid)) == 1


def test_metrics_waist_only_keeps_weight(make_client, admin, app):
    cid = make_client()
    admin.post(f"/clients/{cid}/metrics", data={"waist": "90"})
    with app.app_context():
        assert repo.get_client(cid)["weight"] == 80


def test_metrics_requires_a_value(make_client, admin, app):
    cid = make_client()
    admin.post(f"/clients/{cid}/metrics", data={"date": "2026-03-01"})
    with app.app_context():
        assert repo.list_metrics(cid) == []


def test_metrics_range_validation(make_client, admin, app):
    cid = make_client()
    admin.post(f"/clients/{cid}/metrics", data={"bodyfat": "99"})
    with app.app_context():
        assert repo.list_metrics(cid) == []


def test_weight_chart_rendered(make_client, admin):
    cid = make_client()
    admin.post(f"/clients/{cid}/metrics", data={"date": "2026-03-01", "weight": "79"})
    admin.post(f"/clients/{cid}/metrics", data={"date": "2026-03-08", "weight": "78"})
    assert b"Weight trend" in admin.get(f"/clients/{cid}").data


def test_cascade_delete_removes_children(make_client, admin, app):
    cid = make_client()
    admin.post(f"/clients/{cid}/progress", data={"adherence": "50"})
    admin.post(f"/clients/{cid}/workouts", data={
        "workout_type": "Mixed", "duration_min": "30", "ex_name": "Run", "ex_sets": "1",
        "ex_reps": "1", "ex_weight": "0"})
    admin.post(f"/clients/{cid}/metrics", data={"weight": "70"})
    admin.post(f"/clients/{cid}/delete")
    with app.app_context():
        from app.db import get_db
        db = get_db()
        for t in ("progress", "workouts", "exercises", "metrics"):
            assert db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] == 0
