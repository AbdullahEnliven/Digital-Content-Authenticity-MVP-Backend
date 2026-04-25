from io import BytesIO

from PIL import Image


def make_test_image():
    image = Image.new("RGB", (16, 16), color=(120, 80, 200))
    file = BytesIO()
    image.save(file, format="PNG")
    file.seek(0)
    return file


def auth_headers(client):
    register = client.post(
        "/api/v1/auth/register",
        json={"email": "demo@example.com", "full_name": "Demo User", "password": "strongpass123"},
    )
    token = register.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow(client):
    headers = auth_headers(client)
    upload = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("sample.png", make_test_image(), "image/png")},
    )
    assert upload.status_code == 201
    upload_id = upload.json()["id"]

    verify = client.post(
        f"/api/v1/verifications/{upload_id}/start",
        headers=headers,
        json={"include_identity": True, "auto_issue_certificate": True},
    )
    assert verify.status_code == 200
    verification = verify.json()
    assert verification["status"] == "completed"
    assert verification["certificate"] is not None

    history = client.get("/api/v1/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1

    cert = client.get(f"/api/v1/certificates/{verification['id']}/metadata", headers=headers)
    assert cert.status_code == 200
