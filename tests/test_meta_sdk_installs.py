"""
Tests for Meta SDK install counting
Updated to reflect new behavior where SDK installs come from get_all_sdk_events
which queries multiple event types via App Events API and falls back to Ads Insights.
"""
import pytest
from unittest.mock import Mock, patch, call
from meta_integration import MetaAdsIntegration


@pytest.fixture
def mock_meta_client():
    """Create a mock Meta Ads client for testing"""
    return MetaAdsIntegration(
        access_token="test_token",
        ad_account_id="123456789",
        app_id="test_app_id"
    )


# Number of event types queried by get_all_sdk_events
_SDK_EVENT_COUNT = 6


def _make_agg_response(value=0, status=200):
    """Helper to create a mock response for app_event_aggregations."""
    resp = Mock()
    resp.status_code = status
    if status == 200:
        resp.json.return_value = {
            "data": [{"timestamp": "2024-01-01", "value": value}] if value > 0 else []
        }
    else:
        resp.json.return_value = {
            "error": {"message": "Not found", "code": 803}
        }
    return resp


def test_get_sdk_installs_from_app_event_aggregations(mock_meta_client):
    """Test that SDK installs are fetched from app_event_aggregations as primary source"""

    # Mock different values per event type
    mock_responses = [
        _make_agg_response(153),  # fb_mobile_install
        _make_agg_response(200),  # fb_mobile_activate_app
        _make_agg_response(50),   # fb_mobile_content_view
        _make_agg_response(0),    # fb_mobile_purchase
        _make_agg_response(0),    # fb_mobile_add_to_cart
        _make_agg_response(0),    # fb_mobile_complete_registration
    ]

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_sdk_installs(date_range="last_7d")

        # Should get installs from fb_mobile_install
        assert result["installs"] == 153
        assert result["source"] == "app_event_aggregations"
        assert "fb_mobile_install" in result["event_types"]
        assert "fb_mobile_activate_app" in result["event_types"]
        assert "fb_mobile_content_view" in result["event_types"]

        # all_sdk_events should contain all non-zero events
        assert result["all_sdk_events"]["fb_mobile_install"] == 153
        assert result["all_sdk_events"]["fb_mobile_activate_app"] == 200
        assert result["all_sdk_events"]["fb_mobile_content_view"] == 50


def test_get_sdk_installs_ignores_campaign_filter(mock_meta_client):
    """Test that campaign filter is ignored for SDK installs (returns total) and emits deprecation warning"""

    mock_responses = [
        _make_agg_response(100),  # fb_mobile_install
    ] + [_make_agg_response(0)] * (_SDK_EVENT_COUNT - 1)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        # Call with campaign filter - should emit deprecation warning
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = mock_meta_client.get_sdk_installs(
                date_range="last_7d",
                campaign_name_filter="LIA"
            )

            # Should return total installs, campaign filter is ignored
            assert result["installs"] == 100
            assert result["source"] == "app_event_aggregations"

            # Verify deprecation warning was emitted
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "campaign_name_filter" in str(w[0].message)


def test_get_sdk_installs_respects_date_range(mock_meta_client):
    """Test that date range is properly applied in the API request"""

    mock_responses = [_make_agg_response(42)] + [_make_agg_response(0)] * (_SDK_EVENT_COUNT - 1)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        # Call with specific date range
        mock_meta_client.get_sdk_installs(
            date_range="custom",
            custom_start="2024-01-01",
            custom_end="2024-01-31"
        )

        # Verify the first API call (fb_mobile_install) has correct time_range
        first_call = mock_get.call_args_list[0]
        params = first_call[1]["params"]

        assert "time_range" in params
        import json
        time_range = json.loads(params["time_range"])
        assert time_range["since"] == "2024-01-01"
        assert time_range["until"] == "2024-01-31"


def test_get_sdk_installs_fallback_to_ads_insights(mock_meta_client):
    """Test fallback to account-level ads insights when all app_event_aggregations fail"""

    # Mock ads insights response (fallback)
    mock_ads_response = Mock()
    mock_ads_response.status_code = 200
    mock_ads_response.json.return_value = {
        "data": [
            {
                "actions": [
                    {"action_type": "mobile_app_install", "value": "4"},
                    {"action_type": "fb_mobile_activate_app", "value": "10"},
                ]
            }
        ]
    }
    mock_ads_response.raise_for_status.return_value = None

    # All app_event_aggregations calls fail, then ads insights succeeds
    mock_responses = [_make_agg_response(0, status=404)] * _SDK_EVENT_COUNT + [mock_ads_response]

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_sdk_installs(date_range="last_7d")

        # Should use ads insights fallback (attributed installs only)
        assert result["installs"] == 4
        assert result["source"] == "ads_insights_account_level"
        assert "mobile_app_install" in result["event_types"]


