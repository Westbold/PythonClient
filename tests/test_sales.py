import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import ReservationSaleCompact, ReservationSaleExpanded
import datetime


def test_get_all_sales(tv, mock_http_from_disk):
    sales = tv.sales.list()

    sales_list = [x.to_api() for x in sales]
    assert all(
        dict_subset(sale_test, sale_truth) is None
        for sale_test, sale_truth in zip(sales_list, mock_http_from_disk.last_response["data"])
    )


def test_get_sale(tv, mock_http_from_disk):
    sale_id = "string"
    sale = tv.sales.get(sale_id)

    assert isinstance(sale, ReservationSaleExpanded)
    assert dict_subset(sale.to_api(), mock_http_from_disk.last_response) is None
    assert sale.id == sale_id
