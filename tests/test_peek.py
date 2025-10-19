import pathlib
import pytest
from metro_db import SQLiteDB
from metro_db.peek import main as peek, db_path_completer


@pytest.fixture()
def basic_db():
    path = pathlib.Path('basic.db')
    db = SQLiteDB(path)
    db.tables['people'] = ['name', 'age', 'grade', 'present']
    db.field_types['age'] = 'int'
    db.field_types['grade'] = 'float'
    db.field_types['present'] = 'bool'
    db.update_database_structure()

    db.execute_many('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)',
                    [['David', 25, 98.6, True],
                     ['Elise', 24, 99.1, True]])
    db.write()
    yield db
    db.dispose()


def test_peek_basic(basic_db, capsys):
    peek(['basic.db'])
    captured = capsys.readouterr()
    assert captured.out == open('tests/out/basic_out.txt').read()
    assert captured.err == ''


def test_peek_n1(basic_db, capsys):
    peek(['basic.db', '1'])
    captured = capsys.readouterr()
    assert captured.out == open('tests/out/basic_n1.txt').read()
    assert captured.err == ''


def test_peek_n10(basic_db, capsys):
    peek(['basic.db', '10'])
    captured = capsys.readouterr()
    assert captured.out == open('tests/out/basic_out.txt').read()
    assert captured.err == ''


@pytest.fixture()
def two_table_db():
    path = pathlib.Path('dos.db')
    db = SQLiteDB(path)
    db.tables['first_names'] = ['id', 'name']
    db.tables['last_names'] = ['id', 'name']
    db.field_types['id'] = 'int'
    db.update_database_structure()

    db.execute_many('INSERT INTO first_names (name) VALUES(?)',
                    [['David'], ['Elise']])
    db.execute_many('INSERT INTO last_names (name) VALUES(?)',
                    [['Lu'], ['Peterson']])
    db.write()
    yield db
    db.dispose()


def test_peek_two(two_table_db, capsys):
    peek(['dos.db'])
    captured = capsys.readouterr()
    assert captured.out == open('tests/out/two_out.txt').read()
    assert captured.err == ''


def test_peek_two_single(two_table_db, capsys):
    peek(['dos.db', '-t', 'first_names'])
    captured = capsys.readouterr()
    assert captured.out == open('tests/out/two_first.txt').read()
    assert captured.err == ''


def test_path_completer():
    folder = 'tests/completions'
    all_options = db_path_completer(folder)
    assert len(all_options) == 2
    assert folder + '/foo.db' in all_options
    assert folder + '/bar.db' in all_options

    some_options = db_path_completer(folder + '/f')
    assert len(some_options) == 1
    assert folder + '/foo.db' in some_options

    no_options = db_path_completer(folder + '/n')
    assert len(no_options) == 0
