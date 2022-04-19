"""
    AirtablePy/test_api.py

"""
# Python Dependencies
import json

import pytest
import responses

from .helpers import random_key

from AirtablePy.api import AirtableAPI


# Initial Setup
fake_token = "key" + random_key(14)
mock_base = "app" + random_key(14)
mock_table = "Example Table"
mock_rec = "rec" + random_key(14)
api = AirtableAPI(token=fake_token)
table_url = api.construct_url(mock_base, mock_table)


@responses.activate
def mock_get(url, ret_val, status: int = 200):
    responses.add(responses.GET, url, json=ret_val, status=status)

    resp = api.get(url)
    assert resp == ret_val["records"]
    assert len(responses.calls) == 1
    assert responses.calls[0].response.json() == ret_val
    assert responses.calls[0].response.status_code == status
    assert responses.calls[0].response.text == json.dumps(ret_val)


@pytest.mark.parametrize("url, ret_val, status", [
    (table_url, {"records": [{"id": 123, "fields": {"A": 1, "B": 2}}]}, 200),
    (table_url, {"records": [{"id": 321, "fields": {"C": 3, "D": 4}}]}, 200),
    (table_url, {"records": [{"id": 321, "fields": {"C": 3, "D": 4}}]}, 404),
])
def test_get(url, ret_val, status):
    mock_get(url, ret_val, status)
