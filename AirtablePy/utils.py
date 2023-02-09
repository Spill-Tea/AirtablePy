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
"""
    AirtablePy/utils.py

"""
# Python Dependencies
import requests
from dataclasses import dataclass
from typing import Any, Iterator, List, Union
from pandas import DataFrame


@dataclass
class ValidKeyPrefix:
    """Valid Prefix for Airtable Keys"""
    key = "key"
    base = "app"
    record = "rec"


def convert_upload(data: Union[dict, DataFrame], typecast: bool, limit: int = 10) -> List[dict]:
    """Returns the Corrected pre-json Formatted dictionary from data.

    Args:
        data (dict | pd.DataFrame): Data for a Single Record where the Keys are organized by column.
        typecast (bool): Data is coerced to correct type during upload if True (Recommended).
        limit (int): number of records per parcel (i.e. api rate limit)

    Returns:
        (list) Data as a list of chunked out dictionary record fields in correct airtable pre-json
        format suitable for batch upload to airtable after json.dumps().

    Raises:
        ValueError: Invalid Data Type (i.e. not dict or DataFrame)

    """
    if isinstance(data, dict):
        try:
            # format: {col1: [v1, v2, v3, ...], col2: [v1, v2, v3, ...], ...}
            data = DataFrame(data)
        except ValueError:
            # format: {col1: value1, col2: value2, ...}
            return [construct_record([data], typecast)]

    if isinstance(data, DataFrame):
        return [construct_record(i, typecast) for i in parcels(data.to_dict("records"), limit)]

    else:
        raise ValueError(f"Invalid Data Format for Upload: {type(data)}")


def parcels(iterable: list, chunks: int = 10) -> Iterator[List[dict]]:
    """Meters out an iterable object by defined chunk size (i.e. api upload limit)"""
    for i in range(0, len(iterable), chunks):
        yield iterable[i: i + chunks]


def construct_record(chunk: List[dict], typecast: bool) -> dict:
    """Transforms data to prepare for load to airtable."""
    return {"records": [{"fields": i} for i in chunk], "typecast": typecast}


def check_key(key: str, key_type: str) -> None:
    """Validates an Airtable Key Type.

    Args:
        key (str): AirtableID or Key
        key_type (str): Defines type of key to validate ("API Key" | "Base ID" | "Record ID")

    Raises:
        ValueError: Invalid Key Type or Formatting

    Returns:
        (None) when key meets formatting conventions.

    """
    if not isinstance(key, str):
        raise ValueError(f"Invalid Key Type: {key} ({type(key)})")

    if len(key) != 17:
        raise ValueError(f"Valid Airtable API Keys are 17 Characters in Length: {key}")

    try:
        prefix = getattr(ValidKeyPrefix, key_type)
    except AttributeError as e:
        raise ValueError(e, f"Unsupported KeyType used for Validation: {key_type}")

    if not key.startswith(prefix):
        raise ValueError(f"Invalid Key Formatting: {key} must begin with {prefix}")


def get_key(response: Union[requests.models.Response, dict], key: str) -> Any:
    """Returns a Specific Key Value from a response or from a converted dictionary thereof."""
    try:
        return response.json().get(key)

    except AttributeError:
        return response.get(key)


def retrieve_keys(response: List[requests.models.Response], key: str) -> list:
    """Retrieves a key from a list of requests.

    Args:
        response (list): list of request responses.
        key (str): valid key from response. e.g. "id", "createdTime" or "fields"

    Returns:
        (list) list of key values from a list of responses

    """
    return [rec[key] for r in response for rec in get_key(r, "records")]


def inject_record_id(data: dict, record_id: str, index: int = 0) -> None:
    """Injects the RecordID inplace into a formatted dictionary to update an existing record.

    Args:
        data (dict): formatted data dictionary
        record_id (str): Airtable Record ID
        index (int): Index of record to inject (important in batches)

    Returns:
        (None) the data is modified inplace to include the record id.

    """
    check_key(record_id, "record")
    get_key(data, "records")[index].update({"id": record_id})


def from_records(data: List[dict]) -> DataFrame:
    """Converts data from a list or records into a dataframe."""
    records = []
    for d in data:
        temp = get_key(d, "fields")
        temp.update({key: get_key(d, key) for key in ["id", "createdTime"]})
        records.append(temp)

    return DataFrame.from_records(records)
