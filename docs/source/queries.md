# Queries & Commands

## Row class
Results are returned as `Row` objects, which are built on the [`sqlite3.Row`](https://docs.python.org/3/library/sqlite3.html#row-objects) objects, but they have the additional feature of printing as a dictionary instead of `<sqlite3.Row object at 0x7f70ec8ac9f0>`

## Raw SQL

If you're well versed in SQL, the easiest way to use the class is with the four "raw" methods.

### Query One
`query_one` takes a single parameter: a string of the SQL query you want to run and returns a single `Row` object.

```python
print(db.query('SELECT title, score FROM movie WHERE year=1975'))
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
