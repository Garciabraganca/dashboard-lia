import json
from unittest.mock import Mock, patch

from dashboard_kpis import build_meta_kpi_cards_payload
from meta_integration import MetaAdsIntegration


def _response(data, status=200):
    resp = Mock()
    resp.status_code = status
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"data": data}
    return resp


def test_frequency_hourly_breakdown_fallback_to_non_hourly():
    client = MetaAdsIntegration(access_token="secret_token", ad_account_id="123")

    hourly_zero = _response([
        {"impressions": "1000", "reach": "0", "frequency": "0"}
    ])
    no_hourly_ok = _response([
        {"impressions": "1000", "reach": "500", "frequency": "2.0"}
    ])

    with patch("requests.get", side_effect=[hourly_zero, no_hourly_ok]) as mock_get:
        result = client.get_aggregated_insights(
            date_range="custom",
            custom_start="2024-01-01",
            custom_end="2024-01-07",
            breakdowns=["hourly_stats_aggregated_by_advertiser_time_zone"],
        )

    assert result["reach"] == 500
    assert result["frequency"] == 2.0
    assert result["_debug"]["fallback_reason"] == "hourly_breakdown_missing_frequency_or_reach_with_delivery"
    assert len(result["_debug"]["requests"]) == 2

    first_params = mock_get.call_args_list[0][1]["params"]
    assert "breakdowns" in first_params
    second_params = mock_get.call_args_list[1][1]["params"]
    assert "breakdowns" not in second_params


def test_debug_sanitizes_access_token():
    client = MetaAdsIntegration(access_token="very_secret_token", ad_account_id="123")

    with patch("requests.get", return_value=_response([{"impressions": "10", "reach": "5", "frequency": "2"}])):
        result = client.get_aggregated_insights(date_range="last_7d")

    debug_req = result["_debug"]["requests"][0]
    assert debug_req["access_token"] == "***"
    assert "very_secret_token" not in json.dumps(result["_debug"])


def test_frequency_card_is_rendered_with_value():
    cards = build_meta_kpi_cards_payload(
        {
            "frequencia": 3.14,
            "alcance": 100,
            "impressoes": 314,
        }
    )

    freq_cards = [c for c in cards if c["label"] == "Vezes que cada pessoa viu"]
    assert len(freq_cards) == 1
    assert freq_cards[0]["value"] == "3.14"


def test_hourly_zero_without_delivery_does_not_trigger_fallback():
    client = MetaAdsIntegration(access_token="secret_token", ad_account_id="123")

    hourly_legit_zero = _response([
        {"impressions": "0", "reach": "0", "frequency": "0"}
    ])

    with patch("requests.get", return_value=hourly_legit_zero) as mock_get:
        result = client.get_aggregated_insights(
            date_range="custom",
            custom_start="2024-01-01",
            custom_end="2024-01-07",
            breakdowns=["hourly_stats_aggregated_by_advertiser_time_zone"],
        )

    assert result["reach"] == 0
    assert result["frequency"] == 0
    assert result["_debug"]["fallback_reason"] is None
    assert len(result["_debug"]["requests"]) == 1
    assert mock_get.call_count == 1


def test_debug_request_cap_and_sample_truncation():
    client = MetaAdsIntegration(access_token="very_secret_token", ad_account_id="123")

    long_name = "campaign-" + ("x" * 200)
    with patch("requests.get", return_value=_response([
        {"impressions": "10", "reach": "5", "frequency": "2", "campaign_name": long_name}
    ])):
        result = client.get_aggregated_insights(date_range="last_7d")

    sample_name = result["_debug"]["response_sample"]["campaign_name"]
    assert len(sample_name) <= 120
    assert sample_name.endswith("...")
    assert len(result["_debug"]["requests"]) <= 2
