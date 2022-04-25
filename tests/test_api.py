"""
    AirtablePy/test_api.py

"""
# Python Dependencies
import json

import pytest
import responses

from .helpers import random_key
from AirtablePy import AirtableAPI


# Initial Setup
fake_token = "key" + random_key(14)
mock_base = "app" + random_key(14)
mock_table = "ExampleTable"
mock_rec = "rec" + random_key(14)
api = AirtableAPI(token=fake_token)
table_url = api.construct_url(mock_base, mock_table)

method_map = {
    responses.GET: "get",
    responses.POST: "push",
    responses.PATCH: "update",
    responses.PUT: "replace",
    responses.DELETE: "delete",
}


@responses.activate
def mock_request(url, ret_val, method, status: int = 200, **kwargs):
    """This only simulates single requests (not batching)."""
    original_url = url
    if method == responses.DELETE:
        # the delete method modifies the input url, on a single request, so we must adjust.
        recid = kwargs["record_id"][0]
        url = f"{url}{recid}" if url.endswith("/") else f"{url}/{recid}"

    responses.add(method, url, json=ret_val, status=status)

    resp = getattr(api, method_map[method])(original_url, **kwargs)
    assert len(responses.calls) == 1
    assert responses.calls[0].response.json() == ret_val
    assert responses.calls[0].response.status_code == status
    assert responses.calls[0].response.text == json.dumps(ret_val)

    if method == responses.GET:
        assert resp == ret_val["records"]

    elif method != responses.DELETE:
        assert resp[0].json() == ret_val
        assert resp[0].json()["records"][0]["fields"] == kwargs["data"]

    else:
        assert resp[0].json()["records"][0]["deleted"] is True
        assert resp[0].json()["records"][0]["id"] == recid


@pytest.mark.parametrize("url, ret_val, method, status, kwargs", [
    (table_url, {"records": [{"id": mock_rec, "fields": {"A": 1, "B": 2}}]}, responses.GET, 200, {}),
    (table_url, {"records": [{"id": mock_rec, "fields": {"C": 3, "D": 4}}]}, responses.GET, 200, {}),
    (table_url, {"records": [{"id": mock_rec, "fields": {"C": 3, "D": 4}}]}, responses.GET, 404, {}),
    (table_url, {"records": [{"id": mock_rec, "fields": {"C": 3, "D": 4}}]}, responses.POST, 200, dict(data={"C": 3, "D": 4})),
    (table_url, {"records": [{"id": mock_rec, "fields": {"C": 3, "D": 4}}]}, responses.PATCH, 200, dict(data={"C": 3, "D": 4}, record_id=[mock_rec])),
    (table_url, {"records": [{"id": mock_rec, "fields": {"C": 3, "D": 4}}]}, responses.PUT, 200, dict(data={"C": 3, "D": 4}, record_id=[mock_rec])),
    (table_url, {"records": [{"deleted": True, "id": mock_rec}]}, responses.DELETE, 200, dict(record_id=[mock_rec])),
])
def test_api(url, ret_val, method, status, kwargs):
    mock_request(url, ret_val, method, status, **kwargs)

