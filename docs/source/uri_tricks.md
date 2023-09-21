# URI Tricks

You can pass a URI path to the `sqlite3` constructor. These query params allow you to [customize how to interact with the filesystem](https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris).

## Read Only
You can make a database read only with by setting `uri_query` to `mode=ro` in the constructor to either `SQLiteDB` or `MetroDB`:


```python
from metro_db import SQLiteDB, MetroDB

sdb = SQLiteDB('type_demo', uri_query='mode:ro')
with MetroDB('tutorial', uri_query='mode:ro') as mdb:
    ...
```

## No Creation
You can ensure that you don't create a new file and only work on existing files by specifying `uri_query='mode:rw'`.
