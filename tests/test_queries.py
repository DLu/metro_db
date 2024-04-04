import datetime
import pathlib
import pytest
from metro_db import SQLiteDB
from enum import IntEnum


class Position(IntEnum):
    CATCHER = 2
    FIRST_BASE = 3
    SECOND_BASE = 4
    THIRD_BASE = 5
    SHORTSTOP = 6
    LEFT_FIELD = 7


@pytest.fixture()
def demo_db():
    path = pathlib.Path('demo.db')
    db = SQLiteDB(path, default_type='int')
    db.tables['batters'] = ['id', 'name', 'year', 'hits', 'position']
    db.field_types['name'] = 'str'
    db.field_types['position'] = 'Position'
    db.register_custom_enum(Position)
    db.update_database_structure()
    for values in [
        ['Olerud', 1998, 197, Position.FIRST_BASE],
        ['Piazza', 1998, 137, Position.CATCHER],
        ['Alfonzo', 1998, 155, Position.THIRD_BASE],
        ['Olerud', 1999, 173, Position.FIRST_BASE],
        ['Piazza', 1999, 162, Position.CATCHER],
        ['Alfonzo', 1999, 191, Position.SECOND_BASE],
        ['Zeile', 2000, 146, Position.FIRST_BASE],
        ['Piazza', 2000, 156, Position.CATCHER],
        ['Alfonzo', 2000, 176, Position.SECOND_BASE],
    ]:
        db.execute('INSERT INTO batters (name, year, hits, position) VALUES(?, ?, ?, ?)', values)

    yield db
    db.dispose()


def test_query(demo_db):
    results = demo_db.query('SELECT * FROM batters')
    c = 0
    names = set()
    for row in results:
        c += 1
        names.add(row['name'])
    assert c == 9
    assert len(names) == 4


def test_query_as_list(demo_db):
    results = demo_db.query('SELECT * FROM batters ORDER BY -hits')
    assert len(results) == 9

    assert results[0]['name'] == 'Olerud'


def test_lookup_all(demo_db):
    # Explicitly convert results to list
    # Test from before FlexibleIterator was implemented
    values = list(demo_db.lookup_all('name', 'batters', {'year': 1998}))
    assert str(values) == str(['Olerud', 'Piazza', 'Alfonzo'])

    values = list(demo_db.lookup_all('name', 'batters', {'year': 1999}))
    assert len(values) == 3
    assert 'Olerud' in values
    assert 'Piazza' in values
    assert 'Alfonzo' in values

    values = list(demo_db.lookup_all('name', 'batters', {'year': 2000}))
    assert 'Zeile' in values
    assert 'Piazza' in values
    assert 'Alfonzo' in values
    assert len(values) == 3


def test_lookup_all_without_cast(demo_db):
    values = demo_db.lookup_all('name', 'batters', {'year': 1998})
    assert str(values) == str(['Olerud', 'Piazza', 'Alfonzo'])

    values = demo_db.lookup_all('name', 'batters', {'year': 1999})
    assert len(values) == 3
    assert 'Olerud' in values
    assert 'Piazza' in values
    assert 'Alfonzo' in values

    values = demo_db.lookup_all('name', 'batters', {'year': 2000})
    assert 'Zeile' in values
    assert 'Piazza' in values
    assert 'Alfonzo' in values
    assert len(values) == 3


def test_lookup(demo_db):
    assert demo_db.lookup('hits', 'batters', {'year': 1999, 'name': 'Alfonzo'}) == 191

    # Contrived examples to test quote handling
    assert demo_db.lookup('hits', 'batters', {'year': 1999, 'name': 'O\'Brien'}) is None
    assert demo_db.lookup('hits', 'batters', {'year': 1999, 'name': '"O\'Brien"'}) is None
    assert demo_db.lookup('hits', 'batters', {'year': 1999, 'name': '"Piazza"'}) is None
    assert demo_db.lookup('hits', 'batters', {'year': 1999, 'name': 5}) is None


def test_dict_lookup(demo_db):
    d = demo_db.dict_lookup('name', 'hits', 'batters', 'WHERE year == 1999')
    assert d['Olerud'] == 173
    assert d['Piazza'] == 162
    assert d['Alfonzo'] == 191


def test_dict_lookup_with_clause(demo_db):
    d = demo_db.dict_lookup('name', 'hits', 'batters', {'year': 1998})
    assert d['Olerud'] == 197
    assert d['Piazza'] == 137
    assert d['Alfonzo'] == 155


