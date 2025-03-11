from .types import DatabaseError, FlexibleIterator


def format_value(self, field, value):
    """If the field's type is text, surround with quotes.

    Args:
        field (str): Name of the field
        value: The value to format

    Returns:
        str: String to be inserted into an SQL query.
    """
    ft = self.get_field_type(field)

    if ft in self.adapters:
        value = self.adapters[ft](value)

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
    elif ft in ['DATE', 'TIMESTAMP']:
        return f'"{value}"'
    elif ft == 'BLOB' and isinstance(value, bytes):
        return f'x\'{value.hex()}\''
    else:
        return str(value)


def generate_clause(self, clause_spec, operator='AND', full=True, table=None):
    """Generate a string clause based on the clause spec. If full, include the keyword WHERE

    Args:
        clause_spec: If a dict, the keys are the string fieldnames and the values are the values that must match.
                     Otherwise, assume that the clause_spec is the value of the primary key
        operator (str): Operator to link subclauses with. Default is AND.
        full (bool): If true, includes the WHERE string at the beginning.

    Returns:
        str
    """
    if not clause_spec:
        return ''
    pieces = []
    if isinstance(clause_spec, dict):
        for key, value in clause_spec.items():
            if value is None:
                pieces.append(f'{key} IS NULL')
            else:
                pieces.append('{}={}'.format(key, self.format_value(key, value)))
    elif not table:
        raise DatabaseError(f'Need to specify table name for clause_spec type {type(clause_spec)}',
                            f'generate_clause({clause_spec})')
    elif table not in self.primary_key_per_table:
        raise DatabaseError(f'Table {table} does not have a defined primary key', f'generate_clause({clause_spec})')
    else:
        key = self.primary_key_per_table[table]
        pieces.append('{}={}'.format(key, self.format_value(key, clause_spec)))

    clause = f' {operator} '.join(pieces)
    if full:
        return f'WHERE {clause}'
    else:
        return clause


def lookup_all(self, field, table, clause='', distinct=False):
    """Run a SELECT command with the specified field, table and clause, return the matching values.

    Args:
        field (str): Name of field to return
        table (str): Name of table to query
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.
        distinct (bool): If true, add DISTINCT keyword before field name

    Returns:
        iterator: All the values that match the query
    """
    field_s = field if not distinct else f'DISTINCT {field}'
    if not isinstance(clause, str):
        clause = self.generate_clause(clause, table=table)
    return FlexibleIterator(row[0] for row in self.query(f'SELECT {field_s} FROM {table} {clause}'))


def lookup(self, field, table, clause=''):
    """Run a SELECT command and return the first (only?) value.

    Args:
        field (str): Name of field to return
        table (str): Name of table to query
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.

    Returns:
        The value or None"""
    if not isinstance(clause, str):
        clause = self.generate_clause(clause, table=table)
    result = self.query_one(f'SELECT {field} FROM {table} {clause}')
    if result:
        return result[0]


def count(self, table, clause=''):
    """Return the number of results for a given query.

    Args:
        table (str): Name of table to query
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.

    Returns:
        int: Number of rows in the table (that match the clause)
    """
    return self.lookup('COUNT(*)', table, clause)


def dict_lookup(self, key_field, value_field, table, clause=''):
    """Return a dictionary mapping the key_field to the value_field for some query.

    Args:
        key_field (str): The name of the field that should be the key in the dictionary
        value_field (str): The name of the field that should be the value in the dictionary
        table (str): The name of the table to query
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.

    Returns:
        dict: All of the rows returned by the query formatted into a dictionary

    """
    if not isinstance(clause, str):
        clause = self.generate_clause(clause, table=table)
    results = self.query(f'SELECT {key_field}, {value_field} FROM {table} {clause}')
    return {d[key_field]: d[value_field] for d in results}


def table_as_dict(self, table, key_field='id', fields=None, clause=''):
    """Return a dictionary mapping the key_field to the row for some query.

    Args:
        table (str): The name of the table to query
        key_field (str): The name of the field that should be the key in the dictionary
        fields ([str], None): A list of fields for the rows, or if None, use *
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.

    Returns:
        dict: All of the rows returned by the query formatted into a dictionary

    """
    if not isinstance(clause, str):
        clause = self.generate_clause(clause, table=table)
    if fields is None:
        field_s = '*'
    else:
        field_s = ', '.join(fields)
        if key_field not in fields:
            field_s += f', {key_field}'

    results = self.query(f'SELECT {field_s} FROM {table} {clause}')
    return {d[key_field]: d for d in results}


def unique_counts(self, table, ident_field):
    """Return a dictionary mapping the different values of the ident_field column to how many times each appears.

    Args:
        table (str): The name of the table to query
        ident_field (str): The name of the field to count

    Returns:
        dict: All of the unique values of ident_field mapped to an integer count
    """
    return self.dict_lookup(ident_field, 'COUNT(*)', table, 'GROUP BY ' + ident_field)


