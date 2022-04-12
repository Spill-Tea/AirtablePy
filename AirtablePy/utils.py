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

from typing import Any, Union
from pandas import DataFrame


# Global Variables
_VALID_KEY_PREFIX = {
    "API Key": "key",
    "Base ID": "app",
    "Record ID": "rec",
}


def convert_upload(data: Union[dict, DataFrame], typecast: bool = True) -> dict:
    """Returns the Corrected pre-json Formatted dictionary from data.

    Args:
        data (dict | pd.DataFrame): Data for a Single Record where the Keys are organized by column.
        typecast (bool): Data is coerced to correct type during upload if True (Recommended).

    Returns:
        (dict) Data as a dictionary in correct airtable pre-json format suitable to upload
        to airtable after json.dumps().

    Raises:
        ValueError: Invalid Data Type (i.e. not dict or DataFrame)

    """
    if isinstance(data, dict):
        return {"records": [{"fields": data}], "typecast": typecast}

    elif isinstance(data, DataFrame):
        return {"records": [{"fields": data.to_dict(orient="records")[0]}], "typecast": typecast}

    else:
        raise ValueError(f"Invalid Data Format for Upload: {type(data)}")


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
    if key is None or not isinstance(key, str):
        raise ValueError(f"Invalid Key Type: {key} ({type(key)})")

    if len(key) != 17:
        raise ValueError(f"Valid Airtable API Keys are 17 Characters in Length: {key}")

    try:
        prefix = _VALID_KEY_PREFIX[key_type]
    except KeyError as e:
        raise ValueError(e, f"Unsupported KeyType used for Validation: {key_type}")

    if not key.startswith(prefix):
        raise ValueError(f"Invalid Key Formatting: {key} must begin with {prefix}")


def get_key(response: Union[requests.models.Response, dict], key: str) -> Any:
    """Returns a Specific Key Value from a response or from a converted dictionary thereof."""
    try:
        return response.json().get(key)

    except AttributeError:
        return response.get(key)


def inject_record_id(data: dict, record_id: str) -> None:
    """Injects the RecordID inplace into a formatted dictionary to update an existing record.

    Args:
        data (dict): formatted data dictionary
        record_id (str): Airtable Record ID

    Returns:
        (None)

    """
    check_key(record_id, "Record ID")
    get_key(data, "records")[0].update({"id": record_id})


def get_response(session: requests.Session, method: str, **kwargs) -> requests.models.Response:
    """Interfaces between Request sessions or requests library and appropriate methods."""
    try:
        return getattr(session, method)(**kwargs)

    except AttributeError:
        return getattr(requests, method)(**kwargs)
