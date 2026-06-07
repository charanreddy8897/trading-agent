"""Integration tests for auth endpoints."""
import pytest
import pyotp


@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    """Test the full auth flow through the API."""

    def test_login_success(self, client, sample_user):
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "totp_required"
        assert "temp_token" in data

    def test_login_wrong_password(self, client, sample_user):
        response = client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword",
        })
        assert response.status_code == 401
        assert "Incorrect credentials" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        response = client.post("/api/v1/auth/login", json={
            "username": "nobody",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_totp_verify_success(self, client, sample_user, temp_token):
        totp = pyotp.TOTP(sample_user.totp_secret)
        code = totp.now()
        response = client.post("/api/v1/auth/totp", json={
            "temp_token": temp_token,
            "code": code,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_totp_verify_invalid_code(self, client, sample_user, temp_token):
        response = client.post("/api/v1/auth/totp", json={
            "temp_token": temp_token,
            "code": "000000",
        })
        assert response.status_code == 401
        assert "Invalid TOTP code" in response.json()["detail"]

    def test_totp_verify_invalid_temp_token(self, client):
        response = client.post("/api/v1/auth/totp", json={
            "temp_token": "invalid.jwt.token",
            "code": "123456",
        })
        assert response.status_code == 401

    def test_totp_setup_get(self, client, temp_token, sample_user):
        sample_user.totp_enabled = False
        sample_user.totp_secret = None
        response = client.get(f"/api/v1/auth/totp-setup?temp_token={temp_token}")
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "otpauth_uri" in data
        assert "qr_data_uri" in data
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 8

    def test_totp_setup_verify_success(self, client, db_session, sample_user, temp_token):
        sample_user.totp_enabled = False
        secret = "JBSWY3DPEHPK3PXP"
        sample_user.totp_secret = secret
        db_session.commit()

        totp = pyotp.TOTP(secret)
        code = totp.now()

        response = client.post("/api/v1/auth/totp-setup", json={
            "temp_token": temp_token,
            "code": code,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_success(self, client, sample_user):
        from app.auth.service import TokenType, auth_service
        refresh_token = auth_service.create_token(sample_user.id, TokenType.REFRESH)

        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalid(self, client):
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.jwt.token",
        })
        assert response.status_code == 401

    def test_me_endpoint_success(self, client, auth_headers, sample_user):
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["totp_enabled"] is True
        assert data["is_active"] is True

    def test_me_endpoint_no_auth(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_me_endpoint_invalid_token(self, client):
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid.jwt.token"
        })
        assert response.status_code == 401

    def test_full_auth_flow(self, client, db_session):
        """Test complete flow: create user → login → TOTP setup → verify → get JWT."""
        from app.auth.service import auth_service

        # 1. Create user
        user = auth_service.create_user(db_session, "flowtest", "password123")
        user.totp_enabled = False
        db_session.commit()

        # 2. Login
        resp = client.post("/api/v1/auth/login", json={
            "username": "flowtest",
            "password": "password123",
        })
        assert resp.status_code == 200
        temp_token = resp.json()["temp_token"]

        # 3. Get TOTP setup
        resp = client.get(f"/api/v1/auth/totp-setup?temp_token={temp_token}")
        assert resp.status_code == 200
        secret = resp.json()["secret"]

        # 4. Verify with correct code
        totp = pyotp.TOTP(secret)
        code = totp.now()
        resp = client.post("/api/v1/auth/totp-setup", json={
            "temp_token": temp_token,
            "code": code,
        })
        assert resp.status_code == 200
        tokens = resp.json()

        # 5. Use access token
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {tokens['access_token']}"
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == "flowtest"
