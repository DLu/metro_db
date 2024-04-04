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
    def __contains__(self, field):
        return field in self.keys()

    def get(self, field, default_value=None):
        if field in self:
            return self[field]
        else:
            return default_value

    def items(self):
        for field in self.keys():
            yield field, self[field]

    def __repr__(self):
        return str(dict(self))
