# Queries & Commands

## Raw SQL

If you're well versed in SQL, the easiest way to use the class is with the four "raw" methods.

### Query One
`query_one` takes a single parameter: a string of the SQL query you want to run and returns a single `Row` object.

```python
print(db.query_one('SELECT title, score FROM movie WHERE year=1975'))
# Output: {'title': 'Monty Python and the Holy Grail', 'score': 8.2}
```
### Query
As you might guess, `query` works similarly, taking a single SQL query as a parameter but it now returns an iterator over all `Row`s that match the query.

```python
for row in db.query('SELECT * FROM movie ORDER BY year'):
    print(row)
# Output:
# {'title': 'And Now for Something Completely Different', 'year': 1971, 'score': 7.5}
# {'title': 'Monty Python and the Holy Grail', 'year': 1975, 'score': 8.2}
```

Note that in order to get the number of results or access them with indices, you must convert the iterator to a list.

```python
results = list(db.query('SELECT * FROM movie'))
print(len(results))
print(results[1])
```

### Execute
The `execute` method can be used for basic SQL commands that do not have results.
```python
db.execute('DELETE FROM movie WHERE score < 5.0')
```

It can also be used when you want to pass in Python values using the [`sqlite3` placeholder functionality](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders)

```python
db.execute('INSERT INTO movie (title, year, score) VALUES(?, ?, ?)',
           ('Monty Python and the Holy Grail', 1975, 8.2))
```

