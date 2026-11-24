"""Data-access layer: all SQL lives here and is fully parameterised."""
from .db import get_db
from .services.programs import calculate_calories

CLIENT_COLS = ("name", "age", "height", "weight", "program", "calories",
               "target_weight", "target_adherence", "membership_expiry", "notes")


def list_clients(query=""):
    db = get_db()
    if query:
        return db.execute("SELECT * FROM clients WHERE name LIKE ? ORDER BY name",
                          (f"%{query}%",)).fetchall()
    return db.execute("SELECT * FROM clients ORDER BY name").fetchall()


def get_client(client_id):
    return get_db().execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()


def save_client(data, client_id=None):
    """Insert or update (never INSERT OR REPLACE, which lost data in v2.x/v3.x)."""
    db = get_db()
    data = dict(data, calories=calculate_calories(data.get("weight"), data["program"]))
    values = [data.get(c) for c in CLIENT_COLS]
    if client_id is None:
        cur = db.execute(
            f"INSERT INTO clients ({', '.join(CLIENT_COLS)}) "
            f"VALUES ({', '.join('?' * len(CLIENT_COLS))})", values)
        client_id = cur.lastrowid
    else:
        sets = ", ".join(f"{c} = ?" for c in CLIENT_COLS)
        db.execute(f"UPDATE clients SET {sets} WHERE id = ?", values + [client_id])
    db.commit()
    return client_id


def delete_client(client_id):
    db = get_db()
    cur = db.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    db.commit()
    return cur.rowcount > 0


def upsert_progress(client_id, week_start, adherence):
    db = get_db()
    db.execute(
        "INSERT INTO progress (client_id, week_start, adherence) VALUES (?, ?, ?) "
        "ON CONFLICT(client_id, week_start) DO UPDATE SET adherence = excluded.adherence",
        (client_id, week_start, adherence))
    db.commit()


def list_progress(client_id):
    return get_db().execute(
        "SELECT week_start, adherence FROM progress WHERE client_id = ? ORDER BY week_start",
        (client_id,)).fetchall()


def add_workout(client_id, data, exercises):
    db = get_db()
    cur = db.execute(
        "INSERT INTO workouts (client_id, date, workout_type, duration_min, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (client_id, data["date"], data["workout_type"], data["duration_min"], data["notes"]))
    workout_id = cur.lastrowid
    for ex in exercises:
        db.execute("INSERT INTO exercises (workout_id, name, sets, reps, weight) "
                   "VALUES (?, ?, ?, ?, ?)",
                   (workout_id, ex["name"], ex["sets"], ex["reps"], ex["weight"]))
    db.commit()
    return workout_id


def list_workouts(client_id):
    db = get_db()
    workouts = db.execute(
        "SELECT * FROM workouts WHERE client_id = ? ORDER BY date DESC, id DESC",
        (client_id,)).fetchall()
    result = []
    for w in workouts:
        exs = db.execute("SELECT * FROM exercises WHERE workout_id = ? ORDER BY id",
                         (w["id"],)).fetchall()
        result.append({"workout": w, "exercises": exs})
    return result


def add_metrics(client_id, data):
    db = get_db()
    db.execute("INSERT INTO metrics (client_id, date, weight, waist, bodyfat) "
               "VALUES (?, ?, ?, ?, ?)",
               (client_id, data["date"], data["weight"], data["waist"], data["bodyfat"]))
    if data["weight"]:  # v2.2.4: logging weight refreshes the client's current weight
        client = get_client(client_id)
        db.execute("UPDATE clients SET weight = ?, calories = ? WHERE id = ?",
                   (data["weight"], calculate_calories(data["weight"], client["program"]),
                    client_id))
    db.commit()


def list_metrics(client_id):
    return get_db().execute(
        "SELECT * FROM metrics WHERE client_id = ? ORDER BY date, id", (client_id,)).fetchall()


def dashboard_stats():
    db = get_db()
    one = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    return {
        "clients": one("SELECT COUNT(*) FROM clients"),
        "workouts": one("SELECT COUNT(*) FROM workouts"),
        "avg_adherence": round(one("SELECT COALESCE(AVG(adherence), 0) FROM progress"), 1),
        "by_program": db.execute(
            "SELECT program, COUNT(*) AS n FROM clients GROUP BY program ORDER BY n DESC"
        ).fetchall(),
    }


def get_user(username):
    return get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def get_user_by_id(user_id):
    return get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(username, password_hash, role):
    db = get_db()
    db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
               (username, password_hash, role))
    db.commit()
