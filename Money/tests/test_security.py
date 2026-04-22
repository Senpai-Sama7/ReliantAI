"""
Security tests — auth enforcement, rate limiting, XSS, injection.
"""

import os
import re

os.environ["SKIP_TWILIO_VALIDATION"] = "true"


class TestApiKeyAuth:
    def test_no_key_returns_401(self, client):
        r = client.post("/dispatch", json={"customer_message": "test"})
        assert r.status_code == 401

    def test_wrong_key_returns_401(self, client):
        r = client.post("/dispatch", json={"customer_message": "test"}, headers={"x-api-key": "wrong"})
        assert r.status_code == 401

    def test_dispatches_no_key_returns_401(self, client):
        r = client.get("/dispatches")
        assert r.status_code == 401

    def test_run_no_key_returns_401(self, client):
        r = client.get("/run/test-id")
        assert r.status_code == 401


class TestXssPrevention:
    def test_xss_in_dispatch_message(self, client, api_headers):
        xss = '<script>alert("xss")</script>'
        r = client.post("/dispatch", json={"customer_message": xss}, headers=api_headers)
        assert r.status_code == 200
        # The script tag should not appear unescaped in any response
        assert "<script>" not in r.text

    def test_xss_in_sms_body(self, client):
        xss = '<img src=x onerror=alert(1)>'
        r = client.post("/sms", data={"From": "+15559999999", "Body": xss, "MessageSid": "SM1", "To": "+15550000000"})
        assert r.status_code == 200
        assert "onerror" not in r.text


class TestSqlInjection:
    def test_sql_injection_in_dispatch_id(self, client, api_headers):
        r = client.get("/run/'; DROP TABLE dispatches; --", headers=api_headers)
        # Should return 404, not crash
        assert r.status_code == 404

    def test_sql_injection_in_sms_body(self, client):
        r = client.post("/sms", data={
            "From": "+15558888888",
            "Body": "'; DROP TABLE messages; --",
            "MessageSid": "SM1", "To": "+15550000000"
        })
        assert r.status_code == 200


class TestRateLimiting:
    def test_sms_per_phone_rate_limit(self, client):
        """Same phone within 5 seconds should get empty TwiML."""
        data = {"From": "+15557777777", "Body": "test", "MessageSid": "SM1", "To": "+15550000000"}
        r1 = client.post("/sms", data=data)
        assert r1.status_code == 200
        assert "<Message>" in r1.text  # First request gets a message

        r2 = client.post("/sms", data=data)
        assert r2.status_code == 200
        # Rate-limited: empty TwiML response
        assert "<Message>" not in r2.text


class TestSecurityHeaders:
    def test_all_security_headers_present(self, client):
        r = client.get("/health")
        assert r.headers.get("strict-transport-security") == "max-age=31536000; includeSubDomains"
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"


class TestLoginCsrf:
    @staticmethod
    def _extract_csrf_token(response_text: str) -> str:
        match = re.search(r'name="csrf_token" value="([^"]+)"', response_text)
        assert match is not None
        return match.group(1)

    def test_login_page_sets_csrf_cookie_and_hidden_field(self, client):
        response = client.get("/login")

        assert response.status_code == 200
        form_token = self._extract_csrf_token(response.text)
        assert client.cookies.get("dispatch_login_csrf") == form_token

    def test_login_rejects_missing_csrf_token(self, client):
        response = client.post(
            "/login",
            data={"username": "admin", "password": "test-key-123"},
            follow_redirects=False,
        )

        assert response.status_code == 403
        assert "Invalid or expired CSRF token" in response.text

    def test_login_rejects_invalid_csrf_token(self, client):
        login_page = client.get("/login")
        csrf_token = self._extract_csrf_token(login_page.text)
        invalid_token = f"{csrf_token[:-1]}x" if csrf_token[-1] != "x" else f"{csrf_token[:-1]}y"

        response = client.post(
            "/login",
            data={"username": "admin", "password": "test-key-123", "csrf_token": invalid_token},
            follow_redirects=False,
        )

        assert response.status_code == 403
        assert "Invalid or expired CSRF token" in response.text

    def test_login_accepts_valid_csrf_token(self, client):
        login_page = client.get("/login")
        csrf_token = self._extract_csrf_token(login_page.text)

        response = client.post(
            "/login",
            data={"username": "admin", "password": "test-key-123", "csrf_token": csrf_token},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"] == "/admin"
        assert client.cookies.get("dispatch_session")
        assert client.cookies.get("dispatch_login_csrf") is None
