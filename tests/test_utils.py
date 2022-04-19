"""
    AirtablePy/test_utils.py

"""
# Python Dependencies
import pytest
from random import choices
from string import ascii_letters

from AirtablePy import utils


# Global Variable
FAILURE = pytest.mark.xfail(raises=ValueError)


def random_key(length: int) -> str:
    return "".join(choices(ascii_letters, k=length))


@pytest.mark.parametrize("key, n, _type", [
    ("app", 14, "Base ID"),
    ("key", 14, "API Key"),
    ("rec", 14, "Record ID"),
    pytest.param("app", 13, "Base ID", marks=FAILURE),
    pytest.param("app", 15, "Base ID", marks=FAILURE),
    pytest.param("xxx", 14, "Base ID", marks=FAILURE),
    pytest.param("key", 13, "API Key", marks=FAILURE),
    pytest.param("key", 17, "API Key", marks=FAILURE),
    pytest.param("tea", 14, "API Key", marks=FAILURE),
    pytest.param("rec", 13, "Record ID", marks=FAILURE),
    pytest.param("rec", 18, "Record ID", marks=FAILURE),
    pytest.param("", 17, "Invalid", marks=FAILURE),
    pytest.param("", 17, "Test", marks=FAILURE),
])
def test_check_key(key, n, _type):
    assert utils.check_key(f"{key}{random_key(n)}", _type) is None


@pytest.mark.parametrize("data, typecast, expected", [
    ([{"A": 1, "B": 2}], True, {"records": [{"fields": {"A": 1, "B": 2}}], "typecast": True}),
    ([{"A": 1, "B": 2}], False, {"records": [{"fields": {"A": 1, "B": 2}}], "typecast": False}),
])
def test_construct_record(data, typecast, expected):
    ret_val = utils.construct_record(data, typecast)
    assert ret_val["records"][0]["fields"] == data[0]
    assert ret_val["typecast"] == typecast
    assert ret_val == expected
