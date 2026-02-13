"""
Tests for Meta SDK install counting with campaign filtering
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


def test_get_sdk_installs_filters_by_campaign(mock_meta_client):
    """Test that SDK installs are filtered by campaign when filter is provided"""
    
    # Mock API response with multiple campaigns
    mock_response_data = {
        "data": [
            {
                "campaign_name": "LIA App Install Campaign",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "15"}
                ]
            },
            {
                "campaign_name": "Other Campaign",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "25"}
                ]
            },
            {
                "campaign_name": "LIA Remarketing",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "10"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with campaign filter for "LIA"
        result = mock_meta_client.get_sdk_installs(
            date_range="last_7d",
            campaign_name_filter="LIA"
        )
        
        # Should only count installs from campaigns containing "LIA" (15 + 10 = 25)
        assert result["installs"] == 25
        assert result["source"] == "ads_insights_campaign"
        assert "mobile_app_install" in result["event_types"]


def test_get_sdk_installs_without_filter_counts_all(mock_meta_client):
    """Test that SDK installs count all campaigns when no filter is provided"""
    
    mock_response_data = {
        "data": [
            {
                "campaign_name": "Campaign A",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "15"}
                ]
            },
            {
                "campaign_name": "Campaign B",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "25"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test without campaign filter
        result = mock_meta_client.get_sdk_installs(
            date_range="last_7d",
            campaign_name_filter=None
        )
        
        # Should count all installs (15 + 25 = 40)
        assert result["installs"] == 40
        assert result["source"] == "ads_insights_account"


def test_get_sdk_installs_respects_date_range(mock_meta_client):
    """Test that date range is properly applied in the API request"""
    
    # Mock response with data to prevent fallback to activities endpoint
    mock_response_data = {
        "data": [
            {
                "campaign_name": "Test Campaign",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "10"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
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


def test_get_sdk_installs_uses_campaign_level(mock_meta_client):
    """Test that API request uses campaign level for proper filtering"""
    
    # Mock response with data to prevent fallback
    mock_response_data = {
        "data": [
            {
                "campaign_name": "Test Campaign",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "5"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call get_sdk_installs
        mock_meta_client.get_sdk_installs(date_range="last_7d")
        
        # Verify the API was called with level="campaign"
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        
        assert params["level"] == "campaign"
        assert "campaign_name" in params["fields"]


def test_get_total_app_installs_passes_campaign_filter(mock_meta_client):
    """Test that get_total_app_installs properly passes campaign filter"""
    
    mock_response_data = {
        "data": [
            {
                "campaign_name": "Test Campaign",
                "actions": [
                    {"action_type": "mobile_app_install", "value": "30"}
                ]
            }
        ]
    }
    
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call get_total_app_installs with campaign filter
        total = mock_meta_client.get_total_app_installs(
            date_range="last_7d",
            campaign_name_filter="Test"
        )
        
        # Should return the filtered count
        assert total == 30