def test_get_sdk_installs_uses_activate_app_as_proxy(mock_meta_client):
    """Test that activate_app is used as proxy when no install events found"""

    # Only activate_app events, no installs
    mock_responses = [
        _make_agg_response(0),    # fb_mobile_install = 0
        _make_agg_response(390),  # fb_mobile_activate_app = 390
    ] + [_make_agg_response(0)] * (_SDK_EVENT_COUNT - 2)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_sdk_installs(date_range="last_7d")

        # Should use activate_app as proxy for installs
        assert result["installs"] == 390
        assert result["source"] == "app_event_aggregations"
        assert result["all_sdk_events"]["fb_mobile_activate_app"] == 390


def test_get_sdk_installs_returns_zero_when_no_app_id(mock_meta_client):
    """Test that no app_id returns zero installs"""
    # Create client without app_id
    client_no_app = MetaAdsIntegration(
        access_token="test_token",
        ad_account_id="123456789",
        app_id=None
    )

    result = client_no_app.get_sdk_installs(date_range="last_7d")

    assert result["installs"] == 0
    assert result["source"] == "no_app_id"


def test_get_total_app_installs(mock_meta_client):
    """Test that get_total_app_installs returns the install count"""

    mock_responses = [_make_agg_response(30)] + [_make_agg_response(0)] * (_SDK_EVENT_COUNT - 1)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        total = mock_meta_client.get_total_app_installs(date_range="last_7d")

        assert total == 30


def test_get_all_sdk_events_returns_all_event_counts(mock_meta_client):
    """Test that get_all_sdk_events returns counts for all SDK event types"""

    mock_responses = [
        _make_agg_response(167),  # fb_mobile_install
        _make_agg_response(390),  # fb_mobile_activate_app
        _make_agg_response(74),   # fb_mobile_content_view
        _make_agg_response(0),    # fb_mobile_purchase
        _make_agg_response(0),    # fb_mobile_add_to_cart
        _make_agg_response(5),    # fb_mobile_complete_registration
    ]

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_all_sdk_events(date_range="last_7d")

        assert result["source"] == "app_event_aggregations"
        assert result["events"]["fb_mobile_install"] == 167
        assert result["events"]["fb_mobile_activate_app"] == 390
        assert result["events"]["fb_mobile_content_view"] == 74
        assert result["events"]["fb_mobile_complete_registration"] == 5
        assert "fb_mobile_purchase" not in result["events"]
        assert result["install_count"] == 167
        assert result["activate_count"] == 390
        assert result["errors"] == []


def test_get_all_sdk_events_logs_errors(mock_meta_client):
    """Test that errors from app_event_aggregations are logged"""

    # All calls fail
    mock_responses = [_make_agg_response(0, status=403)] * _SDK_EVENT_COUNT

    # Ads insights also fails
    mock_ads_response = Mock()
    mock_ads_response.status_code = 200
    mock_ads_response.json.return_value = {"data": []}
    mock_ads_response.raise_for_status.return_value = None
    mock_responses.append(mock_ads_response)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_all_sdk_events(date_range="last_7d")

        # Should have errors logged
        assert len(result["errors"]) > 0
        assert result["events"] == {}


def test_get_all_sdk_events_returns_debug_info(mock_meta_client):
    """Test that _debug diagnostics are included in the result"""

    mock_responses = [
        _make_agg_response(100),  # fb_mobile_install succeeds
        _make_agg_response(0),    # fb_mobile_activate_app succeeds but empty
        _make_agg_response(0, status=403),  # fb_mobile_content_view fails
        _make_agg_response(0),    # fb_mobile_purchase succeeds but empty
        _make_agg_response(0),    # fb_mobile_add_to_cart succeeds but empty
        _make_agg_response(0),    # fb_mobile_complete_registration succeeds but empty
    ]

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_all_sdk_events(date_range="last_7d")

        # Should have debug info
        assert "_debug" in result
        debug = result["_debug"]
        assert debug["agg_attempted"] is True
        assert debug["agg_success"] == 5  # 5 returned HTTP 200
        assert debug["agg_fail"] == 1     # 1 returned HTTP 403
        assert debug["agg_empty"] == 4    # 4 returned 200 but count 0
        assert debug["agg_with_data"] == 1  # 1 had actual data
        assert 403 in debug["agg_fail_statuses"]
        assert debug["app_id"] == "test_app_id"


