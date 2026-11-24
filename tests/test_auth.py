def test_dashboard_requires_login(client):
    r = client.get("/")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_login_page_renders(client):
    assert client.get("/login").status_code == 200


def test_login_success_and_dashboard(client):
    r = client.post("/login", data={"username": "admin", "password": "adminpw"})
    assert r.status_code == 302
    assert client.get("/").status_code == 200


def test_login_wrong_password(client):
    r = client.post("/login", data={"username": "admin", "password": "bad"})
    assert r.status_code == 401
    assert b"Invalid credentials" in r.data


def test_login_unknown_user(client):
    assert client.post("/login", data={"username": "ghost", "password": "x"}).status_code == 401


def test_passwords_are_hashed(app):
    from app import repository as repo
    with app.app_context():
        assert repo.get_user("admin")["password_hash"] != "adminpw"


def test_logout(admin):
    assert admin.post("/logout").status_code == 302
    assert admin.get("/clients").status_code == 302


def test_open_redirect_blocked(client):
    r = client.post("/login?next=//evil.com", data={"username": "admin", "password": "adminpw"})
    assert "evil.com" not in r.headers["Location"]


def test_next_local_path_honoured(client):
    r = client.post("/login?next=/clients", data={"username": "admin", "password": "adminpw"})
    assert r.headers["Location"].endswith("/clients")


def test_logged_in_user_skips_login_page(admin):
    assert admin.get("/login").status_code == 302


def test_trainer_cannot_delete_client(make_client, trainer):
    cid = make_client()
    assert trainer.post(f"/clients/{cid}/delete").status_code == 403


def test_admin_can_delete_client(make_client, admin):
    cid = make_client()
    assert admin.post(f"/clients/{cid}/delete").status_code == 302
    assert admin.get(f"/clients/{cid}").status_code == 404


def test_delete_missing_client_404(admin):
    assert admin.post("/clients/999/delete").status_code == 404


def test_protected_routes_redirect_anonymous(client):
    for path in ("/clients", "/clients/new", "/programs", "/clients/export.csv"):
        assert client.get(path).status_code == 302
