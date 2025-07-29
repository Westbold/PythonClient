import pytest
from .fixtures import tv, mock_http_from_disk
from textverified.textverified import TextVerified, BearerToken
from textverified.paginated_list import PaginatedList
from textverified.action import _Action
import datetime
import json

list_initial_response = {
    "data": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}],
    "hasNext": True,
    "links": {"next": {"method": "GET", "href": "/api/pub/v2/list/page2"}},
}


def test_paginated_list_calls_parse_func(tv):
    list_response = json.loads(json.dumps(list_initial_response))
    list_response["hasNext"] = False
    list_response["links"]["next"]["method"] = None
    list_response["links"]["next"]["href"] = None

    list_instance = PaginatedList(request_json=list_response, parse_item=lambda item: item["name"], api_context=tv)

    assert list(list_instance) == ["Item 1", "Item 2"]


def test_paginated_list_next_page(tv, mock_http_from_disk):
    list_instance = PaginatedList(
        request_json=list_initial_response, parse_item=lambda item: item["name"], api_context=tv
    )

    items = list(list_instance)
    assert items == ["Item 1", "Item 2", "Item 3", "Item 4"]


def test_paginated_list_item_access(tv, mock_http_from_disk):
    list_instance = PaginatedList(
        request_json=list_initial_response, parse_item=lambda item: item["name"], api_context=tv
    )

    assert list_instance[2] == "Item 3"
    assert list_instance[1] == "Item 2"
    with pytest.raises(IndexError):
        _ = list_instance[4]  # Should raise IndexError for out of range access


def test_paginated_list_lazy(tv, mock_http_from_disk):
    list_instance = PaginatedList(
        request_json=list_initial_response, parse_item=lambda item: item["name"], api_context=tv
    )

    assert mock_http_from_disk.call_count == 0  # No requests made yet

    # Exhaust page 1
    assert next(list_instance) == "Item 1"
    assert next(list_instance) == "Item 2"

    assert mock_http_from_disk.call_count == 0  # Haven't fetched next page yet

    assert next(list_instance) == "Item 3"  # Triggers next page fetch
    assert mock_http_from_disk.call_count == 1


def test_paginated_list_get_all(tv, mock_http_from_disk):
    list_instance = PaginatedList(
        request_json=list_initial_response, parse_item=lambda item: item["name"], api_context=tv
    )

    all_items = list_instance.get_all_items()
    assert all_items == ["Item 1", "Item 2", "Item 3", "Item 4"]
    assert mock_http_from_disk.call_count == 1
