import pathlib
import pytest
from metro_db import SQLiteDB, DatabaseError
from enum import IntEnum


@pytest.fixture()
def basic_db():
    path = pathlib.Path('basic.db')
    db = SQLiteDB(path)
    db.tables['people'] = ['name', 'age', 'grade', 'present']
    db.field_types['age'] = 'int'
    db.field_types['grade'] = 'real'
    db.field_types['present'] = 'bool'
    yield db
    db.dispose()


def test_creation(basic_db):
    basic_db.update_database_structure()


def test_insertion(basic_db):
    basic_db.update_database_structure()
    basic_db.execute('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)', [1, 1, 1, 1])

    assert basic_db.count('people') == 1

    # Check return types
    row = basic_db.query_one('SELECT * FROM people')
    assert row['name'] == '1'
    assert row['age'] == 1
    assert row['grade'] == 1    # 1 == 1.0
    assert isinstance(row['grade'], float)
    assert row['present'] is True

    # Check string representation of row
    assert str(row) == "{'name': '1', 'age': 1, 'grade': 1.0, 'present': True}"

    # Check repr
    assert str(basic_db) == 'people(1)\n'


def test_insertion_problem(basic_db):
    basic_db.update_database_structure()
    command = 'INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?)'  # Missing ?
    values = [1, 1, 1, 1]
    with pytest.raises(DatabaseError) as e:
        basic_db.execute(command, values)

    assert '3 values for 4 columns' in str(e.value)
    assert command == e.value.command
    assert command in str(e.value)
    assert values == e.value.parameters


def test_empty_query(basic_db):
    basic_db.update_database_structure()
    assert basic_db.count('people') == 0
    row = basic_db.query_one('SELECT * FROM people')
    assert row is None


def test_query_problems(basic_db):
    basic_db.update_database_structure()
    command = 'SELECT FROM PEOPLE'  # missing fields
    with pytest.raises(DatabaseError) as e:
        basic_db.query_one(command)

    assert 'syntax error' in str(e.value)
    assert command == e.value.command
    assert command in str(e.value)
    assert e.value.parameters is None

    with pytest.raises(DatabaseError) as e:
        list(basic_db.query(command))

    assert 'syntax error' in str(e.value)
    assert command == e.value.command
    assert command in str(e.value)
    assert e.value.parameters is None


def test_execute_many(basic_db):
    basic_db.update_database_structure()
    basic_db.execute_many('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)',
                          [['David', 25, 98.6, True],
                           ['Elise', 24, 99.1, True]])
    assert basic_db.count('people') == 2

    # Test reset
    basic_db.reset()
    assert basic_db.count('people') == 0


def test_execute_many_problems(basic_db):
    basic_db.update_database_structure()
    with pytest.raises(DatabaseError) as e:
        # missing table name
        basic_db.execute_many('INSERT INTO  (name, age, grade, present) VALUES(?, ?, ?, ?)',
                              [['David', 25, 98.6, True],
                               ['Elise', 24, 99.1, True]])
    assert 'syntax error' in str(e.value)


def test_inference(basic_db):
    basic_db.update_database_structure()

    # Open second object to same path
    db = SQLiteDB(pathlib.Path('basic.db'))
    db.infer_database_structure()
    assert db.tables == {'people': ['name', 'age', 'grade', 'present']}
    db.close(print_table_sizes=False)


def test_column_add(basic_db):
    basic_db.update_database_structure()
    basic_db.execute('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)', [1, 1, 1, 1])

    row = basic_db.query_one('SELECT * FROM people')
    assert len(row) == 4

    basic_db.tables['people'].append('new_text_field')
    basic_db.update_database_structure()

    row = basic_db.query_one('SELECT * FROM people')
    assert len(row) == 5


def test_column_removal(basic_db):
    basic_db.update_database_structure()
    basic_db.execute('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)', [1, 1, 1, 1])

    row = basic_db.query_one('SELECT * FROM people')
    assert len(row) == 4

    basic_db.tables['people'].pop(-1)  # Remove present
    basic_db.update_database_structure()

    row = basic_db.query_one('SELECT * FROM people')
    assert len(row) == 3


def test_quiet_close(capsys):
    path = pathlib.Path('basic.db')
    db = SQLiteDB(path)
    db.tables['people'] = ['name', 'age', 'grade', 'present']
    db.update_database_structure()
    db.dispose()
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''


def test_close(capsys):
    path = pathlib.Path('basic.db')
    db = SQLiteDB(path)
    db.tables['people'] = ['name', 'age', 'grade', 'present']
    db.update_database_structure()
    db.close(print_table_sizes=True)
    path.unlink()
    captured = capsys.readouterr()
    assert captured.out == 'people(0)\n\n'
    assert captured.err == ''


def test_two_tables(basic_db):
    basic_db.tables['cars'] = ['make', 'model']
    basic_db.update_database_structure()
    basic_db.execute_many('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)',
                          [['David', 25, 98.6, True],
                           ['Elise', 24, 99.1, True]])
    basic_db.execute('INSERT INTO cars (make, model) VALUES(?, ?)', ('Toyota', 'Prius'))
    assert basic_db.count('people') == 2
    assert basic_db.count('cars') == 1

    # Test reset
    basic_db.reset('people')
    assert basic_db.count('people') == 0
    assert basic_db.count('cars') == 1

    basic_db.reset()
    assert basic_db.count('people') == 0
    assert basic_db.count('cars') == 0


def test_enum(basic_db):
    class Status(IntEnum):
        HERE = 1
        ABSENT = 2

    basic_db.register_custom_enum(Status)
    basic_db.field_types['present'] = 'Status'
    basic_db.update_database_structure()

    basic_db.execute('INSERT INTO people (name, present) VALUES(?, ?)', ['Angelica', None])
    basic_db.execute('INSERT INTO people (name, present) VALUES(?, ?)', ['Eliza', Status.HERE])
    basic_db.execute('INSERT INTO people (name, present) VALUES(?, ?)', ['Peggy', Status.ABSENT])

    assert basic_db.query_one('SELECT present FROM people WHERE name="Eliza"')[0] == Status.HERE
    assert basic_db.query_one('SELECT present FROM people WHERE name="Peggy"')[0] == Status.ABSENT
    assert basic_db.query_one('SELECT present FROM people WHERE name="Angelica"')[0] is None


def test_column_alter(basic_db):
    basic_db.update_database_structure()
    basic_db.execute_many('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)',
                          [['David', 25, 98.6, True],
                           ['Elise', 24, 99.1, True]])

    basic_db.field_types['temperature'] = 'real'
    basic_db.update_table('people', ['name', 'age', 'temperature', 'present'], {'temperature': 'grade'})

    assert basic_db.lookup('temperature', 'people', 'WHERE name="David"') == 98.6

    basic_db.field_types['present'] = 'int'
    basic_db.update_database_structure()
    assert basic_db.lookup('present', 'people', 'WHERE name="David"') == 1
