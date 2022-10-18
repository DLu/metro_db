import pathlib
import pytest
from metro_db import SQLiteDB
from metro_db.peek import main as peek


@pytest.fixture()
def basic_db():
    path = pathlib.Path('basic.db')
    db = SQLiteDB(path)
    db.tables['people'] = ['name', 'age', 'grade', 'present']
    db.field_types['age'] = 'int'
    db.field_types['grade'] = 'real'
    db.field_types['present'] = 'bool'
    db.update_database_structure()

    db.execute_many('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)',
                    [['David', 25, 98.6, True],
                     ['Elise', 24, 99.1, True]])
    db.write()
    yield db
    db.close(print_table_sizes=False)
    path.unlink()


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
