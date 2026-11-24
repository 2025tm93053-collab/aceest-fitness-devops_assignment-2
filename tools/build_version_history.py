"""Derive the v1.0.0 / v2.0.0 snapshots from the finished (v3.0.0) source tree.

Usage:  python tools/build_version_history.py <v3_source_dir> <output_dir>

Honest provenance note: the application was developed and validated as a whole,
then split into milestones by *removing* later features.  Every snapshot is a
working application with its own passing test-suite (run before it is committed).
    v1.0.0  core: clients, programmes, calorie estimate, dashboard, /health
    v2.0.0  + weekly progress, workouts/exercises, body metrics, BMI, SVG charts
    v3.0.0  + login, roles, CSRF, CSV/PDF reports, programme generator, shadow mode
"""
import ast
import re
import shutil
import sys
from pathlib import Path

COPY = ["app", "tests", "wsgi.py", "requirements.txt", "requirements-dev.txt",
        "pytest.ini", ".flake8", ".gitignore"]


def drop_defs(src, names):
    """Remove top-level functions/classes/assignments by name (with decorators)."""
    lines = src.splitlines(keepends=True)
    spans = []
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            continue
        if name in names:
            first = node.decorator_list[0].lineno if getattr(node, "decorator_list", None) \
                else node.lineno
            spans.append((first - 1, node.end_lineno))
    for a, b in sorted(spans, reverse=True):
        del lines[a:b]
    return re.sub(r"\n{4,}", "\n\n\n", "".join(lines)).rstrip() + "\n"


def sub(path, old, new, count=1):
    text = path.read_text()
    if old not in text:
        raise SystemExit(f"pattern not found in {path}: {old[:50]!r}")
    path.write_text(text.replace(old, new, count))


def rx(path, pattern, repl="", flags=0):
    text = path.read_text()
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n == 0:
        raise SystemExit(f"regex not found in {path}: {pattern[:50]!r}")
    path.write_text(new)


def edit(path, fn):
    path.write_text(fn(path.read_text()))


INIT_NOAUTH = '''"""ACEest Fitness & Gym - Flask application factory."""
from flask import Flask, render_template

from .config import load_config
from .db import close_db, init_db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    @app.context_processor
    def inject_meta():
        return {"app_version": app.config["APP_VERSION"],
                "deploy_color": app.config["DEPLOY_COLOR"],
                "variant": app.config["VARIANT"]}

    from .blueprints import clients, system%(extra_import)s
    for module in (system, clients%(extra_mod)s):
        app.register_blueprint(module.bp)

    @app.errorhandler(404)
    @app.errorhandler(400)
    def http_error(err):
        return render_template("error.html", err=err), err.code

    return app
'''

BASE_NOAUTH = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}ACEest Fitness{% endblock %}</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
<header class="top">
  <a class="brand" href="{{ url_for('clients.dashboard') }}">ACEest <span>FUNCTIONAL FITNESS</span></a>
  <nav>
    <a href="{{ url_for('clients.dashboard') }}">Dashboard</a>
    <a href="{{ url_for('clients.list_clients') }}">Clients</a>
    <a href="{{ url_for('clients.programs') }}">Programmes</a>
  </nav>
</header>
<main>
  {% for category, message in get_flashed_messages(with_categories=true) %}
  <div class="flash {{ category }}">{{ message }}</div>
  {% endfor %}
  {% block content %}{% endblock %}
</main>
<footer>v{{ app_version }} · <span class="pill {{ deploy_color }}">{{ deploy_color }}</span> · variant {{ variant }}</footer>
</body>
</html>
'''

DETAIL_V1 = '''{% extends "base.html" %}
{% block content %}
<div class="row"><h1>{{ client.name }}</h1><span>
<a class="btn ghost" href="{{ url_for('clients.edit_client', client_id=client.id) }}">Edit</a>
<form method="post" class="inline" action="{{ url_for('clients.delete', client_id=client.id) }}" onsubmit="return confirm('Delete this client?')">
<button class="btn danger">Delete</button></form>
</span></div>
<div class="grid">
  <div class="card"><h2>Profile</h2>
  <p>Age {{ client.age or '-' }} · {{ client.height or '-' }} cm · {{ client.weight or '-' }} kg</p>
  <p>Programme: <b style="color:{{ program.get('color', '#fff') }}">{{ client.program }}</b></p>
  <p>Calories: <b>{{ client.calories or '-' }}</b> kcal/day</p>
  <p>Target: {{ client.target_weight or '-' }} kg · {{ client.target_adherence or '-' }}% adherence</p>
  <p>Membership: <span class="pill s-{{ status|replace(' ', '-')|lower }}">{{ status }}</span> {{ client.membership_expiry or '' }}</p></div>
  <div class="card"><h2>Weekly training plan</h2><pre>{{ program.get('workout', '') }}</pre></div>
  <div class="card"><h2>Nutrition plan</h2><pre>{{ program.get('diet', '') }}</pre></div>
