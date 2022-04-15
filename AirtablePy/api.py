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
    AirtablePy/api.py

"""
# Python Dependencies
import os
import json
import requests

from io import StringIO
from typing import List, Optional, Tuple, Union
from pandas import DataFrame

from .utils import check_key
from .utils import get_key
from .utils import get_response
from .utils import convert_upload
from .utils import inject_record_id


class AirtableAPI:
    """Airtable API to retrieve, push, update, replace, and delete Airtable Records.

    Args:
        token (str): Airtable API authorization token
        timeout (Tuple[float, float] | float): timeout specification for connecting and reading
            requests. See the following for more details:
                - https://docs.python-requests.org/en/master/user/advanced/#timeouts
        version (str): API version (currently v0 by default)
        environment_variable (str): Environment Variable to retrieve if token is None.

    """

    def __init__(self,
                 token: Optional[str] = None,
                 timeout: Optional[Union[Tuple[float, float], float]] = None,
                 environment_variable: str = "AIRTABLE_AUTH_TOKEN",
                 version: str = "v0",
                 ) -> None:
        self._token = token or os.getenv(environment_variable)
        check_key(self._token, "API Key")

        self.timeout = timeout
        self._header = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        self.base_url = f"https://api.airtable.com/{version}/"

    def construct_url(self, base_id: str, table_id: str, record_id: Optional[str] = None) -> str:
        """Constructs a Valid Airtable API Link either to a table or record.

        Args:
            base_id (str): Valid BaseID (17 Characters and starts with `app`)
            table_id (str): TableID or Table Name
            record_id (str): Valid recordID (Optional)

        Returns:
            (str) Completed Airtable API link

        """
        check_key(key=base_id, key_type="Base ID")

        if record_id:
            check_key(key=record_id, key_type="Record ID")
            return f"{self.base_url}{base_id}/{table_id}/{record_id}"

        return f"{self.base_url}{base_id}/{table_id}"

    def get(self,
            url: str,
            n_records: Optional[int] = None,
            offset: Optional[str] = None,
            query: Optional[str] = None,
            fields: Optional[List[str]] = None,
            **kwargs
            ) -> List[dict]:
        """Iteratively Retrieve all Records from a given Table.

        Args:
            url (str): Valid Airtable link
            n_records (int): Optional Number of Records to retrieve (If None, all are retrieved)
            offset (str): Optional Number of Records to offset to retrieve.
            query (str): Optional A Valid Airtable Formatted Query to filter results
            fields (list): Optional list of column names to limit return

        Returns:
            (list) A List of Dictionary Records from a give table

        """
        data = []

        with requests.session() as s:
            while 1:
                response = self.fetch(
                    url=url,
                    n_records=n_records,
                    offset=offset,
                    query=query,
                    fields=fields,
                    session=s,
                    **kwargs
                )
                offset = get_key(response, "offset")
                data.extend(get_key(response, "records"))

                if offset is None:
                    break

        return data

    def fetch(self,
              url: str,
              n_records: Optional[int] = None,
              offset: Optional[str] = None,
              query: Optional[str] = None,
              fields: Optional[List[str]] = None,
              session: Optional[requests.Session] = None,
              **kwargs
              ) -> requests.models.Response:
        """Fetches a Page of results (or a single record) from a table.

        Args:
            url (str): Valid Airtable link
            n_records (int): Number of Records to retrieve (If None, all are retrieved)
            offset (str): Optional Number of Records to offset to retrieve.
            query (str): Optional A Valid Airtable Formatted Query to filter results
            fields (list): Optional list of column names to limit return

        Returns:
            (requests.models.Response) A Single Page of Results from a table.

        """

        return get_response(
            session,
            "get",
            url=url,
            headers=self._header,
            params=dict(
                maxRecords=n_records,
                offset=offset,
                filterByFormula=query,
                fields=fields,
            ),
            timeout=self.timeout,
            **kwargs
        )

    def push(self,
             url: str,
             data: Union[str, dict, DataFrame],
             typecast: bool = True,
             session: Optional[requests.Session] = None,
             **kwargs
             ):
        """Posts a Single Record to Airtable.

        Args:
            url (str): Valid Airtable Base
            data (str | dict | DataFrame): _
            typecast (bool): Coerce data type to cast during upload.
            session (requests.Session): request session which can be useful for iterative submissions.
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.post method.

        Returns:
            (requests.models.Response) Response from Airtable Server.

        Warning:
            - Submitting a Request Multiple times will create multiple (duplicated) entries.

        """
        if isinstance(data, (dict, DataFrame)):
            data = json.dumps(convert_upload(data, typecast))

        return get_response(
            session,
            "post",
            url=url,
            data=data,
            headers=self._header,
            timeout=self.timeout,
            **kwargs
        )

    def update(self,
               url: str,
               data: Union[str, dict, DataFrame],
               record_id: str,
               modify: bool = True,
               typecast: bool = True,
               session: Optional[requests.Session] = None,
               **kwargs
               ) -> requests.models.Response:
        """Modifies a Single existing Record inplace.

        Args:
            url (str): Valid Airtable Base
            data (str | dict | DataFrame): _
            typecast (bool): Coerce data type to cast during upload.
            record_id (str): Valid Record ID
            modify (bool): If true, inject record id into data for upload compatibility.
            session (requests.Session): request session which can be useful for iterative submissions.
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.patch method.

        Returns:
            (requests.models.Response) Response from Airtable

        Raises:
            ValueError: When data is not of type str | dict | or pd.DataFrame

        """
        if isinstance(data, str):
            _data = json.load(StringIO(data))

        elif isinstance(data, (dict, DataFrame)):
            _data = convert_upload(data=data, typecast=typecast)

        else:
            raise ValueError(f"Unsupported Data Format: {type(data)}")

        if modify:
            inject_record_id(data=_data, record_id=record_id)

        return get_response(
            session,
            "patch",
            url=url,
            data=json.dumps(_data),
            headers=self._header,
            timeout=self.timeout,
            **kwargs
        )

    def replace(self,
                url: str,
                data: Union[str, dict, DataFrame],
                record_id: str,
                modify: bool = True,
                typecast: bool = True,
                session: Optional[requests.Session] = None,
                **kwargs
                ) -> requests.models.Response:
        """Overwrites an existing Record.

        Args:
            url (str): Valid Airtable Base
            data (str | dict | DataFrame): _
            typecast (bool): Coerce data type to cast during upload.
            record_id (str): Valid Record ID
            modify (bool): If true, inject record id into data for upload compatibility.
            session (requests.Session): request session which can be useful for iterative submissions.
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.patch method.

        Returns:
            (requests.models.Response) Response from Airtable

        Raises:
            ValueError: When data is not of type str | dict | or pd.DataFrame

        """
        if isinstance(data, str):
            _data = json.load(StringIO(data))

        elif isinstance(data, (dict, DataFrame)):
            _data = convert_upload(data=data, typecast=typecast)

        else:
            raise ValueError(f"Unsupported Data Format: {type(data)}")

        if modify:
            inject_record_id(data=_data, record_id=record_id)

        return get_response(
            session,
            "put",
            url=url,
            data=json.dumps(_data),
            headers=self._header,
            timeout=self.timeout,
            **kwargs
        )

    def delete(self,
               url: str,
               record_id: Optional[str] = None,
               session: Optional[requests.Session] = None,
               **kwargs,
               ) -> requests.models.Response:
        """Deletes a Record from Airtable.

        Args:
            url (str): Valid Airtable Base or record
            record_id (str): Valid Record ID (Required if not already present on provided url)
            session (requests.Session): request session which can be useful for iteration.

        Returns:
            (requests.models.Response)

        Notes:
            -To submit a batch request, pass params={"records": record_ids}, and keep record_id
            as None.

        """
        if record_id is not None:
            url = f"{url}{record_id}" if url.endswith("/") else f"{url}/{record_id}"

        return get_response(
            session,
            "delete",
            url=url,
            headers=self._header,
            timeout=self.timeout,
            **kwargs
        )
