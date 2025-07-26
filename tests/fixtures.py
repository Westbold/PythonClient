import pytest
from unittest.mock import Mock, patch
import json
import os
from pathlib import Path
from unittest.mock import MagicMock
from requests import Response
from textverified.textverified import TextVerified, BearerToken
import datetime

@pytest.fixture
def tv() -> TextVerified:
    """
    Build a mock TextVerified client
    """
    return TextVerified(api_key="test-key", api_username="test-user")

@pytest.fixture
def tv_valid_bearer() -> TextVerified:
    """
    Build a mock TextVerified client with a valid bearer token
    """
    tv = TextVerified(api_key="test-key", api_username="test-user")
    tv.bearer = BearerToken(
        "valid-token",
        expires_at=datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=3600)
    )
    return tv

@pytest.fixture
def mock_http():
    """
    Pytest fixture that intercepts HTTP requests and returns a mock response.
    """
    with patch('requests.Session.request') as mock_request:
        yield mock_request
    
@pytest.fixture
def mock_http_from_disk():
    """
    Pytest fixture that intercepts HTTP requests and loads data from tests/mock_endpoints.
    
    Files are laid out as HTTP paths with / replaced with .
    For example: /api/pub/v2/auth becomes api.pub.v2.auth
    
    Each mock file should contain JSON with HTTP methods as keys:
    {
        "get": { "data": {...} },
        "post": { "data": {...} }
    }
    """
    # Get the tests directory path
    tests_dir = Path(__file__).parent
    mock_endpoints_dir = tests_dir / "mock_endpoints"
    
    def mock_request(method, url, **kwargs):
        """Mock implementation for requests.Session.request"""
        # Extract the path from the URL
        # Remove base URL if present (e.g., "https://www.textverified.com/api/pub/v2/auth" -> "/api/pub/v2/auth")
        if "://" in url:
            path = "/" + url.split("://", 1)[1].split("/", 1)[1]
        else:
            path = url
        
        # Convert path to filename (remove leading slash and replace remaining slashes with dots)
        if path.startswith("/"):
            path = path[1:]
        filename = path.replace("/", ".")
        
        # Look for the mock file
        mock_file_path = mock_endpoints_dir / filename
        
        if not mock_file_path.exists():
            # If no mock file exists, raise an exception to indicate missing mock data
            raise FileNotFoundError(f"No mock data found for {method.upper()} {url}. Expected file: {mock_file_path}")
        
        # Load the mock data
        try:
            with open(mock_file_path, 'r', encoding='utf-8') as f:
                mock_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in mock file {mock_file_path}: {e}")
        
        # Get the data for the specific HTTP method
        method_lower = method.lower()
        if method_lower not in mock_data:
            raise KeyError(f"No mock data for {method.upper()} method in {mock_file_path}. Available methods: {list(mock_data.keys())}")
        
        response_data = mock_data[method_lower]
        
        # Create a mock response object
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = response_data.get("data", {})
        mock_response.status_code = response_data.get("status_code", 200)
        mock_response.headers = response_data.get("headers", {})
        mock_response.raise_for_status.return_value = None
        
        return mock_response
    
    # Patch the requests.Session.request method
    with patch('requests.Session.request', side_effect=mock_request) as mock:
        yield mock