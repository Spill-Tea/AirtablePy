# MIT License
#
# Copyright (c) 2022 Spill-Tea
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""""
    AirtablePy/query.py

    Helper tools to construct Airtable queries

"""""
# Python Dependencies
from typing import Optional


def is_formula(value: str):
    """Checks if value is an Airtable Formula (one which does not require arguments)."""
    if value in ["NOW()", "TODAY()", "FALSE()", "TRUE()", "CREATED_TIME()", "RECORD_ID()", "ERROR()", "BLANK()"]:
        return value
    return f"{value!r}"


def is_column(value: str):
    """Checks if value is an Airtable Formula (which refers to a field, or modifications thereof)."""
    special = ["CREATED_TIME()", "RECORD_ID()", "DATETIME_PARSE("]
    if any([value.startswith(i) for i in special]):
        return value
    return "{%s}" % value


def merge_queries(kind: str, /, *args):
    """Create an AND / OR Query"""
    assert kind.upper() in ["OR", "AND"]
    return f"{kind.upper()}({', '.join(args)})"


def date_query(column_name: str,
               start: Optional[str] = None,
               end: Optional[str] = None,
               comparison: str = "day"
               ):
    """Constructs an Inclusive Date Query.

    Args:
        column_name (str): Name of Column in a table Defining a Date
        start (str): Optional Arg indicating Start Date (Inclusive).
        end (str): Optional Arg indication End Date (Inclusive)
        comparison (str): Defines how truth of date equality are compared

    Returns:
        (str) Complete Airtable Compatible Date Query

    Notes:
        The Date may be provided in the following formats:
            - YYYYMMDD HH:MM:SS.0
            - MM/DD/YYY HH:MM:SS.0

    Raises:
        - ValueError: When a column name is not defined
        - ValueError: When neither a start or end date is not defined.

    """
    # Sanity Checks
    if column_name is None:
        raise ValueError(f"Must Define a Column Name: {column_name}")
    if start is None and end is None:
        raise ValueError(f"Must Define Either Start or End Dates: {start} - {end}")

    column = is_column(column_name)

    if start:
        _start = (column, is_formula(start))
        a = "IS_AFTER(%s, %s)" % _start
        b = "IS_SAME(%s, %s, %s)" % (_start + (f"{comparison!r}",))
        start = merge_queries("OR", a, b)

    if end:
        _end = (column, is_formula(end))
        a = "IS_BEFORE(%s, %s)" % _end
        b = "IS_SAME(%s, %s, %s)" % (_end + (f"{comparison!r}",))
        end = merge_queries("OR", a, b)

    if start and end:
        return merge_queries("AND", start, end)

    return start or end
