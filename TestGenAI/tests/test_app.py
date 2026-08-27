def test_index_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"TestGen AI" in response.data or b"testgen" in response.data.lower()


def test_health_reports_ai_available(client, app_instance, monkeypatch):
    monkeypatch.setattr(app_instance, "ai_generator", object())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["ai_available"] is True


def test_generate_tests_requires_code(client):
    response = client.post("/generate_tests", data={"language": "python"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_generate_tests_rejects_unsupported_language(client):
    response = client.post(
        "/generate_tests", data={"language": "cobol", "code": "print(1)"}
    )
    assert response.status_code == 400
    assert "Unsupported language" in response.get_json()["error"]


def test_generate_tests_rejects_oversized_code(client):
    huge_code = "x = 1\n" * 10_000
    response = client.post(
        "/generate_tests", data={"language": "python", "code": huge_code}
    )
    assert response.status_code == 400
    assert "too long" in response.get_json()["error"]


def test_generate_tests_happy_path(client, app_instance, monkeypatch):
    class FakeGenerator:
        def generate_tests(self, language, code, requirements=""):
            return {"tests": "def test_ok():\n    assert True\n", "explanation": "1 test"}

    monkeypatch.setattr(app_instance, "ai_generator", FakeGenerator())

    response = client.post(
        "/generate_tests",
        data={"language": "python", "code": "def add(a, b):\n    return a + b\n"},
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "test_ok" in body["tests"]
    assert body["test_file"] == "test_generated.py"


def test_generate_tests_returns_502_on_ai_failure(client, app_instance, monkeypatch):
    class FailingGenerator:
        def generate_tests(self, language, code, requirements=""):
            raise RuntimeError("AI API error: rate limited")

    monkeypatch.setattr(app_instance, "ai_generator", FailingGenerator())

    response = client.post(
        "/generate_tests", data={"language": "python", "code": "print(1)"}
    )
    assert response.status_code == 502
    assert response.get_json()["success"] is False


def test_analyze_code_requires_code(client):
    response = client.post("/analyze_code", json={"language": "python"})
    assert response.status_code == 400


def test_analyze_code_rejects_unsupported_language(client):
    response = client.post(
        "/analyze_code", json={"language": "cobol", "code": "DISPLAY 1"}
    )
    assert response.status_code == 400
    assert "Unsupported language" in response.get_json()["error"]


def test_analyze_code_returns_analysis(client):
    response = client.post(
        "/analyze_code",
        json={
            "language": "python",
            "code": "def add(a, b):\n    return a + b\n",
            "description": "adds two numbers",
        },
    )
    body = response.get_json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "quality_score" in body["analysis"]


def test_run_tests_requires_test_file(client):
    response = client.post("/run_tests", json={"language": "python"})
    assert response.status_code == 400


def test_run_tests_rejects_unsupported_language(client):
    response = client.post(
        "/run_tests", json={"language": "cobol", "test_file": "test.cbl"}
    )
    assert response.status_code == 400
    assert "Unsupported language" in response.get_json()["error"]


def test_run_tests_missing_file_returns_404(client):
    response = client.post(
        "/run_tests", json={"language": "python", "test_file": "does_not_exist.py"}
    )
    assert response.status_code == 404


def test_download_test_rejects_path_traversal(client):
    response = client.get("/download_test/..%2F..%2Fapp.py")
    assert response.status_code == 404


def test_download_test_missing_file(client):
    response = client.get("/download_test/nope.py")
    assert response.status_code == 404
