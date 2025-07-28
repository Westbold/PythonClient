import pytest
from unittest.mock import Mock, patch
import json
import os
from pathlib import Path
from unittest.mock import MagicMock
from requests import Response
from textverified.textverified import TextVerified, BearerToken
import datetime
import glob
import re
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional
from itertools import chain

@pytest.fixture
def tv_raw() -> TextVerified:
    """
    Build a mock TextVerified client with nothing set
    """
    return TextVerified(api_key="test-key", api_username="test-user")

@pytest.fixture
def tv() -> TextVerified:
    """
    Build a mock TextVerified client with a "valid" bearer token
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

def _create_mock_response(response_data):
    """Create a mock response object from response data"""
    mock_response = MagicMock(spec=Response)
    
    # Handle both old format (data key) and new format (response key)
    if "response" in response_data:
        mock_response.json.return_value = response_data["response"]
    else:
        mock_response.json.return_value = {}
        
    mock_response.status_code = response_data.get("status_code", 200)
    mock_response.headers = response_data.get("headers", {})
    mock_response.raise_for_status.return_value = None
    
    return mock_response

def _find_mock_file(request_path: str, file_list: List[Path]) -> Optional[Dict]:
    """Find mock file, supporting path parameters with glob patterns"""
    # Convert to request filename
    request_filename = request_path[request_path.find('://') + 3:]  # Remove scheme
    request_filename = re.sub(r'^[^\/]*\/', '', request_filename) # Remove leading path
    request_filename = request_filename.replace("/", ".").lstrip(".")
    request_filename = re.sub(r'\?.*$', '', request_filename)  # Remove query params
    query_params = parse_qs(urlparse(request_path).query)
    
    for file_path in file_list:
        # Convert possible target to regex pattern
        file_name = file_path.name
        file_name = file_name[:file_name.rfind('.')] # Remove .json extension
        path_param_keys   = re.findall(r'\{([^}]+)\}', str(file_name)) # 1 group per key of path parameters
        file_path_pattern = re.sub(r'\{([^}]+)\}', '.*?', str(file_name)) # file path with 1 group for each path parameter
                
        if re.fullmatch(file_path_pattern, request_filename):
            return {
                "path": file_path,
                "query_params": query_params,
                "path_params": dict(zip(path_param_keys, re.findall(file_path_pattern, request_filename)))
            }
    return None

def _load_mock_data(mock_file_path, method):
    """Load and validate mock data from file"""
    try:
        with open(mock_file_path, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in mock file {mock_file_path}: {e}")
    
    method_lower = method.lower()
    if method_lower not in mock_data:
        raise KeyError(f"No mock data for {method.upper()} method in {mock_file_path}. Available methods: {list(mock_data.keys())}")
    
    return mock_data[method_lower]

@pytest.fixture
def mock_http_from_disk():
    """
    Pytest fixture that intercepts HTTP requests and loads data from tests/mock_endpoints (preferred)
    or tests/mock_endpoints_generated (if not found in the first).
    
    Files are laid out as HTTP paths with / replaced with .
    For example: /api/pub/v2/auth becomes api.pub.v2.auth.json
    Path parameters like {id} are supported.
    
    Each mock file should contain JSON with HTTP methods as keys:
    {
        "get": { 
            "path_params": {"id": "value"},
            "query_params": {"param": "value"}, 
            "header_params": {"header": "value"},
            "response": {...} 
        }
    }
    """
    # Get the tests directory path
    tests_dir = Path(__file__).parent
    mock_dirs = [tests_dir / "mock_endpoints", tests_dir / "mock_endpoints_generated"]
    mock_files = list(chain.from_iterable(mock_dir.iterdir() for mock_dir in mock_dirs if mock_dir.exists()))

    def mock_request(method, url, **kwargs):
        """Mock implementation for requests.Session.request"""
        # Parse URL and extract parameters
        mock_file_data = _find_mock_file(url, mock_files)
        if not mock_file_data:
            raise FileNotFoundError(f"No mock data found for {method.upper()} {url}. Searched in {mock_dirs}")
        
        # Load mock data
        response_data = _load_mock_data(mock_file_data.get("path"), method)
        
        # Load incoming headers
        extracted_header_params = kwargs.get("headers", {})
        if isinstance(extracted_header_params, dict):
            extracted_header_params = {k.lower(): v for k, v in extracted_header_params.items() if v is not None}
        
        # Store parameters for test verification
        mock_request.last_path_params = mock_file_data.get("path_params", {})
        mock_request.last_query_params = mock_file_data.get("query_params", {})
        mock_request.last_header_params = extracted_header_params

        return _create_mock_response(response_data)
    
    # Patch the requests.Session.request method
    with patch('requests.Session.request', side_effect=mock_request) as mock:
        # Add parameter access methods to the mock
        mock.last_path_params = {}
        mock.last_query_params = {}
        mock.last_header_params = {}
        yield mock