# Return Types

## Rows

By default, SQLite3 returns tuples to represent table rows, which are tricky because they do not contain field names.

You can change the "row factory" so that they return [`sqlite3.Row`](https://docs.python.org/3/library/sqlite3.html#row-objects) objects, which are a great improvement, since they mostly behave like dictionaries, allowing you to get the values via square brackets.

```python
for row in db.query('SELECT title, year FROM movie ORDER BY year'):
    print(row['title'])
```

This library takes it one step further with the `metro_db.Row` class, and implements three missing features:
 * String representation, so that printing the row results in the field/value dictionary being printed, and not something like `<sqlite3.Row object at 0x7f3ee438f350>`
 * The "contains" test, so that you can check if a field is `in` the `Row`, e.g. `'title' in row`
 * The `get` method to return either the value of a field or a default value if the field is not present.

 ```python
for row in db.query(f'SELECT {fields} FROM movie ORDER BY year'):
    print(row.get('title', 'Unknown title'))
 ```

## Flexible Iterators
Sometimes when retrieving results from a database, you just want to iterate over them, as in the above examples. However, in other situations, you'll want to do multiple things and/or treat the results more like a list. This package uses the `FlexibleIterator` class to allow you to do both.

In addition to iterating over the results, you can also get the number of results using `len` and use square brackets to index into the results.

```python
movies = db.query('SELECT * FROM movie')
print(f'Found {len(movies)} movies. The first is')
print(movies[0]['title'])
```

Using the list-like features does not affect the iteration, i.e. if you check the first element with `results[0]` that element will still be iterated over. On the other hand, iterating or using `next` will affect the list, in that the length will be however many elements are remaining in the iteration.
