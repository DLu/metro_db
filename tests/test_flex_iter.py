
from metro_db.types import FlexibleIterator

import pytest


@pytest.fixture()
def flex_range():
    return FlexibleIterator(a for a in range(1, 6))


def test_values(flex_range):
    assert next(flex_range) == 1
    assert next(flex_range) == 2
    assert next(flex_range) == 3
    assert next(flex_range) == 4
    assert next(flex_range) == 5
    with pytest.raises(StopIteration):
        next(flex_range)


def test_items(flex_range):
    assert flex_range[0] == 1
    assert flex_range[1] == 2
    assert flex_range[2] == 3
    assert flex_range[3] == 4
    assert flex_range[4] == 5
    assert len(flex_range) == 5

    with pytest.raises(IndexError):
        flex_range[5]

    assert flex_range[-1] == 5
    assert flex_range[-2] == 4
    assert flex_range[-3] == 3
    assert flex_range[-4] == 2
    assert flex_range[-5] == 1

    with pytest.raises(IndexError):
        flex_range[-6]


def test_len(flex_range):
    assert len(flex_range) == 5
    assert next(flex_range) == 1
    assert len(flex_range) == 4
    assert next(flex_range) == 2
    assert len(flex_range) == 3
    assert next(flex_range) == 3
    assert len(flex_range) == 2
    assert next(flex_range) == 4
    assert len(flex_range) == 1
    assert next(flex_range) == 5
    assert len(flex_range) == 0
    with pytest.raises(StopIteration):
        next(flex_range)
    assert len(flex_range) == 0


def test_multiple(flex_range):
    assert len(flex_range) == 5
    c = 0
    for n in flex_range:
        assert flex_range[0] == 1
        c += 1
    assert c == 5
    c = 0
    for n in flex_range:
        assert flex_range[0] == 1
        c += 1
    assert c == 5
