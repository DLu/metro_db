import sqlite3


class DatabaseError(sqlite3.Error):
    def __init__(self, error_s, command, parameters=None):
        s = f'{error_s}\nCommand: {command}'
        if parameters:
            s += f'\n\t{parameters}'
        sqlite3.Error.__init__(self, s)
        self.command = command
        self.parameters = parameters


class Row(sqlite3.Row):
    def __repr__(self):
        return str(dict(self))
