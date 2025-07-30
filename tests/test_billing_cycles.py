import pytest
from .fixtures import tv, mock_http_from_disk, mock_http, dict_subset
from textverified.textverified import TextVerified, BearerToken
from textverified.action import _Action
from textverified.data import (
    Account,
    BillingCycleExpanded,
    BillingCycleRenewalInvoice,
    BillingCycleRenewalInvoicePreview,
)
import datetime


def test_get_all_billing_cycles(tv, mock_http_from_disk):
    billing_cycle_obj = tv.billing_cycles.list()

    billing_cycles_list = [x.to_api() for x in billing_cycle_obj]
    assert billing_cycles_list == mock_http_from_disk.last_response.get("data", [])


def test_get_billing_cycle(tv, mock_http_from_disk):
    billing_cycle_id = "string"
    billing_cycle_obj = tv.billing_cycles.get(billing_cycle_id)

    assert isinstance(billing_cycle_obj, BillingCycleExpanded)
    assert dict_subset(billing_cycle_obj.to_api(), mock_http_from_disk.last_response) is None
    assert billing_cycle_obj.id == billing_cycle_id


def test_update_billing_cycle_by_id(tv, mock_http_from_disk):
    billing_cycle_id = "string"

    result = tv.billing_cycles.update(billing_cycle_id, reminders_enabled=True)

    assert result is True
    assert mock_http_from_disk.last_body_params["remindersEnabled"] is True


def test_update_billing_cycle_by_instance(tv, mock_http_from_disk):
    test_get_billing_cycle(tv, mock_http_from_disk)  # Load the billing cycle
    billing_cycle = BillingCycleExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.billing_cycles.update(billing_cycle, reminders_enabled=False, nickname="New Nickname")

    assert result is True
    assert mock_http_from_disk.last_body_params["remindersEnabled"] is False
    assert mock_http_from_disk.last_body_params["nickname"] == "New Nickname"


def test_get_billing_invoices_by_id(tv, mock_http_from_disk):
    billing_cycle_id = "string"

    invoices = tv.billing_cycles.invoices(billing_cycle_id)

    invoices_list = [x.to_api() for x in invoices]
    assert all(
        dict_subset(invoice_test, invoice_truth) is None
        for invoice_test, invoice_truth in zip(invoices_list, mock_http_from_disk.last_response["data"])
    )


def test_get_billing_invoices_by_instance(tv, mock_http_from_disk):
    test_get_billing_cycle(tv, mock_http_from_disk)  # Load the billing cycle
    billing_cycle = BillingCycleExpanded.from_api(mock_http_from_disk.last_response)

    invoices = tv.billing_cycles.invoices(billing_cycle)

    invoices_list = [x.to_api() for x in invoices]
    assert all(
        dict_subset(invoice_test, invoice_truth) is None
        for invoice_test, invoice_truth in zip(invoices_list, mock_http_from_disk.last_response["data"])
    )


def test_preview_next_billing_cycle_by_id(tv, mock_http_from_disk):
    billing_cycle_id = "string"

    preview = tv.billing_cycles.preview(billing_cycle_id)

    assert isinstance(preview, BillingCycleRenewalInvoicePreview)
    assert dict_subset(preview.to_api(), mock_http_from_disk.last_response) == None


def test_preview_next_billing_cycle_by_instance(tv, mock_http_from_disk):
    test_get_billing_cycle(tv, mock_http_from_disk)  # Load the billing cycle
    billing_cycle = BillingCycleExpanded.from_api(mock_http_from_disk.last_response)

    preview = tv.billing_cycles.preview(billing_cycle)

    assert isinstance(preview, BillingCycleRenewalInvoicePreview)
    assert dict_subset(preview.to_api(), mock_http_from_disk.last_response) == None


def test_renew_billing_cycle_by_id(tv, mock_http_from_disk):
    billing_cycle_id = "string"

    result = tv.billing_cycles.renew(billing_cycle_id)

    assert result is True


def test_renew_billing_cycle_by_instance(tv, mock_http_from_disk):
    test_get_billing_cycle(tv, mock_http_from_disk)  # Load the billing cycle
    billing_cycle = BillingCycleExpanded.from_api(mock_http_from_disk.last_response)

    result = tv.billing_cycles.renew(billing_cycle)

    assert result is True
