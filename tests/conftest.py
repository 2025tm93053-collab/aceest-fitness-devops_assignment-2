import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app import repository as repo


@pytest.fixture
def app(tmp_path):
    """Fresh app + isolated SQLite file per test (never touches dev/prod data)."""
    app = create_app({"TESTING": True, "CSRF_ENABLED": False, "SECRET_KEY": "test",
                      "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        repo.create_user("admin", generate_password_hash("adminpw"), "Admin")
        repo.create_user("coach", generate_password_hash("coachpw"), "Trainer")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


@pytest.fixture
def admin(client):
    _login(client, "admin", "adminpw")
    return client


@pytest.fixture
def trainer(app):
    c = app.test_client()
    _login(c, "coach", "coachpw")
    return c


VALID = {"name": "Ravi", "age": "30", "height": "175", "weight": "80",
         "program": "Fat Loss (FL) - 3 day", "target_weight": "72",
         "target_adherence": "90", "membership_expiry": "2999-01-01"}


@pytest.fixture
def make_client(admin, app):
    def _make(**over):
        resp = admin.post("/clients/new", data=dict(VALID, **over))
        assert resp.status_code == 302, resp.get_data(as_text=True)
        return int(resp.headers["Location"].rsplit("/", 1)[1])
    return _make