def test_table_as_dict(demo_db):
    d = demo_db.table_as_dict('batters')
    assert d[1]['name'] == 'Olerud'
    assert d[1]['year'] == 1998
    assert d[1]['position'] == Position.FIRST_BASE
    assert len(d) == 9

    d = demo_db.table_as_dict('batters', 'position', ['name', 'hits'], {'year': 2000})
    assert len(d) == 3
    assert d[Position.FIRST_BASE]['name'] == 'Zeile'
    assert d[Position.FIRST_BASE]['hits'] == 146
    assert 'year' not in d[Position.FIRST_BASE]
    assert d[Position.CATCHER]['name'] == 'Piazza'
    assert d[Position.SECOND_BASE]['name'] == 'Alfonzo'


def test_unique_counts(demo_db):
    d = demo_db.unique_counts('batters', 'name')
    assert d['Olerud'] == 2
    assert d['Piazza'] == 3
    assert d['Alfonzo'] == 3


def test_sum(demo_db):
    assert demo_db.sum('batters', 'hits') == 1493
    assert demo_db.sum('batters', 'hits', {}) == 1493
    assert demo_db.sum('batters', 'hits', {'year': 2000}) == 478
    assert demo_db.sum('batters', 'hits', {'position': Position.FIRST_BASE}) == 516


def test_sum_counts(demo_db):
    d = demo_db.sum_counts('batters', 'hits', 'name')
    assert d['Olerud'] == 370
    assert d['Piazza'] == 455
    assert d['Alfonzo'] == 522


def test_insertion(demo_db):
    new_id = demo_db.insert('batters', {'name': 'Abayani', 'hits': 101, 'year': 2000, 'position': Position.LEFT_FIELD})
    assert new_id == 10
    assert demo_db.count('batters') == 10


def test_bulk_insert(demo_db):
    demo_db.bulk_insert('batters', ['name', 'year', 'hits', 'position'], [
        ('Ordóñez', 1999, 134, Position.SHORTSTOP),
        ('Ventrua', 1999, 177, Position.THIRD_BASE),
    ])

    assert demo_db.count('batters') == 11


def test_update(demo_db):
    # No match, just insert
    assert demo_db.count('batters') == 9
    row_id = demo_db.update('batters', {'name': 'McEwing', 'year': 2000, 'hits': 34}, ['name', 'year'])
    assert demo_db.count('batters') == 10
    assert row_id == 10

    # Actual update
    assert demo_db.lookup('hits', 'batters', {'name': 'Olerud', 'year': 1999}) == 173
    row_id = demo_db.update('batters', {'name': 'Olerud', 'year': 1999, 'hits': 334}, ['name', 'year'])
    assert demo_db.count('batters') == 10
    assert row_id == 4
    assert demo_db.lookup('hits', 'batters', {'name': 'Olerud', 'year': 1999}) == 334

    # Update by ID
    b_id = demo_db.lookup('id', 'batters', {'name': 'Zeile'})
    row_id = demo_db.update('batters', {'id': b_id, 'hits': 4})
    assert demo_db.count('batters') == 10
    assert row_id == b_id
    assert demo_db.lookup('hits', 'batters', {'name': 'Zeile'}) == 4


def test_unique_insert(demo_db):
    assert demo_db.count('batters') == 9
    b_id = demo_db.unique_insert('batters', {'name': 'Olerud', 'year': 1998})
    assert b_id <= 9
    assert demo_db.count('batters') == 9
    b_id = demo_db.unique_insert('batters', {'name': 'Piazza', 'year': 2001})
    assert b_id == 10
    assert demo_db.count('batters') == 10


def test_none(demo_db):
    assert demo_db.count('batters', clause={'name': None}) == 0
    demo_db.insert('batters', {'year': 2002, 'hits': 5})
    clause = 'WHERE hits > 0 AND ' + demo_db.generate_clause({'name': None}, full=False)
    assert demo_db.count('batters', clause=clause) == 1


@pytest.fixture()
def demo_without_id_db():
    path = pathlib.Path('all_field.db')
    db = SQLiteDB(path, default_type='int')
    db.tables['batters'] = ['name', 'year', 'position']
    db.field_types['name'] = 'str'
    db.field_types['position'] = 'Position'
    db.register_custom_enum(Position)
    db.update_database_structure()
    for values in [
        ['Olerud', 1998, Position.FIRST_BASE],
        ['Piazza', 1998, Position.CATCHER],
        ['Alfonzo', 1998, Position.THIRD_BASE],
    ]:
        db.execute('INSERT INTO batters (name, year, position) VALUES(?, ?, ?)', values)

    yield db
    db.dispose()


