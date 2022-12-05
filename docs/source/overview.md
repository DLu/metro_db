# Overview

The `metro_db` library provides a wrapper around the [`sqlite3`](https://docs.python.org/3/library/sqlite3.html) library for easy database development.

The overall goal is to write less SQL and more Python.

## Installation

```
sudo pip3 install metro_db
```


## Standard `SQLite3` Usage
Consider this example from the SQLite3 tutorial.

```python
import sqlite3
con = sqlite3.connect("tutorial.db")
cur = con.cursor()
cur.execute("CREATE TABLE movie(title, year, score)")
cur.execute("""
    INSERT INTO movie VALUES
        ('Monty Python and the Holy Grail', 1975, 8.2),
        ('And Now for Something Completely Different', 1971, 7.5)
""")
con.commit()
for row in cur.execute("SELECT * FROM movie ORDER BY year"):
    print(row)
```

The output will be:

```python
('And Now for Something Completely Different', 1971, 7.5)
('Monty Python and the Holy Grail', 1975, 8.2)
```

All the data is manually converted to strings of SQL commands. Alternatively, you can [pass parameters](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.execute) into the execute command, that avoids *some* of the string conversion.

Another limitation is that tuples are returned, so it is not immediately apparent what fields go with each value.

```python
cur.execute('INSERT INTO movie (title, year, score) VALUES(?, ?, ?)',
            ['Monty Python and the Holy Grail', 1975, 8.2]
            )
```

## Equivalent `metro_db` usage
The equivalent `metro_db.SQLiteDB` usage is much simpler.

```python
from metro_db import SQLiteDB
db = SQLiteDB('tutorial.db')
db.tables['movie'] = ['title', 'year', 'score']
db.field_types = {'year': 'int', 'score': 'real'}
db.update_database_structure()
db.insert('movie',
          {'title': 'Monty Python and the Holy Grail',
           'year': 1975,
           'score': 8.2})
db.insert('movie',
          {'title': 'And Now for Something Completely Different',
           'year': 1971,
           'score': 7.5})
db.write()
for row in db.query('SELECT * FROM movie ORDER BY year'):
    print(row)
```

The resulting output is:
```python
{'title': 'And Now for Something Completely Different', 'year': 1971, 'score': 7.5}
{'title': 'Monty Python and the Holy Grail', 'year': 1975, 'score': 8.2}
```

### Benefits
 * **Table Names and Fields Defined in Python Structures** - `tables` is a dictionary mapping table names to a list of field names.
 * **Field Types Enforced** - Defining a type for the field ensures that the values returned by queries are not just strings.
 * **Updating Database Structure** - If you decide to add a new table or a new field to an existing table, calling `update_database_structure` will automatically update the underlying database structure.
 * **Rows are Dictionaries** - The values in the insertion and query are paired with the name of the fields, and order doesn't matter.

### MetroDB
To make things even easier, there's an extension of `SQLiteDB` that loads the entire database structure from a `yaml` file.


```yaml
# tutorial.yaml
tables:
    movie:
    - title
    - year
    - score
types:
    year: int
    score: real
```

The equivalent Python for initialization is even easier:

```python
from metro_db import MetroDB
with MetroDB('tutorial') as db:
    db.insert('movie',
              {'title': 'Monty Python and the Holy Grail',
               'year': 1975,
               'score': 8.2})
    ...
```

Notes:
 * The string `'tutorial'`in the constructor reads the database structure from `tutorial.yaml` and reads/writes the data to `tutorial.db`
 * Using the `with` context automatically updates the database structure when the context is entered, and automatically calls `close/write` when exited.
