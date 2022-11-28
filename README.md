# MetroDB
A wrapper around the sqlite3 database for easy database development

The overall goal is to write less SQL and more Python.

## Installation
[![PyPI version](https://badge.fury.io/py/metro_db.svg)](https://badge.fury.io/py/metro_db)

    sudo pip3 install metro_db

## Documentation
[![readthedocs badget](https://readthedocs.org/projects/metro_db/badge/?version=latest)](http://metro_db.readthedocs.org/)

[Read the primary documentation here](http://metro_db.readthedocs.org/)

## Overview

Table/column definitions can be specified via source-controllable YAML files. e.g.

    tables:
        people:
            - name
            - age
            - grade
            - present
    types:
        # default type is text
        age: int
        grade: float
        present: bool

Loading the above YAML will result in the following SQL command to be run:

    CREATE TABLE people (name TEXT, age INTEGER, grade REAL, present bool)

The resulting table will be easier to manipulate as well. For example, consider the following `sqlite3` commands.

    cursor = db.cursor()
    cursor.execute('INSERT INTO people (name, age, grade, present) VALUES(?, ?, ?, ?)', ['David', 25, 98.7, 1])

The equivalent MetroDB command would be a simpler one-liner:

    db.insert('people', {'name': 'David', 'age': 25, 'grade': 98.7, 'present': True})

## Continuous Integration
[![Build Status](https://app.travis-ci.com/DLu/metro_db.svg?branch=main)](https://app.travis-ci.com/DLu/metro_db)