def test_all_field_update(demo_without_id_db):
    db = demo_without_id_db

    # No match, just insert
    assert db.count('batters') == 3
    row_id = db.update('batters', {'name': 'McEwing', 'year': 2000}, ['name', 'year'])
    assert db.count('batters') == 4
    assert row_id is None

    # Actual update
    row_id = db.update('batters', {'name': 'Olerud', 'year': 1998}, ['name', 'year'])
    assert db.count('batters') == 4
    assert row_id is None


def test_accidental_open():
    db = SQLiteDB(pathlib.Path('empty.db'))
    db.update_database_structure()  # Update with no tables defined
    db.dispose()


@pytest.fixture()
def date_db():
    path = pathlib.Path('history.db')
    db = SQLiteDB(path)
    db.tables = {
        'great_moments': ['id', 'name', 'date'],
        'better_moments': ['id', 'name', 'datetime'],
    }
    db.field_types['id'] = 'int'
    db.field_types['date'] = 'date'
    db.field_types['datetime'] = 'datetime'
    db.update_database_structure()

    yield db
    db.dispose()


def test_date_handling(date_db):
    # Test insertion
    date_db.execute('INSERT INTO great_moments (name, date) VALUES(?, ?)',
                    ['Declaration of Independence', datetime.date(1776, 7, 4)])

    assert date_db.count('great_moments') == 1

    # Check return types
    row = date_db.query_one('SELECT * FROM great_moments')
    assert row['id'] == 1
    assert row['name'] == 'Declaration of Independence'
    assert row['date'] == datetime.date(1776, 7, 4)
    assert isinstance(row['date'], datetime.date)

    # Insert two more
    date_db.insert('great_moments', {'name': 'Beethoven\'s Ninth Symphony', 'date': '1824-05-07'})
    date_db.update('great_moments', {'name': 'Rosalind Franklin born', 'date': datetime.date(1920, 7, 25)}, 'name')

    # Check output type
    assert isinstance(date_db.lookup('date', 'great_moments', {'name': "Beethoven's Ninth Symphony"}),
                      datetime.date)

    # Check clause generation
    event_name = date_db.lookup('name', 'great_moments', {'date': datetime.date(1920, 7, 25)})
    assert event_name == 'Rosalind Franklin born'


def test_datetime_handling(date_db):
    date_db.insert('better_moments', {'name': '2015 Game 1', 'datetime': datetime.datetime(2015, 10, 27, 20, 7)})
    date_db.insert('better_moments', {'name': '1986 Game 6', 'datetime': datetime.datetime(1986, 10, 25, 20, 30)})
    date_db.insert('better_moments', {'name': '1969 Game 5', 'datetime': datetime.datetime(1969, 10, 16)})

    # Check output type
    assert isinstance(date_db.lookup('datetime', 'better_moments', {'name': '2015 Game 1'}), datetime.datetime)

    # Check clause generation
    event_name = date_db.lookup('name', 'better_moments', {'datetime': datetime.datetime(1986, 10, 25, 20, 30)})
    assert event_name == '1986 Game 6'

    count = date_db.count('better_moments', clause='WHERE datetime > "1984-01-01"')
    assert count == 2


def test_date_handling_with_old_field_type():
    # Note: For backwards compatibility, we ensure that declaring the fieldtype "timestamp" still works
    path = pathlib.Path('old_history.db')
    date_db = SQLiteDB(path)
    date_db.tables = {
        'better_moments': ['id', 'name', 'datetime'],
    }
    date_db.field_types['id'] = 'int'
    date_db.field_types['date'] = 'date'
    date_db.field_types['datetime'] = 'timestamp'
    date_db.update_database_structure()

    date_db.insert('better_moments', {'name': '2015 Game 1', 'datetime': datetime.datetime(2015, 10, 27, 20, 7)})
    date_db.insert('better_moments', {'name': '1986 Game 6', 'datetime': datetime.datetime(1986, 10, 25, 20, 30)})
    date_db.insert('better_moments', {'name': '1969 Game 5', 'datetime': datetime.datetime(1969, 10, 16)})

    # Check output type
    assert isinstance(date_db.lookup('datetime', 'better_moments', {'name': '2015 Game 1'}), datetime.datetime)

    # Check clause generation
    event_name = date_db.lookup('name', 'better_moments', {'datetime': datetime.datetime(1986, 10, 25, 20, 30)})
    assert event_name == '1986 Game 6'

    count = date_db.count('better_moments', clause='WHERE datetime > "1984-01-01"')
    assert count == 2

    date_db.dispose()
