# Return Types

## Rows

By default, SQLite3 returns tuples to represent table rows, which are tricky because they do not contain field names.

You can change the "row factory" so that they return [`sqlite3.Row`](https://docs.python.org/3/library/sqlite3.html#row-objects) objects, which are a great improvement, since they mostly behave like dictionaries, allowing you to get the values via square brackets.

```python
for row in db.query('SELECT title, year FROM movie ORDER BY year'):
    print(row['title'])
```

This library takes it one step further with the `metro_db.Row` class, and implements four missing features:
 * String representation, so that printing the row results in the field/value dictionary being printed, and not something like `<sqlite3.Row object at 0x7f3ee438f350>`
 * The `items` method so you can iterate over keys and values
 * The "contains" method, so that you can check if a field is `in` the `Row`, e.g. `'title' in row`
 * The `get` method to return either the value of a field or a default value if the field is not present.

 ```python
for row in db.query(f'SELECT {fields} FROM movie ORDER BY year'):
    print(row.get('title', 'Unknown title'))
 ```