`execute` does also return a [`sqlite3.Cursor`](https://docs.python.org/3/library/sqlite3.html#cursor-objects) object, which is particularly useful when running `INSERT` commands as it allows you to access the [`lastrowid`](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.lastrowid).


### Execute Many
In a shocking twist development (`/s`), `execute_many` is like `execute` but it runs multiple times. The parameters are a SQL command and a list of tuples to execute individually.

```python
db.execute_many('INSERT INTO movie (title, year, score) VALUES(?, ?, ?)',
                [('Life of Brian', 1979, 8.5),
                 ('The Meaning of Life', 1983, 7.7)])
```

Running `execute_many` is often quicker than running `execute` on the individual items.

## Errors
There's lots of ways for database operations to go wrong. When that happens, `metro_db` will throw a `DatabaseError`. What sets it apart from the garden-variety [`sqlite3.Error`](https://docs.python.org/3/library/sqlite3.html#exceptions) is that it will contain the SQL query and values used in the `query/execute` methods. These can be accessed with the `command` and `parameters` fields.

```python
from metro_db import DatabaseError

try:
    # a bunch of complicated SQL stuff
except DatabaseError as e:
    print(f'Problem occurred: {e.value}')
    print(f'   with the command "{e.value.command}"')
    print(f'   and parameters {e.value.parameters}')
```

## Python Powered SQL

The exact syntax required for SQL commands is a skill unto itself, and not necessarily one that Python developers have fully developed. To that end, `metro_db` implements a number of Python-esque methods that wrap the database commands for ease of use.

### Lookup
Let's start with a basic lookup, where you want to know what year a movie came out.

```python
# Raw SQL Approach
result = db.query_one('SELECT year FROM movie WHERE title="Monty Python and the Holy Grail"')
print(result['year'])
```

A couple of pain points with this approach:
 1. Requires knowing the exact SQL syntax
 2. Must remember to quote the title yourself
 3. Even though we only look up one field, a `Row` is still returned and we must retrieve the value from there.

Alternatively, we could use the `lookup` wrapper.

```python
year = db.lookup('year', 'movie', 'WHERE title="Monty Python and the Holy Grail"')
print(year)
```

The parameters here are
 * The field we want to look up
 * The table name
 * (optional) the SQL clause

We can simplify this even further by letting the library generate the clause for us, by passing a dictionary in.
```python
year = db.lookup('year', 'movie', {'title': 'Monty Python and the Holy Grail'})
print(year)
```

Look! No SQL here!


### Generating Clauses
In general, all of the methods here that take a clause can use one of two options:
 1. A string that starts with `WHERE`
 2. A dictionary of values that must match exactly.

If a dictionary is passed in, it will be converted to an SQL `WHERE` clause via the `generate_clause` method. Note that the quotation marks around the value in the clause will be inserted automatically, using the `format_value` method which uses the column's datatype to determine any necessary wrapping.

If there are multiple fields in the dictionary, the default behavior is to generate a clause where all the values must match, i.e. `WHERE year=1975 AND score=8.4`

There are a few limitations to using the dictionary-based approach:
 * There is no support for complex logical operations, e.g. combining AND/OR.
 * There is no support for operators other than `=`, e.g. `>`, `<`, `LIKE`, etc.


### Lookup All

`lookup_all` is similar to `lookup` except it returns all the values of a field matching the query.

```python
for title in db.lookup_all('title', 'movie'):
    print(title)
```

In addition to specifying a clause, you can also add the flag `distinct=True` to ensure uniqueness in the returned results.


### Insert
The `insert` method wraps the `INSERT` SQL execution. Compare the raw SQL approach:

```python
db.execute('INSERT INTO movie (title, year, score) VALUES(?, ?, ?)',
            ('Monty Python and the Holy Grail', 1975, 8.2))
```
where the column names are completely separate from their values, to the Python dictionary based approach:
```python
db.insert('movie',
          {'title': 'Monty Python and the Holy Grail', 'year': 1975, 'score': 8.2})
```

Note that `insert` also has a return value, which is the value of the primary key for the newly inserted row (if it exists). This comes from the [`lastrowid`](https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-lastrowid.html), which is the value of the `AUTO_INCREMENT` column, and since our primary keys have that property, that is what `lastrowid` contains.

### Bulk Insert
`bulk_insert` is a faster way to insert multiple rows into tables. One of the ways it does that is by removing the dictionary data structure for the new rows. Instead, the parameters are
 * The name of the table
 * The names of the columns for each new row
 * A list of tuples with the new values.

The example from the `execute` section above could be rewritten as

```python
db.bulk_insert('movie', ['title', 'year', 'score'],
               [('Life of Brian', 1979, 8.5),
                ('The Meaning of Life', 1983, 7.7)])
```

### Update
The `update` is very similar to `insert` in that it takes two main parameters (a table name and a dictionary of values), but instead, it will only insert the dictionary isn't already in the table. Otherwise, it will just update the values.

```python
city_id = db.insert('cities', {'name': 'Manhattan', 'population': 1597000})
db.update('cities', {'id': city_id, 'population': 1629000})
```
The first line inserts a row into the table, and `city_id` is set to the auto-generated `id` field.

Then, if we want to update the population, we can do so with the `update` function. It determines whether the row is already contained in the table by looking at the third parameter `replace_key` which by default is `'id'`. It then updates (all) the row(s) with that `id` to have the new population.

If you pass in a different `replace_key`, it will instead determine membership with that column.
```python
db.update('movie', {'title': 'Monty Python and the Holy Grail', 'score': 9.8})
```

You can also pass in multiple criteria by setting `replace_key` to a list of column names.


### Unique Insert
`unique_insert` is a wrapper around `update`, but it ensures that the *entire* row (as specified) is in the table.

```python
db.unique_insert('movie', {'title': 'Monty Python and the Holy Grail', 'year': 1975})
db.unique_insert('movie', {'title': 'Life of Brian', 'year': 1979})
print(db.count('movie'))  # Contains two movies
db.unique_insert('movie', {'title': 'Life of Brian'})  # Does nothing, since row matches existing
db.unique_insert('movie', {'title': 'Monty Python and the Holy Grail', 'year': 2040})  # Inserts new row because
                                                                                       # year doesn't match.
                                                                                       # You just know they're going to
                                                                                       # remake it someday.
```

## Even Fancier SQL
### Count
Count the number of matching rows with `count`
```python
db.count('movie', 'WHERE score > 8')
```
The clause portion is optional.

### Dictionaries
In the case where you want the output of a query to not be a list / iterator, you can structure it into a dictionary in two different ways.

With `dict_lookup`, you specify a field for the dictionary key, and a field for the dictionary value.

```python
scores = db.dict_lookup('title', 'score', 'movie')
# Result is {'And Now for Something Completely Different', 7.5,
#            'Monty Python and the Holy Grail': 8.2}
```

With `table_as_dict`, you get the entire row as the dictionary value.

```python
movies = db.table_as_dict('movie', 'title')
# Result is
# {'Monty Python and the Holy Grail': {'title': 'Monty Python and the Holy Grail',
#                                      'year': 1975,
#                                      'score': 8.2},
#  'And Now for Something Completely Different': {
#                                      'title': 'And Now for Something Completely Different',
#                                      'year': 1971,
#                                      'score': 7.5}
#   }
```


### Unique Counts
If you want to count the number of occurrences of all values of a column, you can get a dictionary mapping the values to their counts with `unique_counts`:

```python
yearly_activity = db.unique_counts('movie', 'year')
# Result is {1971: 1, 1975: 1}
```

### Sum
Here's a shortcut for calculating the sum of the values of a column.

```python
avg_score = db.sum('movie', 'score') / db.count('movie')
```
