"""ACEest Fitness & Gym - Flask application factory."""
import click
from flask import Flask, g, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash

from . import repository as repo
from .config import load_config
from .db import close_db, init_db
from .security import check_csrf, csrf_token


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if test_config:
        app.config.update(test_config)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
        user, pwd = app.config["BOOTSTRAP_ADMIN_USER"], app.config["BOOTSTRAP_ADMIN_PASSWORD"]
        if user and pwd and repo.get_user(user) is None:
            repo.create_user(user, generate_password_hash(pwd), "Admin")

    @app.before_request
    def load_user():
        uid = session.get("user_id")
        g.user = repo.get_user_by_id(uid) if uid else None
        # Shadow deployment safety: never perform writes in shadow mode.
        if app.config["SHADOW_MODE"] and request.method not in ("GET", "HEAD", "OPTIONS"):
            return jsonify(shadow="write suppressed"), 202
        check_csrf()

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.context_processor
    def inject_meta():
        return {"app_version": app.config["APP_VERSION"],
                "deploy_color": app.config["DEPLOY_COLOR"],
                "variant": app.config["VARIANT"]}

    from .blueprints import auth, clients, system, tracking
    for module in (system, auth, clients, tracking):
        app.register_blueprint(module.bp)

    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(400)
    def http_error(err):
        return render_template("error.html", err=err), err.code

    @app.cli.command("create-user")
    @click.argument("username")
    @click.argument("role", type=click.Choice(["Admin", "Trainer"]))
    @click.password_option()
    def create_user_cmd(username, role, password):
        """Create a user with a hashed password."""
        if repo.get_user(username):
            raise click.ClickException("User already exists")
        repo.create_user(username, generate_password_hash(password), role)
        click.echo(f"Created {role} {username}")

    return app
