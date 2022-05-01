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

from typing import List, Optional, Tuple, Union
from pandas import DataFrame

from .utils import check_key
from .utils import get_key
from .utils import parcels
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

    """
    maxUpload = 10  # 10 records may be uploaded at a time at maximum
    apiRateLimit = 5  # Rate Limit is 5 submissions per second (1 / 0.2s)
    _base_url = "https://api.airtable.com/"

    def __init__(self,
                 token: Optional[str] = None,
                 timeout: Optional[Union[Tuple[float, float], float]] = None,
                 version: str = "v0",
                 ) -> None:
        self.session = requests.Session()
        self.token = token
        self.timeout = timeout

        self.base_url = f"{self._base_url}{version}/"

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        value = value or os.environ.get("AIRTABLE_API_KEY")
        check_key(value, "API Key")
        self._update_header(value)
        self._token = value

    def _update_header(self, value):
        self.session.headers.update({
            "Authorization": f"Bearer {value}",
            "Content-Type": "application/json"
        }
        )

    def _check_upload_limit(self):
        if self.maxUpload <= 0:
            raise ValueError(f"Must define a valid Maximum Upload Limit: {self.maxUpload}")

    def close(self):
        """Close out the request session.

        Warning:
            Enacting this method is irreversible, and will cause all methods interfacing
            with airtable to fail.

        """
        self.session.close()

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
        """Iteratively Retrieves Records from a given Table.

        Args:
            url (str): Valid Airtable link
            n_records (int): Optional Number of Records to retrieve (If None, all are retrieved)
            offset (str): Optional Number of Records to offset to retrieve.
            query (str): Optional A Valid Airtable Formatted Query to filter results
            fields (list): Optional list of column names to limit return

        Returns:
            (List[dict]) A List of Dictionary Records from a given table

        """
        data = []

        while 1:
            response = self.session.get(
                url=url,
                params=dict(
                    maxRecords=n_records,
                    offset=offset,
                    filterByFormula=query,
                    fields=fields,
                ),
                timeout=self.timeout,
                **kwargs
            )
            offset = get_key(response, "offset")
            data.extend(get_key(response, "records"))

            if offset is None:
                break

        return data

    def push(self,
             url: str,
             data: Union[dict, DataFrame],
             typecast: bool = True,
             **kwargs
             ):
        """Posts Record(s) to Airtable.

        Args:
            url (str): Valid Airtable Base
            data (str | dict | DataFrame): _
            typecast (bool): Coerce data type to cast during upload.
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.post method.

        Returns:
            (requests.models.Response) Response from Airtable Server.

        Warning:
            - Submitting a Request Multiple times will create multiple (duplicated) entries.

        """
        self._check_upload_limit()
        data = convert_upload(data=data, typecast=typecast, limit=self.maxUpload)
        responses = []
        for d in data:
            response = self.session.post(
                url=url,
                data=json.dumps(d),
                timeout=self.timeout,
                **kwargs
            )
            responses.append(response)
        return responses

    def update(self,
               url: str,
               data: Union[dict, DataFrame],
               record_id: List[str],
               typecast: bool = True,
               **kwargs
               ) -> List[requests.models.Response]:
        """Modifies existing Record(s) inplace.

        Args:
            url (str): Valid Airtable Base
            data (dict | DataFrame): data to update
            typecast (bool): Coerce data type to cast during upload.
            record_id (str): Valid Record ID(s)
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.patch method.

        Returns:
            (List[requests.models.Response]) Response(s) from Airtable

        Raises:
            ValueError: When data is not of type dict | pd.DataFrame

        """
        self._check_upload_limit()
        _data = convert_upload(data=data, typecast=typecast, limit=self.maxUpload)
        responses = []

        count = 0
        for d in _data:
            for idx in range(len(get_key(d, "records"))):
                inject_record_id(data=d, record_id=record_id[count + idx], index=idx)

            response = self.session.patch(
                url=url,
                data=json.dumps(d),
                timeout=self.timeout,
                **kwargs
            )
            responses.append(response)
            count += self.maxUpload

        return responses

    def replace(self,
                url: str,
                data: Union[dict, DataFrame],
                record_id: List[str],
                typecast: bool = True,
                **kwargs
                ) -> List[requests.models.Response]:
        """Overwrites existing Record(s).

        Args:
            url (str): Valid Airtable Base
            data (dict | DataFrame): _
            typecast (bool): Coerce data type to cast during upload.
            record_id (list): Valid Record ID(s)
            kwargs (Any): Any addition keyword Arguments are fed directly to requests.patch method.

        Returns:
            (List[requests.models.Response]) Response(s) from Airtable

        Raises:
            ValueError: When data is not of type dict | pd.DataFrame

        """
        self._check_upload_limit()
        _data = convert_upload(data=data, typecast=typecast, limit=self.maxUpload)

        responses = []
        count = 0
        for d in _data:
            for idx in range(len(get_key(d, "records"))):
                inject_record_id(data=d, record_id=record_id[count + idx], index=idx)
            response = self.session.put(
                url=url,
                data=json.dumps(d),
                timeout=self.timeout,
                **kwargs
            )
            responses.append(response)
            count += self.maxUpload

        return responses

    def delete(self,
               url: str,
               record_id: List[str],
               **kwargs,
               ) -> List[requests.models.Response]:
        """Deletes Record(s) from Airtable.

        Args:
            url (str): Valid Airtable Base or record
            record_id (list): List of Valid Record ID(s)

        Returns:
            (List[requests.models.Response]) Response(s) from Airtable

        """
        # Sanity Checks
        self._check_upload_limit()
        assert len(record_id) >= 1, "Must provide a list of record ids."

        # Preparation
        original_url = url
        responses = []

        for j in parcels(record_id, self.maxUpload):
            # The params records keyword fails when only one record is provided (len(j) % self.maxUpload == 1)
            if len(j) == 1:
                # In the funny case where maxUpload is set to 1, we need to refer to original url
                url = f"{original_url}{j[0]}" if url.endswith("/") else f"{original_url}/{j[0]}"
                try:
                    # when a single record id, there will be no previous params keyword
                    kwargs.pop("params")
                except KeyError:
                    pass
            else:
                kwargs.update(dict(params={"records": j}))

            response = self.session.delete(
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            responses.append(response)

        return responses
