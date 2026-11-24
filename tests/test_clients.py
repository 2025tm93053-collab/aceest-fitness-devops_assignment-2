from tests.conftest import VALID


def test_create_client_and_calories(make_client, admin):
    cid = make_client()
    page = admin.get(f"/clients/{cid}")
    assert page.status_code == 200
    assert b"1760" in page.data  # 80 kg x 22


def test_calories_follow_program_factor(make_client, admin):
    cid = make_client(program="Muscle Gain (MG) - PPL")
    assert b"2800" in admin.get(f"/clients/{cid}").data  # 80 x 35


def test_name_required(admin):
    r = admin.post("/clients/new", data=dict(VALID, name=""))
    assert r.status_code == 400 and b"Name is required" in r.data


def test_invalid_program_rejected(admin):
    assert admin.post("/clients/new", data=dict(VALID, program="Bogus")).status_code == 400


def test_numeric_validation(admin):
    for field, bad in (("age", "abc"), ("age", "5"), ("weight", "-3"), ("height", "999"),
                       ("target_adherence", "150"), ("membership_expiry", "31/12/2030")):
        r = admin.post("/clients/new", data=dict(VALID, **{field: bad}))
        assert r.status_code == 400, field


def test_long_name_rejected(admin):
    assert admin.post("/clients/new", data=dict(VALID, name="x" * 81)).status_code == 400


def test_optional_fields_may_be_empty(admin):
    r = admin.post("/clients/new", data={"name": "Min", "program": "Beginner (BG)"})
    assert r.status_code == 302


def test_duplicate_name_conflict(make_client, admin):
    make_client()
    assert admin.post("/clients/new", data=VALID).status_code == 409


def test_list_and_search(make_client, admin):
    make_client(name="Alice")
    make_client(name="Bob")
    assert b"Alice" in admin.get("/clients").data
    r = admin.get("/clients?q=Bo")
    assert b"Bob" in r.data and b"Alice" not in r.data


def test_edit_updates_and_keeps_id(make_client, admin):
    cid = make_client()
    r = admin.post(f"/clients/{cid}/edit", data=dict(VALID, weight="90"))
    assert r.status_code == 302
    assert b"1980" in admin.get(f"/clients/{cid}").data  # 90 x 22


def test_edit_validation_error(make_client, admin):
    cid = make_client()
    assert admin.post(f"/clients/{cid}/edit", data=dict(VALID, age="x")).status_code == 400


def test_edit_form_get_and_missing(make_client, admin):
    cid = make_client()
    assert admin.get(f"/clients/{cid}/edit").status_code == 200
    assert admin.get("/clients/999/edit").status_code == 404


def test_edit_duplicate_name_conflict(make_client, admin):
    make_client(name="A")
    b = make_client(name="B")
    assert admin.post(f"/clients/{b}/edit", data=dict(VALID, name="A")).status_code == 409


def test_new_form_renders(admin):
    assert admin.get("/clients/new").status_code == 200


def test_missing_client_404(admin):
    assert admin.get("/clients/12345").status_code == 404


def test_membership_status_shown(make_client, admin):
    make_client(name="Old", membership_expiry="2000-01-01")
    assert b"Expired" in admin.get("/clients").data


def test_csv_export(make_client, admin):
    make_client()
    r = admin.get("/clients/export.csv")
    assert r.mimetype == "text/csv"
    assert b"Ravi" in r.data and r.data.startswith(b"name,age")


def test_pdf_report(make_client, admin):
    cid = make_client()
    r = admin.get(f"/clients/{cid}/report.pdf")
    assert r.status_code == 200 and r.data[:4] == b"%PDF"


def test_pdf_missing_client(admin):
    assert admin.get("/clients/999/report.pdf").status_code == 404


def test_programs_page_lists_all(admin):
    page = admin.get("/programs").data
    assert b"Beginner (BG)" in page and b"Muscle Gain" in page


def test_dashboard_counts(make_client, admin):
    make_client()
    assert b"Clients by programme" in admin.get("/").data


def test_generate_program(make_client, admin):
    cid = make_client()
    r = admin.post(f"/clients/{cid}/generate", data={"level": "beginner"})
    assert r.status_code == 200 and b"Monday" in r.data


def test_generate_invalid_level(make_client, admin):
    cid = make_client()
    assert admin.post(f"/clients/{cid}/generate", data={"level": "god"}).status_code == 302
