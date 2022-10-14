def format_value(self, field, value):
    """If the field's type is text, surround with quotes."""
    ft = self.get_field_type(field)
    if ft == 'TEXT':
        if not isinstance(value, str):
            value = str(value)
        if '"' in value:
            if "'" in value:
                return '"{}"'.format(value.replace('"', '""'))
            else:
                return f"'{value}'"
        else:
            return f'"{value}"'
    elif ft in self.adapters:
        return self.adapters[ft](value)
    else:
        return value


def generate_clause(self, value_dict, operator='AND', full=True):
    """Generate a string clause. If full, include the keyword WHERE"""
    if not value_dict:
        return ''
    pieces = []
    for key, value in value_dict.items():
        pieces.append('{}={}'.format(key, self.format_value(key, value)))

    clause = f' {operator} '.join(pieces)
    return f'WHERE {clause}'


def lookup_all(self, field, table, clause='', distinct=False):
    """Run a SELECT command with the specified field, table and clause, return the matching values."""
    field_s = field if not distinct else f'DISTINCT {field}'
    if not isinstance(clause, str):
        clause = self.generate_clause(clause)
    for row in self.query(f'SELECT {field_s} FROM {table} {clause}'):
        yield row[0]


def lookup(self, field, table, clause=''):
    """Run a SELECT command and return the first (only?) value."""
    if not isinstance(clause, str):
        clause = self.generate_clause(clause)
    result = self.query_one(f'SELECT {field} FROM {table} {clause}')
    if result:
        return result[0]


def count(self, table, clause=''):
    """Return the number of results for a given query."""
    return self.lookup('COUNT(*)', table, clause)


def dict_lookup(self, key_field, value_field, table, clause=''):
    """Return a dictionary mapping the key_field to the value_field for some query."""
    if not isinstance(clause, str):
        clause = self.generate_clause(clause)
    results = self.query(f'SELECT {key_field}, {value_field} FROM {table} {clause}')
    return {d[key_field]: d[value_field] for d in results}


def unique_counts(self, table, ident_field):
    """Return a dictionary mapping the different values of the ident_field column to how many times each appears."""
    return self.dict_lookup(ident_field, 'COUNT(*)', table, 'GROUP BY ' + ident_field)


def sum(self, table, value_field, clause=''):
    """Return the sum of the value_field column."""
    return self.lookup(f'SUM({value_field})', table, clause)


def sum_counts(self, table, value_field, ident_field):
    """Return the values of the ident_field column mapped to the sum of the value_field column."""
    return self.dict_lookup(ident_field, f'SUM({value_field})', table, 'GROUP BY ' + ident_field)


def insert(self, table, row_dict):
    """Insert the given row into the table."""
    keys = row_dict.keys()

    values = [row_dict.get(k) for k in keys]
    key_s = ', '.join(keys)
    n = len(values)

    cur = self.execute(f'INSERT INTO {table} ({key_s}) VALUES({self.q_strings[n]})', values)
    return cur.lastrowid


def bulk_insert(self, table, fields, rows):
    n = len(fields)
    key_s = ', '.join(fields)
    self.execute_many(f'INSERT INTO {table} ({key_s}) VALUES({self.q_strings[n]})', rows)


def update(self, table, row_dict, replace_key='id'):
    """If there's a row where the key value matches the row_dict's value, update it. Otherwise, insert it."""
    if isinstance(replace_key, str):
        clause = self.generate_clause({replace_key: row_dict[replace_key]})
    else:
        clause = self.generate_clause({key: row_dict[key] for key in replace_key})

    if self.count(table, clause) == 0:
        # If no matches, just insert
        return self.insert(table, row_dict)

    field_qs = []
    values = []
    for k in row_dict.keys():
        if k == replace_key:
            continue
        values.append(row_dict[k])
        field_qs.append(f'{k}=?')
    field_s = ', '.join(field_qs)
    query = f'UPDATE {table} SET {field_s} ' + clause
    self.execute(query, values)
    if 'id' in row_dict:
        return row_dict['id']
    else:
        return self.lookup('id', table, clause)
