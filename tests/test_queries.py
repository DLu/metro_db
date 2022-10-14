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
    db.field_types['name'] = 'text'
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
    db.close(print_table_sizes=False)
    path.unlink()


def test_lookup_all(demo_db):
    values = list(demo_db.lookup_all('name', 'batters', {'year': 1999}))
    assert len(values) == 3
    assert 'Olerud' in values
    assert 'Piazza' in values
    assert 'Alfonzo' in values


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
