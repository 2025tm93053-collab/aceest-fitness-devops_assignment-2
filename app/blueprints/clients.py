import csv
import io

from flask import (Blueprint, Response, abort, flash, redirect, render_template,
                   request, url_for)

from .. import repository as repo
from ..security import admin_required, login_required
from ..services import charts
from ..services.membership import membership_status
from ..services.programs import (LEVELS, PROGRAMS, WORKOUT_TYPES, calculate_bmi,
                                 generate_program)
from ..services.validation import validate_client

bp = Blueprint("clients", __name__)


def _client_or_404(client_id):
    client = repo.get_client(client_id)
    if client is None:
        abort(404)
    return client


@bp.get("/")
@login_required
def dashboard():
    return render_template("dashboard.html", stats=repo.dashboard_stats())


@bp.get("/clients")
@login_required
def list_clients():
    q = request.args.get("q", "").strip()
    rows = [dict(c, status=membership_status(c["membership_expiry"]))
            for c in repo.list_clients(q)]
    return render_template("clients.html", clients=rows, q=q)


def _form(client, errors=None, status=200):
    client = dict(client)  # sqlite3.Row has no .get()
    return render_template("client_form.html", client=client, programs=PROGRAMS,
                           errors=errors or []), status


@bp.route("/clients/new", methods=["GET", "POST"])
@login_required
def create_client():
    if request.method == "POST":
        data, errors = validate_client(request.form)
        if not errors:
            try:
                client_id = repo.save_client(data)
            except Exception as exc:  # unique-name violation
                if "UNIQUE" not in str(exc):
                    raise
                return _form(data, ["A client with this name already exists"], 409)
            flash("Client created", "ok")
            return redirect(url_for("clients.detail", client_id=client_id))
        return _form(request.form, errors, 400)
    return _form({})


@bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = _client_or_404(client_id)
    if request.method == "POST":
        data, errors = validate_client(request.form)
        if not errors:
            try:
                repo.save_client(data, client_id)
            except Exception as exc:
                if "UNIQUE" not in str(exc):
                    raise
                return _form(dict(data, id=client_id), ["A client with this name already exists"],
                             409)
            flash("Client updated", "ok")
            return redirect(url_for("clients.detail", client_id=client_id))
        return _form(dict(request.form, id=client_id), errors, 400)
    return _form(client)


@bp.get("/clients/<int:client_id>")
@login_required
def detail(client_id):
    client = _client_or_404(client_id)
    progress = repo.list_progress(client_id)
    metrics = [m for m in repo.list_metrics(client_id) if m["weight"]]
    program = PROGRAMS.get(client["program"], {})
    weights = [m["weight"] for m in metrics]
    return render_template(
        "client_detail.html", client=client, program=program,
        status=membership_status(client["membership_expiry"]),
        bmi=calculate_bmi(client["height"], client["weight"]),
        progress=progress, metrics=repo.list_metrics(client_id),
        workouts=repo.list_workouts(client_id), workout_types=WORKOUT_TYPES,
        levels=list(LEVELS), plan=None,
        adherence_chart=charts.line_chart([p["week_start"] for p in progress],
                                          [p["adherence"] for p in progress], unit="%"),
        weight_chart=charts.line_chart(
            [m["date"] for m in metrics], weights,
            y_min=min(weights) - 2 if weights else 0, y_max=max(weights) + 2 if weights else 1,
            color="#e67e22", unit=" kg"))


@bp.post("/clients/<int:client_id>/delete")
@admin_required
def delete(client_id):
    if not repo.delete_client(client_id):
        abort(404)
    flash("Client deleted", "ok")
    return redirect(url_for("clients.list_clients"))


@bp.post("/clients/<int:client_id>/generate")
@login_required
def generate(client_id):
    client = _client_or_404(client_id)
    try:
        plan = generate_program(client["program"], request.form.get("level", ""))
    except ValueError:
        flash("Invalid experience level", "error")
        return redirect(url_for("clients.detail", client_id=client_id))
    return render_template(
        "plan.html", client=client, plan=plan, level=request.form["level"])


@bp.get("/clients/export.csv")
@login_required
def export_csv():
    out = io.StringIO()
    writer = csv.writer(out)
    cols = ["name", "age", "height", "weight", "program", "calories",
            "target_weight", "target_adherence", "membership_expiry"]
    writer.writerow(cols)
    for c in repo.list_clients():
        writer.writerow([c[k] for k in cols])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=clients.csv"})


@bp.get("/clients/<int:client_id>/report.pdf")
@login_required
def report_pdf(client_id):
    from fpdf import FPDF  # fpdf2

    client = _client_or_404(client_id)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, f"ACEest Client Report - {client['name']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    rows = [("Age", client["age"]), ("Height (cm)", client["height"]),
            ("Weight (kg)", client["weight"]), ("Programme", client["program"]),
            ("Calories/day", client["calories"]), ("Target weight", client["target_weight"]),
            ("Target adherence", client["target_adherence"]),
            ("Membership expiry", client["membership_expiry"]),
            ("Membership status", membership_status(client["membership_expiry"]))]
    for label, value in rows:
        pdf.cell(0, 8, f"{label}: {'-' if value is None else value}",
                 new_x="LMARGIN", new_y="NEXT")
    return Response(bytes(pdf.output()), mimetype="application/pdf",
                    headers={"Content-Disposition": f"inline; filename=client_{client_id}.pdf"})


@bp.get("/programs")
@login_required
def programs():
    return render_template("programs.html", programs=PROGRAMS)
