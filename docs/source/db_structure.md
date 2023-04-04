# Database Structure

There are four parts to the database structure definition:

 * **Tables** - a dictionary mapping the table name (string) to a list of field names (also strings)
 * **Field Types** - a dictionary mapping the field name (string) to a string for the type to be used for that field *in all tables*.
 * **Default Type** - a string representing the default type for a field if it is not specified above. (By default, `'TEXT'`)
 * **Primary Keys** - A list of string field names that should be treated as primary keys. (By default, `['id']`)

There are two places to define the database structure.
 * Using `SQLiteDB`, you can directly modify the `tables`, `field_types`, `default_type` and `primary_keys` and then call `update_database_structure()`
   * `default_type` and `primary_keys` can also be passed in in the constructor.
 * Using `MetroDB`, the definition is loaded in via the `yaml` file, which should be a dictionary at the top level, with at the very least, the tables definition with the key `tables`. The other parts are optional, and can be loaded with the keys `types`, `default_type`, and `primary_keys`.
   * You can also use the more verbose `field_types` for `types`

## SQL Limitations
The functionality implemented here is only a small subset of what can be done with SQL. Here are a couple of key limitations.
 * All fields with the same name have the same type
 * The only SQL constraint implemented thus far is `PRIMARY KEY`

## Datatypes
Every field has an associated "type", which is really TWO types, the **Python** type that is used in the Python code, and the [**SQL**](https://www.sqlite.org/datatype3.html) type that is used in the database. The standard available types are:

| Python Type | SQL Type    |
|-------------|-------------|
| `int`       | `INTEGER`   |
| `float`     | `REAL`      |
| `str`       | `TEXT`      |
| `bool`      | `INTEGER`   |
| `date`      | `DATE`      |
| `datetime`  | `TIMESTAMP` |

When you want to use a Python type in SQL, it will automatically be **adapted** into its corresponding SQL type.
When you read a value from the SQL, it will automatically be **converted** into its corresponding Python type.

When specifying a type in the database structure, use the Python type.

### Example
```python
from metro_db import SQLiteDB
db = SQLiteDB('type_demo')
db.tables['people'] = ['name', 'age', 'grade', 'present']
db.field_types['age'] = 'int'
db.field_types['grade'] = 'float'
db.field_types['present'] = 'bool'
db.update_database_structure()
db.insert('people', {'name': 'David', 'age': 21, 'grade': 98.6, 'present': True})
db.insert('people', {'name': 1, 'age': 1, 'grade': 1, 'present': 1})

for row in db.query('SELECT * FROM people'):
    for key, value in dict(row).items():
        print(f'{key:8s}: {repr(value):>8s} ({type(value)})')
```

The output will be
```
name    :  'David' (<class 'str'>)
age     :       21 (<class 'int'>)
grade   :     98.6 (<class 'float'>)
present :     True (<class 'bool'>)
name    :      '1' (<class 'str'>)
age     :        1 (<class 'int'>)
grade   :      1.0 (<class 'float'>)
present :     True (<class 'bool'>)
```

Note that the values read from the database have the specified Python type (where possible), regardless of what type was inserted (by design).


### Custom Data Types
You can also set up the database to have custom data types, which requires four things:
 1. A name for the type (a string)
 1. The Python type (notably, not the string representing the type, but the type itself)
 1. An adapter function for translating the Python type into the SQL type.
 1. A converter function for translating the SQL type to the Python type.

For example, `bool` is not natively supported by `sqlite3`. Instead it is implemented with the following snippet.

```python
    db.register_custom_type('bool', bool, int, lambda v: bool(v))
```
 1. The name is the string `'bool'`
 1. The type is the Python type for `bool`
 1. To adapt a `bool` to an integer for the SQL, we use the built-in `int` function
 1. To convert an integer to a `bool`, we use the built-in `bool` function.

Additionally, you can register custom [`IntEnum`](https://docs.python.org/3/library/enum.html#enum.IntEnum) to be stored as integers in the SQL with `register_custom_enum`:

```python
class Direction(IntEnum):
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4

db.register_custom_enum(Direction)
```

The name and adapter/converter functions are generated automatically.
