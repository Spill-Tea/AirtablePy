# AirtablePy
[![build status][buildstatus-image]][buildstatus-url]

[buildstatus-image]: https://github.com/Spill-Tea/AirtablePy/actions/workflows/python-package.yml/badge.svg?branch=main
[buildstatus-url]: https://github.com/Spill-Tea/AirtablePy/actions?query=branch%3Amain

Python API to interact with Airtable

### Table of Contents
1. [Installation](#installation) 
2. [API Token](#api-token)
3. [Simple Interface](#simple-interface)
4. [License](#license)


### Installation
AirtablPy is available on [pypi](https://pypi.org/project/AirtablePy/). Install using pip.
```bash
pip install AirtablePy
```

### API Token
To use the Airtable API, you need a valid [token](https://support.airtable.com/hc/en-us/articles/219046777-How-do-I-get-my-API-key-).
You may setup an environment variable called `AIRTABLE_API_KEY` which this interface will use.

### Simple Interface
```python

from AirtablePy import AirtableAPI
from AirtablePy.utils import retrieve_keys
from AirtablePy.query import date_query

# Instantiate interface with valid token.
# If token is not specified, it will search for environment variable AIRTABLE_API_KEY
api = AirtableAPI(token="keyXXXXXXXXXXXXXX")

# Construct a valid url
base_id = "appXXXXXXXXXXXXXX"
table_name = "Example Table"
url = api.construct_url(base_id, table_name)

# Retrieve records from a table, with or without a query filter
records = api.get(url, query=date_query(column_name="date", start="20220401", end="20220415"))

# Upload new data entries
data = {"Column 1": [1, 2, 3], "Column 2": [4, 5, 6]}
response_upload = api.push(url=url, data=data)

# Collect a list of record id's from upload
record_ids = retrieve_keys(response_upload, "id")

# Update records with additional (or modified) data
data_update = {"Column 3": [7, 8, 9]}  # data will be present in all three columns
response_update = api.update(url=url, data=data_update, record_id=record_ids)

# Replace existing records with different data
data_replace = {"Column 2": [10, 11, 12]}  # only column 2 will have data
response_replace = api.replace(url=url, data=data_replace, record_id=record_ids)

# Delete existing Records
response_delete = api.delete(url=url, record_id=record_ids)

```



### License
[MIT](./LICENSE)