def test_get_all_sdk_events_no_app_id_reports_error():
    """Test that no app_id produces an error message (not just source flag)"""
    client = MetaAdsIntegration(
        access_token="test_token",
        ad_account_id="123456789",
        app_id=None
    )

    result = client.get_all_sdk_events(date_range="last_7d")

    assert result["source"] == "no_app_id"
    assert len(result["errors"]) == 1
    assert "META_APP_ID" in result["errors"][0]


def test_get_all_sdk_events_all_200_empty_reports_diagnostic(mock_meta_client):
    """Test that when all aggregations return 200 but empty data, a diagnostic error is added"""

    # All 6 return HTTP 200 with empty data
    mock_responses = [_make_agg_response(0)] * _SDK_EVENT_COUNT

    # Ads insights fallback also returns nothing
    mock_ads_response = Mock()
    mock_ads_response.status_code = 200
    mock_ads_response.json.return_value = {"data": []}
    mock_ads_response.raise_for_status.return_value = None
    mock_responses.append(mock_ads_response)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_all_sdk_events(date_range="last_7d")

        # Should report that aggregations returned 200 but no data
        assert result["events"] == {}
        agg_errors = [e for e in result["errors"] if "app_event_aggregations" in e]
        assert len(agg_errors) >= 1
        assert "contagem 0" in agg_errors[0] or "HTTP 200" in agg_errors[0]

        # Debug info should reflect the scenario
        assert result["_debug"]["agg_success"] == 6
        assert result["_debug"]["agg_fail"] == 0
        assert result["_debug"]["agg_empty"] == 6


def test_get_all_sdk_events_all_403_reports_permission_error(mock_meta_client):
    """Test that when all aggregations return 403, a clear permission error is added"""

    # All 6 return HTTP 403
    mock_responses = [_make_agg_response(0, status=403)] * _SDK_EVENT_COUNT

    # Ads insights fallback also returns nothing
    mock_ads_response = Mock()
    mock_ads_response.status_code = 200
    mock_ads_response.json.return_value = {"data": []}
    mock_ads_response.raise_for_status.return_value = None
    mock_responses.append(mock_ads_response)

    with patch('requests.get') as mock_get:
        mock_get.side_effect = mock_responses

        result = mock_meta_client.get_all_sdk_events(date_range="last_7d")

        # Should have per-event errors + summary error
        assert result["events"] == {}
        # 6 per-event errors + 1 summary + 1 fallback error
        assert len(result["errors"]) >= 7
        # Summary error should mention permissions
        summary_errors = [e for e in result["errors"] if "permissões" in e.lower() or "falharam" in e.lower()]
        assert len(summary_errors) >= 1

        # Debug info
        assert result["_debug"]["agg_fail"] == 6
        assert result["_debug"]["agg_success"] == 0
        assert 403 in result["_debug"]["agg_fail_statuses"]


def test_query_app_event_aggregations_includes_http_status(mock_meta_client):
    """Test that _query_app_event_aggregations returns http_status in response"""

    # Success case
    with patch('requests.get') as mock_get:
        mock_get.return_value = _make_agg_response(10)
        resp = mock_meta_client._query_app_event_aggregations("fb_mobile_install", "2024-01-01", "2024-01-07")
        assert resp["http_status"] == 200
        assert resp["success"] is True

    # Error case
    with patch('requests.get') as mock_get:
        mock_get.return_value = _make_agg_response(0, status=403)
        resp = mock_meta_client._query_app_event_aggregations("fb_mobile_install", "2024-01-01", "2024-01-07")
        assert resp["http_status"] == 403
        assert resp["success"] is False
        assert "code=" in resp["error"]


def test_query_app_event_aggregations_exception_has_no_http_status(mock_meta_client):
    """Test that network exceptions return http_status=None"""

    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError("Network error")
        resp = mock_meta_client._query_app_event_aggregations("fb_mobile_install", "2024-01-01", "2024-01-07")
        assert resp["http_status"] is None
        assert resp["success"] is False
        assert "Network error" in resp["error"]
