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
import yaml
from pathlib import Path
from typing import Any, Optional


with Path(__file__).parent.joinpath("airtable_filters.yml").open("r") as f:
    formulas = yaml.load(f, Loader=yaml.SafeLoader)


def _check_formula(value: Any) -> bool:
    if value in formulas["fields"]["no args"]:
        return True

    for i in formulas["fields"]["args"]:
        if value.startswith(i):
            return True

    return False


def is_formula(value: Any) -> Any:
    """Checks if value is an Airtable Formula (one which does not require arguments) or int/float."""
    if isinstance(value, (int, float)) or _check_formula(value):
        return value

    return f"{value!r}"


def is_column(value: str) -> Any:
    """Checks if value is an Airtable Formula (which refers to a field, or modifications thereof)."""
    if _check_formula(value):
        return value
    return "{%s}" % value


def merge_queries(kind: str, /, *args):
    """Creates an AND / OR / NOT Query."""
    kind = kind.upper()
    assert kind in ["OR", "AND", "NOT"]
    if kind == "NOT" and len(args) != 1:
        raise ValueError(f"NOT Queries only take one argument: {args}")
    return f"{kind}({', '.join(args)})"


def arithmetic(column: str, comparison: str, value: Any) -> str:
    """Constructs an arithmetic Operator Comparison Query.

    Args:
        column (str): column name
        comparison (str): Arithmetic operator: "<" | "<=" | "=" | "!=" | ">=" | ">"
        value (Any): value to compare to

    Returns:
        (str) airtable formatted operator query

    Notes:
        - "!=" operator may not work as expected here. Consider using NOT() query instead.

    """
    return f"{is_column(column)} {comparison} {is_formula(value)}"


def date_query(column_name: str,
               start: Optional[str] = None,
               end: Optional[str] = None,
               comparison: str = "day"
               ) -> str:
    """Constructs an Inclusive Date Query.

    Args:
        column_name (str): Name of Column in a table Defining a Date
        start (str): Optional Arg indicating Start Date (Inclusive).
        end (str): Optional Arg indication End Date (Inclusive)
        comparison (str): Defines the truth of date equality is discerned
            - Options: "second" | "hour" | "day" | "month" | "year"

    Returns:
        (str) Complete Airtable Compatible Date Query

    Notes:
        The Date may be provided in the following formats:
            - YYYYMMDD HH:MM:SS.0
            - MM/DD/YYYY HH:MM:SS.0

    Raises:
        - ValueError: When a column name is not defined
        - ValueError: When neither a start nor end date is defined.

    """
    # Sanity Checks
    if column_name is None:
        raise ValueError(f"Must Define a Column Name: {column_name}")
    if start is None and end is None:
        raise ValueError(f"Must Define Either Start or End Dates.")
    if comparison not in ["second", "hour", "day", "month", "year"]:
        raise ValueError(f"Invalid Comparison: {comparison}")

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