</div>
{% endblock %}
'''

DETAIL_FN_V1 = '''

@bp.get("/clients/<int:client_id>")
def detail(client_id):
    client = _client_or_404(client_id)
    return render_template(
        "client_detail.html", client=client, program=PROGRAMS.get(client["program"], {}),
        status=membership_status(client["membership_expiry"]))
'''

CONFTEST_NOAUTH = '''import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """Fresh app + isolated SQLite file per test (never touches dev/prod data)."""
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin(client):
    """No authentication before v3.0.0: every visitor may use the app."""
    return client


VALID = {"name": "Ravi", "age": "30", "height": "175", "weight": "80",
         "program": "Fat Loss (FL) - 3 day", "target_weight": "72",
         "target_adherence": "90", "membership_expiry": "2999-01-01"}


@pytest.fixture
def make_client(admin):
    def _make(**over):
        resp = admin.post("/clients/new", data=dict(VALID, **over))
        assert resp.status_code == 302, resp.get_data(as_text=True)
        return int(resp.headers["Location"].rsplit("/", 1)[1])
    return _make
'''

DELETE_TEST = '''

def test_delete_client(make_client, admin):
    cid = make_client()
    assert admin.post(f"/clients/{cid}/delete").status_code == 302
    assert admin.get(f"/clients/{cid}").status_code == 404
    assert admin.post("/clients/999/delete").status_code == 404
'''


def downgrade(root, level):
    """Strip v3 features (level 2) and v2 features as well (level 1)."""
    app = root / "app"
    tmpl = app / "templates"
    # ---- files that only exist from v3.0.0
    for p in ("security.py", "blueprints/auth.py", "templates/login.html",
              "templates/plan.html"):
        (app / p).unlink()
    (root / "tests/test_auth.py").unlink()

    # ---- package + base template
    extra = (", tracking", ", tracking") if level == 2 else ("", "")
    (app / "__init__.py").write_text(
        INIT_NOAUTH % {"extra_import": extra[0], "extra_mod": extra[1]})
    (tmpl / "base.html").write_text(BASE_NOAUTH)

    # ---- config: no bootstrap admin / csrf / shadow mode
    cfg = app / "config.py"
    text = "".join(line for line in cfg.read_text().splitlines(keepends=True)
                   if not any(k in line for k in ("BOOTSTRAP", "SHADOW_MODE", "CSRF_ENABLED")))
    cfg.write_text(drop_defs(text, {"_bool"}))
    sub(app / "blueprints/system.py", ', shadow=c["SHADOW_MODE"]', "")

    # ---- database schema
    rx(app / "db.py", r"CREATE TABLE IF NOT EXISTS users \(.*?\n\);\n", "", re.S)

    # ---- repository
    repo = app / "repository.py"
    drop = {"get_user", "get_user_by_id", "create_user"}
    if level == 1:
        drop |= {"upsert_progress", "list_progress", "add_workout", "list_workouts",
                 "add_metrics", "list_metrics", "dashboard_stats"}
    src = drop_defs(repo.read_text(), drop)
    if level == 1:
        src += '''

def dashboard_stats():
    db = get_db()
    return {
        "clients": db.execute("SELECT COUNT(*) FROM clients").fetchone()[0],
        "by_program": db.execute(
            "SELECT program, COUNT(*) AS n FROM clients GROUP BY program ORDER BY n DESC"
        ).fetchall(),
    }
