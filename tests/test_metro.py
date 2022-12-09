import pathlib
import pytest
from metro_db import MetroDB
from enum import IntEnum


class Role(IntEnum):
    PROTAGONIST = 1
    LOVE_INTEREST = 2


TEST_FOLDER = pathlib.Path('tests')


def test_metro_basic():
    db = MetroDB('metro', folder=TEST_FOLDER, enums_to_register=[Role])
    db.update_database_structure()
    assert len(db.tables) == 1
    assert 'characters' in db.tables
    db.dispose()


def test_structure_filepath():
    db = MetroDB('other', folder=TEST_FOLDER)
    db.load_yaml(db.folder / 'metro.yaml')
    assert len(db.tables) == 1
    assert 'characters' in db.tables
    db.dispose()


def test_structure_key():
    db = MetroDB('other', folder=TEST_FOLDER)
    db.load_yaml(structure_key='metro')
    assert len(db.tables) == 1
    assert 'characters' in db.tables
    db.dispose()


def test_invalid_spec():
    db = MetroDB('other', folder=TEST_FOLDER)
    with pytest.raises(RuntimeError):
        db.load_yaml(db.folder / 'metro.yaml', 'x')
    db.dispose()


def test_scope():
    with MetroDB('metro', folder=TEST_FOLDER, enums_to_register=[Role]) as db:
        assert len(db.tables) == 1
        assert 'characters' in db.tables

    pathlib.Path('tests/metro.db').unlink()
