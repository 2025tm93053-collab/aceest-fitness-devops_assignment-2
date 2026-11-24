from app import create_app


def test_factory_creates_app(app):
    assert app.testing is True


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json["status"] == "ok"


def test_health_503_when_db_broken(app, monkeypatch):
    import app.blueprints.system as system

    def boom():
        raise RuntimeError("db down")

    monkeypatch.setattr(system, "get_db", boom)
    r = app.test_client().get("/health")
    assert r.status_code == 503 and r.json["status"] == "unhealthy"


def test_version_reports_metadata(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "v.db"),
                      "APP_VERSION": "2.0.0", "DEPLOY_COLOR": "green", "VARIANT": "B"})
    assert app.test_client().get("/version").json == {
        "version": "2.0.0", "color": "green", "variant": "B", "shadow": False}


def test_shadow_mode_suppresses_writes(tmp_path):
    app = create_app({"TESTING": True, "CSRF_ENABLED": False, "SHADOW_MODE": True,
                      "DATABASE": str(tmp_path / "s.db")})
    r = app.test_client().post("/clients/new", data={"name": "x"})
    assert r.status_code == 202


def test_unknown_route_404(client):
    assert client.get("/nope").status_code == 404


def test_bootstrap_admin_from_env(tmp_path):
    cfg = {"TESTING": True, "CSRF_ENABLED": False, "DATABASE": str(tmp_path / "b.db"),
           "BOOTSTRAP_ADMIN_USER": "boss", "BOOTSTRAP_ADMIN_PASSWORD": "pw"}
    create_app(cfg)
    app = create_app(cfg)  # second start must not fail or duplicate the user
    r = app.test_client().post("/login", data={"username": "boss", "password": "pw"})
    assert r.status_code == 302


def test_cli_create_user(app):
    runner = app.test_cli_runner()
    r = runner.invoke(args=["create-user", "newbie", "Trainer"], input="pw12345\npw12345\n")
    assert r.exit_code == 0, r.output
    dup = runner.invoke(args=["create-user", "newbie", "Trainer"], input="pw12345\npw12345\n")
    assert dup.exit_code != 0


def test_csrf_enforced_when_enabled(tmp_path):
    app = create_app({"TESTING": True, "CSRF_ENABLED": True, "DATABASE": str(tmp_path / "c.db")})
    c = app.test_client()
    assert c.post("/login", data={"username": "a", "password": "b"}).status_code == 400
    c.get("/login")
    with c.session_transaction() as s:
        token = s["_csrf"]
    assert c.post("/login", data={"username": "a", "password": "b", "_csrf": token}
                  ).status_code == 401
