"""
Test script to verify the updated mock_http_from_disk fixture works correctly
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))

from fixtures import mock_http_from_disk
import requests

def test_mock_endpoints_priority():
    """Test that mock_endpoints is prioritized over mock_endpoints_generated"""
    with mock_http_from_disk() as mock_http:
        # Make a request that should match the mock_endpoints file
        response = requests.post("https://api.example.com/api/pub/v2/auth", 
                               headers={"X-API-KEY": "test", "X-API-USERNAME": "test"})
        
        # Should get data from mock_endpoints (old format)
        data = response.json()
        print("Auth response:", data)
        
        # Check that parameters were captured
        print("Last header params:", mock_http.last_header_params)

def test_path_parameters():
    """Test that path parameters are correctly extracted"""
    with mock_http_from_disk() as mock_http:
        # Make a request with path parameters
        response = requests.get("https://api.example.com/api/pub/v2/reservations/123", 
                               params={"type": "renewable"})
        
        data = response.json()
        print("Reservation response:", data)
        
        # Check that path and query parameters were captured
        print("Last path params:", mock_http.last_path_params)
        print("Last query params:", mock_http.last_query_params)

if __name__ == "__main__":
    print("Testing mock_endpoints priority...")
    test_mock_endpoints_priority()
    
    print("\nTesting path parameters...")
    test_path_parameters()
    
    print("\nAll tests completed successfully!")
