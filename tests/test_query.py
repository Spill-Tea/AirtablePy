"""
    AirtablePy/test_query.py

"""
# Python Dependencies
import pytest

from .helpers import FAILURE

from AirtablePy import query


@pytest.mark.parametrize("value, expected", [
    ("NOW()", "NOW()"),
    ("date", "'date'"),
    ("CREATED_TIME()", "CREATED_TIME()")
])
def test_formula(value, expected):
    assert query.is_formula(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("CREATED_TIME()", "CREATED_TIME()"),
    ("DATETIME_PARSE(val1, val2)", "DATETIME_PARSE(val1, val2)"),
    ("RECORD_ID()", "RECORD_ID()"),
    ("date", "{date}"),
    ("example", "{example}")
])
def test_column(value, expected):
    assert query.is_column(value) == expected


date_result = "AND(OR(IS_AFTER({date}, '20220814'), IS_SAME({date}, '20220814', 'day')), "
date_result += "OR(IS_BEFORE({date}, '20220817'), IS_SAME({date}, '20220817', 'day')))"


@pytest.mark.parametrize("col, start, end, comp, expected", [
    pytest.param(None, "20220814", "20220817", "day", "", marks=FAILURE),
    pytest.param("column", None, None, "day", "", marks=FAILURE),
    ("date", "20220814", None, "day", "OR(IS_AFTER({date}, '20220814'), IS_SAME({date}, '20220814', 'day'))"),
    ("date", None, "20220817", "day", "OR(IS_BEFORE({date}, '20220817'), IS_SAME({date}, '20220817', 'day'))"),
    ("date", "20220814", "20220817", "day", date_result),
])
def test_date_query(col, start, end, comp, expected):
    assert query.date_query(col, start, end, comp) == expected
