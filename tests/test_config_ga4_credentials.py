import json

from config import Config


def test_get_ga4_credentials_from_google_service_account_json_env(monkeypatch):
    creds = {
        "type": "service_account",
        "project_id": "p",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",
        "client_email": "svc@example.com",
    }
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON", json.dumps(creds))
    monkeypatch.delenv("GCP_CREDENTIALS_JSON", raising=False)

    loaded = Config.get_ga4_credentials()

    assert loaded["client_email"] == "svc@example.com"
    assert loaded["project_id"] == "p"
