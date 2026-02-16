from unittest.mock import Mock

from config import Config
from landing_events_service import build_landing_events_card_data


def test_events_mode_off_skips_ga4_call(monkeypatch):
    client = Mock()

    payload = build_landing_events_card_data(
        client,
        events_mode="off",
        period_api="last_7d",
        custom_start=None,
        custom_end=None,
        landing_host_filter=None,
    )

    assert payload["status"] == "disabled"
    client.get_landing_events_summary.assert_not_called()


def test_config_events_mode_default_off_when_ga4_not_configured(monkeypatch):
    monkeypatch.delenv("EVENTS_MODE", raising=False)
    monkeypatch.delenv("GA4_SERVICE_ACCOUNT_JSON", raising=False)
    monkeypatch.delenv("GCP_CREDENTIALS_JSON", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON", raising=False)

    assert Config.get_events_mode() == "off"


def test_config_events_mode_env_override(monkeypatch):
    monkeypatch.setenv("EVENTS_MODE", "ga4")
    assert Config.get_events_mode() == "ga4"
