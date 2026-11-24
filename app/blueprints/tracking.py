from flask import Blueprint, abort, flash, redirect, request, url_for

from .. import repository as repo
from ..security import login_required
from ..services.validation import validate_metrics, validate_progress, validate_workout

bp = Blueprint("tracking", __name__)


def _guard(client_id):
    if repo.get_client(client_id) is None:
        abort(404)


def _back(client_id, errors=None):
    for e in errors or []:
        flash(e, "error")
    if not errors:
        flash("Saved", "ok")
    return redirect(url_for("clients.detail", client_id=client_id))


@bp.post("/clients/<int:client_id>/progress")
@login_required
def add_progress(client_id):
    _guard(client_id)
    data, errors = validate_progress(request.form)
    if not errors:
        repo.upsert_progress(client_id, data["week_start"], data["adherence"])
    return _back(client_id, errors)


@bp.post("/clients/<int:client_id>/workouts")
@login_required
def add_workout(client_id):
    _guard(client_id)
    data, exercises, errors = validate_workout(request.form)
    if not errors:
        repo.add_workout(client_id, data, exercises)
    return _back(client_id, errors)


@bp.post("/clients/<int:client_id>/metrics")
@login_required
def add_metrics(client_id):
    _guard(client_id)
    data, errors = validate_metrics(request.form)
    if not errors:
        repo.add_metrics(client_id, data)
    return _back(client_id, errors)