'''
    repo.write_text(src)

    # ---- programmes service
    prog = app / "services/programs.py"
    drop = {"generate_program", "EXERCISE_POOL", "LEVELS", "WEEK_DAYS"}
    if level == 1:
        drop |= {"calculate_bmi", "WORKOUT_TYPES"}
    prog.write_text(drop_defs(prog.read_text(), drop).replace("import random\n\n", ""))

    # ---- validation service
    val = app / "services/validation.py"
    if level == 1:
        val.write_text(drop_defs(val.read_text(), {
            "validate_progress", "validate_workout", "validate_metrics"}))
        sub(val, "import PROGRAMS, WORKOUT_TYPES", "import PROGRAMS")

    # ---- clients blueprint
    cl = app / "blueprints/clients.py"
    src = drop_defs(cl.read_text(), {"generate", "export_csv", "report_pdf"})
    if level == 1:
        src = drop_defs(src, {"detail"}) + DETAIL_FN_V1
    src = re.sub(r"^@(login|admin)_required\n", "", src, flags=re.M)
    src = src.replace("from ..security import admin_required, login_required\n", "")
    src = src.replace("import csv\nimport io\n\n", "")
    src = src.replace("from flask import (Blueprint, Response, abort,",
                      "from flask import (Blueprint, abort,")
    src = re.sub(r"from \.\.services\.programs import \(.*?\)\n",
                 "from ..services.programs import PROGRAMS"
                 + (", WORKOUT_TYPES, calculate_bmi" if level == 2 else "") + "\n",
                 src, flags=re.S)
    src = src.replace("from ..services import charts\n" if level == 1 else "", "")
    if level == 1:
        src = src.replace("from ..services.validation import validate_client\n",
                          "from ..services.validation import validate_client\n")
    else:
        src = src.replace("levels=list(LEVELS), plan=None,\n        ", "")
    cl.write_text(src)
    if level == 1:
        (app / "services/charts.py").unlink()
        (app / "blueprints/tracking.py").unlink()
    else:
        tr = app / "blueprints/tracking.py"
        text = tr.read_text().replace("from ..security import login_required\n", "")
        tr.write_text(re.sub(r"^@login_required\n", "", text, flags=re.M))

    # ---- templates
    for f in tmpl.glob("*.html"):
        rx(f, r'\s*<input type="hidden" name="_csrf" value="\{\{ csrf_token\(\) \}\}">'
           ) if "_csrf" in f.read_text() else None
    rx(tmpl / "clients.html", r"\n\s*<a class=\"btn ghost\" href=\"\{\{ url_for\('clients\.export_csv'\) \}\}\">Export CSV</a>")
    if level == 1:
        (tmpl / "client_detail.html").write_text(DETAIL_V1)
        for k in ("stats.workouts", "stats.avg_adherence"):
            rx(tmpl / "dashboard.html", r"[^\n]*" + re.escape(k) + r"[^\n]*\n")
    else:
        det = tmpl / "client_detail.html"
        rx(det, r"<a class=\"btn ghost\" href=\"\{\{ url_for\('clients\.report_pdf'[^\n]*\n")
        rx(det, r"\{% if g\.user\['role'\] == 'Admin' %\}\n")
        sub(det, "</form>{% endif %}", "</form>")
        rx(det, r"<form method=\"post\" class=\"card\" action=\"\{\{ url_for\('clients\.generate'.*?</form>\n", "", re.S)

    # ---- tests
    tests = root / "tests"
    (tests / "conftest.py").write_text(CONFTEST_NOAUTH)
    ts = tests / "test_system.py"
    ts.write_text(drop_defs(ts.read_text(), {
        "test_version_reports_metadata", "test_shadow_mode_suppresses_writes",
        "test_bootstrap_admin_from_env", "test_cli_create_user",
        "test_csrf_enforced_when_enabled"}))
    sub(ts, "from app import create_app\n", "")
    tc = tests / "test_clients.py"
    tc.write_text(drop_defs(tc.read_text(), {
        "test_pdf_report", "test_pdf_missing_client", "test_csv_export",
        "test_generate_program", "test_generate_invalid_level"}) + DELETE_TEST)
    tsv = tests / "test_services.py"
    gen = {"test_generate_program_shape_and_determinism",
           "test_generate_program_beginner_three_days", "test_generate_program_invalid"}
    if level == 1:
        gen |= {"test_bmi_categories", "test_bmi_missing_data",
                "test_chart_empty_and_single_point", "test_chart_escapes_labels"}
        header = ("from datetime import date\n\n"
                  "import pytest\n\n"
                  "from app.services.membership import membership_status\n"
                  "from app.services.programs import calculate_calories\n")
    else:
        header = ("from datetime import date\n\n"
                  "import pytest\n\n"
                  "from app.services.charts import line_chart\n"
                  "from app.services.membership import membership_status\n"
                  "from app.services.programs import calculate_bmi, calculate_calories\n")
    body = drop_defs(tsv.read_text(), gen)
    body = body[body.index("@pytest.mark.parametrize"):]
    tsv.write_text(header + "\n\n" + body)
    if level == 1:
        (tests / "test_tracking.py").unlink()


def main(src, out):
    src, out = Path(src), Path(out)
    for level, name in ((1, "v1.0.0"), (2, "v2.0.0"), (3, "v3.0.0")):
        dest = out / name
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        for item in COPY:
            s = src / item
            if s.is_dir():
                shutil.copytree(s, dest / item, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy(s, dest / item)
        if level < 3:
            downgrade(dest, level)
        print("built", dest)


if __name__ == "__main__":
    main(*sys.argv[1:3])
