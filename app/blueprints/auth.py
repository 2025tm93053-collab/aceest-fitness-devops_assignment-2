from flask import (Blueprint, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash

from .. import repository as repo
from ..security import safe_next

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = repo.get_user(request.form.get("username", "").strip())
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(safe_next(request.args.get("next")) or url_for("clients.dashboard"))
        flash("Invalid credentials", "error")
        return render_template("login.html"), 401
    if g.get("user"):
        return redirect(url_for("clients.dashboard"))
    return render_template("login.html")


@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
