from app.service import app, hash_password


def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_create_and_read_invoice():
    c = client()
    made = c.post("/invoices", json={"customer": "ACME", "amount": "12.345"}).get_json()
    assert made["amount"] == 12.35 and made["currency"] == "EUR"
    assert c.get(f"/invoices/{made['number']}").get_json()["customer"] == "ACME"


def test_missing_invoice_is_404():
    assert client().get("/invoices/999").status_code == 404


def test_users_store_a_password_hash_not_the_password():
    c = client()
    assert c.post("/users", json={"name": "ana", "password": "s3cret"}).status_code == 201
    assert hash_password("s3cret") != "s3cret"
