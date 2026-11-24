"""Operational endpoints used by Docker, Kubernetes probes and Jenkins."""
from flask import Blueprint, current_app, jsonify

from ..db import get_db

bp = Blueprint("system", __name__)


@bp.get("/health")
def health():
    """Liveness/readiness: 200 if the app and its database respond, else 503."""
    try:
        get_db().execute("SELECT 1").fetchone()
    except Exception:  # noqa: BLE001 - any DB failure means 'not ready'
        return jsonify(status="unhealthy"), 503
    return jsonify(status="ok", version=current_app.config["APP_VERSION"]), 200


@bp.get("/version")
def version():
    """Reveals which release/colour/variant served the request (strategy demos)."""
    c = current_app.config
    return jsonify(version=c["APP_VERSION"], color=c["DEPLOY_COLOR"],
                   variant=c["VARIANT"], shadow=c["SHADOW_MODE"])
