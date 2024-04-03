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

    def __repr__(self):
        return str(dict(self))


class FlexibleIterator:
    def __init__(self, iterable):
        self.iterable = iterable
        self.list_form = None
        self.index = 0

    def __iter__(self):
        if self.list_form:
            return self.list_form.__iter__()
        return self

    def __next__(self):
        if self.list_form:
            if self.index < len(self.list_form):
                value = self.list_form[self.index]
                self.index += 1
                return value
            else:
                raise StopIteration()

        return next(self.iterable)

    def __len__(self):
        if self.list_form is None:
            self.list_form = list(self.iterable)
        return len(self.list_form) - self.index

    def __getitem__(self, index):
        if self.list_form is None:
            self.list_form = list(self.iterable)
        return self.list_form[index]

    def __contains__(self, field):
        if self.list_form is None:
            self.list_form = list(self.iterable)
        return field in self.list_form

    def __repr__(self):
        if self.list_form is None:
            self.list_form = list(self.iterable)
        return str(self.list_form)