def sum(self, table, value_field, clause=''):
    """Return the sum of the value_field column.

    Args:
        table (str): The name of the table to query
        value_field (str): The name of the field (presumed to have integer type)
        clause (str/any): Optional clause to add to query. Use generate_clause to translate to str as needed.

    Returns:
        int: The sum of all the values of value_field matching the query.
    """
    return self.lookup(f'SUM({value_field})', table, clause)


def sum_counts(self, table, value_field, ident_field):
    """Return the values of the ident_field column mapped to the sum of the value_field column.

    Args:
        table (str): The name of the table to query
        value_field (str): The name of the value field (presumed to have an integer type)
        ident_field (str): The name of the identifier field, used as the key

    Returns:
        dict: A mapping from all the unique values of ident_field to the sum of all the matching value_field entries
    """
    return self.dict_lookup(ident_field, f'SUM({value_field})', table, 'GROUP BY ' + ident_field)


def insert(self, table, row_dict):
    """Insert the given row into the table.

    Args:
        table (str): The name of the table to insert into
        row_dict (dict): A dictionary where the keys are string field names, and the values are, well, the values

    Returns:
        int: the lastrowid (i.e. probably the primary key of the inserted row)
    """
    n = len(row_dict)
    if n > len(self.tables[table]):
        raise DatabaseError('Too many values in dictionary', f'insert({table}, {row_dict})')
    keys = row_dict.keys()

    values = [row_dict.get(k) for k in keys]
    key_s = ', '.join(keys)

    cur = self.execute(f'INSERT INTO {table} ({key_s}) VALUES({self.q_strings[n]})', values)
    return cur.lastrowid


def bulk_insert(self, table, fields, rows):
    """Insert multiple rows into the table at a time

    Args:
        table (str): The name of the table to insert into
        fields (str[]): The names of the fields
        rows (tuple[]): Each tuple is the values for the fields.
                        The length of each tuple should match the length of fields
    """
    n = len(fields)
    if n > len(self.tables[table]):
        raise DatabaseError('Too many values in dictionary', f'bulk_insert({table}, {fields}, ...)')
    key_s = ', '.join(fields)
    self.execute_many(f'INSERT INTO {table} ({key_s}) VALUES({self.q_strings[n]})', rows)


def update(self, table, row_dict, replace_key='id'):
    """If there's a row where the key value matches the row_dict's value, update it. Otherwise, insert it.

    Args:
        table (str): The name of the table
        row_dict (dict): A dictionary where the keys are string field names, and the values are, well, the values
        replace_key (str/list): If replace_key is a string, then the row where the field matches is updated.
                                Otherwise, it specifies multiple field names that have to match.

    Returns:
        int: The row id of the new or old row (emulating lastrowid)
    """
    if isinstance(replace_key, str):
        clause = self.generate_clause({replace_key: row_dict[replace_key]})
    else:
        clause = self.generate_clause({key: row_dict[key] for key in replace_key})

    existing = self.query_one(f'SELECT * FROM {table} {clause}')
    if not existing:
        # If no matches, just insert
        self.insert(table, row_dict)
        existing = self.query_one(f'SELECT * FROM {table} {clause}')
    else:
        field_qs = []
        values = []
        for k in row_dict.keys():
            if isinstance(replace_key, str) and k == replace_key:
                continue
            elif isinstance(replace_key, (list, dict)) and k in replace_key:
                continue
            values.append(row_dict[k])
            field_qs.append(f'{k}=?')

        if field_qs:
            field_s = ', '.join(field_qs)
            query = f'UPDATE {table} SET {field_s} ' + clause
            self.execute(query, values)

    # Determine proper return
    if table not in self.primary_key_per_table:
        # No primary key, return nothing
        return
    return_key = self.primary_key_per_table[table]

    if return_key in row_dict:
        return row_dict[return_key]
    else:
        return existing[return_key]


def unique_insert(self, table, row_dict):
    """If there's a row where ALL the values match the row_dict's value, do nothing. Otherwise, insert it.

    Args:
        table (str): The name of the table
        row_dict (dict): A dictionary where the keys are string field names, and the values are, well, the values

    Returns:
        int: The row id of the new or old row (emulating lastrowid)
    """
    return self.update(table, row_dict, row_dict.keys())


def delete(self, table, clause=''):
    """Run a DELETE command with the specified table.

    Args:
        table (str): The name of the table
        clause (str/any): Optional clause to add to command. Use generate_clause to translate to str as needed.
    """

    if not isinstance(clause, str):
        clause = self.generate_clause(clause, table=table)
    self.execute(f'DELETE FROM {table} {clause}')
