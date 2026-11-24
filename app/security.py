"""Minimal CSRF protection, login/role decorators and safe redirects."""
import secrets
from functools import wraps

from flask import abort, current_app, g, redirect, request, session, url_for


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def check_csrf():
    if not current_app.config.get("CSRF_ENABLED", True):
        return
    if request.method == "POST" and request.endpoint != "system.health":
        sent = request.form.get("_csrf", "")
        if not secrets.compare_digest(sent, session.get("_csrf", "x")):
            abort(400, "Invalid CSRF token")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "Admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def safe_next(target):
    """Only allow local relative redirects (prevents open-redirect)."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None
