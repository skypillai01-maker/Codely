import os
import sys
import json
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi.testclient import TestClient
from core.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["service"] == "Codely AI"


class TestAuthFlow:
    def test_login_page_served(self, client):
        resp = client.get("/api/v1/auth/request-login")
        assert resp.status_code == 200
        assert "Sign In" in resp.text
        assert "Codely" in resp.text

    def test_index_served(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Codely AI" in resp.text

    def test_request_magic_link(self, client):
        resp = client.post(
            "/api/v1/auth/request-login",
            json={"email": "test@example.com"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "dev_link" in data
        assert "magic" in data["message"].lower()
        assert "/api/v1/auth/verify?token=" in data["dev_link"]

    def test_full_auth_flow(self, client):
        resp = client.post(
            "/api/v1/auth/request-login",
            json={"email": "flowtest@example.com"}
        )
        assert resp.status_code == 200
        token = resp.json()["dev_link"].split("token=")[-1]

        resp = client.post(
            "/api/v1/auth/verify",
            json={"token": token}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["email"] == "flowtest@example.com"
        session_id = data["session_id"]

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_id}"}
        )
        assert resp.status_code == 200
        me = resp.json()
        assert me["user_id"] == data["user_id"]
        assert me["email"] == "flowtest@example.com"

        resp = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {session_id}"}
        )
        assert resp.status_code == 200

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_id}"}
        )
        assert resp.status_code == 401

    def test_verify_get_redirects(self, client):
        resp = client.post(
            "/api/v1/auth/request-login",
            json={"email": "redirecttest@example.com"}
        )
        token = resp.json()["dev_link"].split("token=")[-1]

        resp = client.get(f"/api/v1/auth/verify?token={token}", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "session_id" in resp.headers["location"]

    def test_invalid_token_returns_error(self, client):
        resp = client.post("/api/v1/auth/verify", json={"token": "garbage"})
        assert resp.status_code == 400

    def test_endpoints_require_auth(self, client):
        protected = [
            ("GET", "/api/v1/auth/me"),
            ("POST", "/api/v1/auth/logout"),
            ("GET", "/api/v1/threads"),
        ]
        for method, path in protected:
            resp = client.request(method, path)
            assert resp.status_code == 401, f"{method} {path} should require auth"


class TestModules:
    def test_list_modules(self, client):
        resp = client.get("/api/v1/modules")
        assert resp.status_code == 200
        data = resp.json()
        assert "modules" in data
        names = [m["name"] for m in data["modules"]]
        assert "WebSearch" in names
        assert "FileWrite" in names
        assert "SandboxExec" in names
        assert "TestGen" in names

    def test_list_tools(self, client):
        resp = client.get("/api/v1/tools")
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data
        assert len(data["tools"]) >= 3


class TestMemory:
    def _setup_session(self, client):
        resp = client.post(
            "/api/v1/auth/request-login",
            json={"email": "memorytest@example.com"}
        )
        token = resp.json()["dev_link"].split("token=")[-1]
        resp = client.post("/api/v1/auth/verify", json={"token": token})
        return resp.json()["session_id"]

    def test_add_and_clear_memory(self, client):
        sid = self._setup_session(client)
        headers = {"Authorization": f"Bearer {sid}"}
        cid = "test_thread_mem"

        resp = client.post(
            "/api/v1/memory/add",
            json={"context_id": cid, "text": "Test memory content for search."},
            headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        resp = client.delete(f"/api/v1/memory/clear/{cid}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_thread_listing(self, client):
        sid = self._setup_session(client)
        headers = {"Authorization": f"Bearer {sid}"}

        resp = client.get("/api/v1/threads", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "threads" in data
        assert "count" in data


class TestChat:
    def _setup_session(self, client):
        resp = client.post(
            "/api/v1/auth/request-login",
            json={"email": "chattest@example.com"}
        )
        token = resp.json()["dev_link"].split("token=")[-1]
        resp = client.post("/api/v1/auth/verify", json={"token": token})
        return resp.json()["session_id"]

    def test_chat_requires_context_and_prompt(self, client):
        sid = self._setup_session(client)
        headers = {"Authorization": f"Bearer {sid}"}

        resp = client.post("/api/v1/chat", json={}, headers=headers)
        assert resp.status_code == 400

        resp = client.post(
            "/api/v1/chat",
            json={"context_id": "test", "prompt": ""},
            headers=headers
        )
        assert resp.status_code == 400

    def test_chat_without_ollama_returns_error(self, client):
        sid = self._setup_session(client)
        headers = {"Authorization": f"Bearer {sid}"}

        resp = client.post(
            "/api/v1/chat",
            json={"context_id": "test", "prompt": "Hello"},
            headers=headers
        )
        assert resp.status_code == 503
        err = resp.text.lower()
        assert "ollama" in err or "connect" in err
