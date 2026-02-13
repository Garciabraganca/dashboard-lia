"""
Tests for Meta SDK install counting
Updated to reflect new behavior where SDK installs come from App Events API
(showing total real installs, not just attributed ones)
"""
import pytest
from unittest.mock import Mock, patch
from meta_integration import MetaAdsIntegration


@pytest.fixture
def mock_meta_client():
    """Create a mock Meta Ads client for testing"""
    return MetaAdsIntegration(
        access_token="test_token",
        ad_account_id="123456789",
        app_id="test_app_id"
    )


def test_get_sdk_installs_from_app_event_aggregations(mock_meta_client):
    """Test that SDK installs are fetched from app_event_aggregations as primary source"""
    
    # Mock API response from app_event_aggregations endpoint
    mock_response_data = {
        "data": [
            {"timestamp": "2024-01-01", "value": 50},
            {"timestamp": "2024-01-02", "value": 75},
            {"timestamp": "2024-01-03", "value": 28},
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Call get_sdk_installs
        result = mock_meta_client.get_sdk_installs(date_range="last_7d")
        
        # Should sum all values from app_event_aggregations (50 + 75 + 28 = 153)
        assert result["installs"] == 153
        assert result["source"] == "app_event_aggregations"
        assert result["event_types"] == ["fb_mobile_install"]
        
        # Verify the correct endpoint was called
        call_args = mock_get.call_args
        assert "/app_event_aggregations" in call_args[0][0]


def test_get_sdk_installs_ignores_campaign_filter(mock_meta_client):
    """Test that campaign filter is ignored for SDK installs (returns total) and emits deprecation warning"""
    
    mock_response_data = {
        "data": [
            {"timestamp": "2024-01-01", "value": 100},
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
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
    
    mock_response_data = {
        "data": [
            {"timestamp": "2024-01-15", "value": 42},
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Call with specific date range
        mock_meta_client.get_sdk_installs(
            date_range="custom",
            custom_start="2024-01-01",
            custom_end="2024-01-31"
        )
        
        # Verify the API was called with correct time_range
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        
        # Check that time_range is in params and contains the correct dates
        assert "time_range" in params
        import json
        time_range = json.loads(params["time_range"])
        assert time_range["since"] == "2024-01-01"
        assert time_range["until"] == "2024-01-31"


def test_get_sdk_installs_fallback_to_activities(mock_meta_client):
    """Test fallback to activities endpoint when aggregations fails"""
    
    # Mock activities response
    mock_activities_data = {
        "data": [
            {"event": "fb_mobile_install"},
            {"event": "fb_mobile_install"},
            {"event": "fb_mobile_install"},
        ]
    }
    
    with patch('requests.get') as mock_get:
        # First call (aggregations) returns 404
        # Second call (activities) returns data
        mock_response_agg = Mock()
        mock_response_agg.status_code = 404
        
        mock_response_act = Mock()
        mock_response_act.status_code = 200
        mock_response_act.json.return_value = mock_activities_data
        
        mock_get.side_effect = [mock_response_agg, mock_response_act]
        
        result = mock_meta_client.get_sdk_installs(date_range="last_7d")
        
        # Should use activities fallback and count events
        assert result["installs"] == 3
        assert result["source"] == "app_activities"


def test_get_sdk_installs_fallback_to_ads_insights(mock_meta_client):
    """Test final fallback to ads insights when app events fail"""
    
    # Mock ads insights response (final fallback)
    mock_ads_data = {
        "data": [
            {
                "actions": [
                    {"action_type": "mobile_app_install", "value": "4"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        # First call (aggregations) returns 404
        # Second call (activities) returns 404
        # Third call (ads insights) returns data
        mock_response_agg = Mock()
        mock_response_agg.status_code = 404
        
        mock_response_act = Mock()
        mock_response_act.status_code = 404
        
        mock_response_ads = Mock()
        mock_response_ads.status_code = 200
        mock_response_ads.json.return_value = mock_ads_data
        mock_response_ads.raise_for_status.return_value = None
        
        mock_get.side_effect = [mock_response_agg, mock_response_act, mock_response_ads]
        
        result = mock_meta_client.get_sdk_installs(date_range="last_7d")
        
        # Should use ads insights fallback (attributed installs only)
        assert result["installs"] == 4
        assert result["source"] == "ads_insights_fallback"


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
    
    mock_response_data = {
        "data": [
            {"timestamp": "2024-01-01", "value": 30},
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_get.return_value = mock_response
        
        # Call get_total_app_installs
        total = mock_meta_client.get_total_app_installs(date_range="last_7d")
        
        # Should return the install count
        assert total == 30
