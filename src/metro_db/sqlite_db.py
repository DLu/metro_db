import sqlite3
import datetime

from .types import DatabaseError, Row, FlexibleIterator

PYTHON_SQL_TYPE_TRANSLATION = {
    'int': 'INTEGER',
    'float': 'REAL',
    'str': 'TEXT',
    'datetime': 'TIMESTAMP',
    'bytes': 'BLOB',
}


class SQLiteDB:
    """Core database structure that handles base sqlite3 interactions"""

    def __init__(self, database_path, default_type='str', primary_keys=['id'], uri_query=None):
        """
        Args:
            database_path (pathlib.Path): File to store the data
            default_type (str): The default SQL type to use
            primary_keys (list of strings): Fields that should automatically be marked as primary keys
            uri_query (str|None): If specified, the query string to use in the URI [1]

        [1] https://docs.python.org/3/library/sqlite3.html#how-to-work-with-sqlite-uris
        """
        if uri_query:
            self.target = f'file:{database_path}?{uri_query}'
            uri = True
        else:
            self.target = str(database_path)
            uri = False
        try:
            self.raw_db = sqlite3.connect(self.target, uri=uri, detect_types=sqlite3.PARSE_DECLTYPES)
        except sqlite3.OperationalError as e:
            raise DatabaseError(str(e), self.target) from None
        self.path = database_path
        self.raw_db.row_factory = Row

        self.tables = {}
        self.field_types = {}
        self.default_type = default_type
        self.primary_keys = list(primary_keys)
        self.primary_key_per_table = {}
        self.adapters = {}
        self.converters = {}
        self.register_custom_type('bool', bool, int, lambda v: bool(int(v)))

        # Default Converters and Adapters are deprecated in Python 3.12
        # https://discuss.python.org/t/deprecate-default-built-in-sqlite3-converters-and-adapters/15781
        self.register_custom_type('TIMESTAMP', datetime.datetime,
                                  lambda dt: dt.isoformat(),
                                  lambda s: datetime.datetime.fromisoformat(s.decode()),
                                  )
        self.register_custom_type('DATE', datetime.date,
                                  lambda dt: dt.isoformat(),
                                  lambda s: datetime.date.fromisoformat(s.decode()),
                                  )

        self.q_strings = {}

    def register_custom_type(self, name, type_, adapter_fn, converter_fn):
        """Register a non-standard datatype.

        Args:
            name (str): The name of the custom type
            type_ (class): Python type
            adapter_fn (function): Translates the Python type to the sqlite3 type
            converter_fn (function): Translates the sqlite3 to the Python type
        """
        self.adapters[name] = adapter_fn
        self.converters[name] = converter_fn
        sqlite3.register_adapter(type_, adapter_fn)
        sqlite3.register_converter(name, converter_fn)

    def register_custom_enum(self, custom_enum_class):
        """Register an IntEnum

        Args:
            custom_enum_class (IntEnum): Class type of enum to register
        """
        self.register_custom_type(custom_enum_class.__name__,
                                  custom_enum_class,
                                  lambda d: d.value,
                                  lambda v: custom_enum_class(int(v)))

    def query_one(self, query):
        """Run the specified query and return the first result

        Args:
            query (str): SQL query to execute

        Returns:
            Row or None: The result of the query
        """
        try:
            cursor = self.raw_db.cursor()
            cursor.execute(query)
            return cursor.fetchone()
        except sqlite3.OperationalError as e:
            raise DatabaseError(str(e), query) from None

    def query(self, query):
        """Run the specified query and return the results

        Args:
            query (str): SQL query to execute

        Returns:
            Iterator(Row): The results of the query
        """
        try:
            cursor = self.raw_db.cursor()
            return FlexibleIterator(cursor.execute(query))
        except (sqlite3.Error, ValueError) as e:
            raise DatabaseError(str(e), query) from None

    def execute(self, command, params=()):
        """Execute the given command with the parameters. Returns the cursor

        Args:
            command (str): SQL command to execute
            params (tuple): values to substitute into the placeholders

        Returns:
            Cursor: sqlite3 cursor for getting additional info like lastrowid
        """
        try:
            cur = self.raw_db.cursor()
            cur.execute(command, params)
            return cur
        except (sqlite3.Error, ValueError) as e:
            raise DatabaseError(str(e), command, params) from None

    def execute_many(self, command, objects):
        """Execute the given command multiple times.

        Args:
            command (str): SQL command to execute
            objects (list of tuples): The given command is run for each object/set of placeholder values
        """
        try:
            self.raw_db.executemany(command, objects)
        except (sqlite3.Error, ValueError) as e:
            raise DatabaseError(str(e), command, objects) from None

    def get_field_type(self, field, full=False):
        """Return a string representing the type of a given field.

        Args:
            field (str): The name of the field
            full (bool): If True, it returns other elements that would be used in the column definition
                         (i.e. PRIMARY KEY)
        Returns:
            str: SQL type for the given field
        """
        base = self.field_types.get(field, self.default_type)
        if base in self.converters:
            sql_type = base
        elif base in PYTHON_SQL_TYPE_TRANSLATION:
            sql_type = PYTHON_SQL_TYPE_TRANSLATION[base]
        else:
            sql_type = base.upper()

        if not full or field not in self.primary_keys:
            return sql_type
        else:
            return sql_type + ' PRIMARY KEY'

    def get_sql_table_types(self, table):
        """Create a dictionary mapping the name of each field in the table to its type in the actual db

        Args:
            table (str): Name of the table to get information about

        Returns:
            dict[str/str]: a mapping from field name to sql
        """
        type_map = {}
        for row in self.query(f'PRAGMA table_info("{table}")'):
            type_map[row['name']] = row['type']
        return type_map

    def update_database_structure(self):
        """Create or update the structure of all tables."""
        self.primary_key_per_table = {}
        for table, keys in self.tables.items():
            # Check if table exists
            table_exists = self.count('sqlite_master', f"WHERE type='table' AND name='{table}'") > 0
            if not table_exists:
                self.create_table(table, keys)
            else:
                self.update_table(table, keys)

            # Save primary key
            for key in keys:
                if key in self.primary_keys:
                    self.primary_key_per_table[table] = key

        if not self.tables:
            return

        # Cache strings consisting of a number of comma separated question marks
        for n in range(1, max(len(k) for k in self.tables.values()) + 1):
            self.q_strings[n] = ', '.join(['?'] * n)

    def create_table(self, table, keys):
        """Create a table with the given name and fields

        Args:
            table (str): Name of the table
            keys (str[]): Names of the fields
        """
        types = []
        for key in keys:
            tt = self.get_field_type(key, full=True)
            types.append(f'{key} {tt}')
        type_s = ', '.join(types)
        self.execute(f'CREATE TABLE {table} ({type_s})')

    def update_table(self, table, keys, field_mappings={}):
        """Update a table to have the given keys while preserving the data.

        Args:
            table (str): Name of the table
            keys (str[]): Keys that the table should have after this operation
            field_mappings (dict[str/str]): Mapping of new field names to old field names.
        """
        self.tables[table] = keys
        type_map = self.get_sql_table_types(table)

        fields_to_add = []
        old_fields = []
        new_fields = []
        needs_restructure = False

        for key in keys:
            if key in field_mappings:
                old_fields.append(field_mappings[key])
                new_fields.append(key)
                needs_restructure = True
            elif key in type_map:
                old_fields.append(key)
                new_fields.append(key)

                if type_map[key] != self.get_field_type(key):
                    needs_restructure = True
            else:
                fields_to_add.append(key)

                if key in self.primary_keys:
                    needs_restructure = True

        fields_to_remove = set(type_map.keys()) - set(keys)
        needs_restructure = needs_restructure or len(fields_to_remove)

        if not needs_restructure:
            # Can alter the table in-place
            for field in fields_to_add:
                tt = self.get_field_type(field, full=True)
                self.execute(f'ALTER TABLE {table} ADD COLUMN {field} {tt}')
            return

        temp_table_name = f'{table}_x'
        self.execute(f'ALTER TABLE {table} RENAME TO {temp_table_name}')
        self.create_table(table, self.tables[table])

        old_fields_s = ', '.join(old_fields)
        new_fields_s = ', '.join(new_fields)
        command = f'INSERT INTO {table}({new_fields_s}) SELECT {old_fields_s} FROM {temp_table_name}'
        self.execute(command)
        self.execute(f'DROP TABLE {temp_table_name}')

    def infer_database_structure(self):
        """Use the existing database entries to infer the tables and field_types"""
        for table in self.lookup_all('name', 'sqlite_master', "WHERE type='table'"):
            type_dict = self.get_sql_table_types(table)
            self.tables[table] = list(type_dict.keys())
            for field, type_name in type_dict.items():
                if type_name != self.default_type:
                    self.field_types[field] = type_name

    # Bonus "syntactic sugar" is provided in queries.py
    from ._queries import lookup_all, lookup, count, dict_lookup, unique_counts, sum_counts, insert, bulk_insert
    from ._queries import format_value, generate_clause, sum, update, unique_insert, table_as_dict

    def reset(self, table=None):
        """Clear all or some of the data out of the database and recreate the table(s).

        Args:
            table (str/None): If specified, the name of the table to reset. Otherwise, all tables are reset.
        """
        db = self.raw_db.cursor()
        if table is None:
            tables = list(self.tables.keys())
        else:
            tables = [table]

        for table in tables:
            db.execute(f'DROP TABLE IF EXISTS {table}')

        self.update_database_structure()

    def write(self):
        """Commit the changes to the file."""
        self.raw_db.commit()

    def close(self, print_table_sizes=True):
        """Write data to database. Possibly print the number of rows in each table.

        Args:
            print_table_sizes (bool): Whether to print the table sizes
        """
        if print_table_sizes:
            print(self)
        self.write()
        self.raw_db.close()

    def dispose(self):
        """Used in tests to close the database and remove the file."""
        self.close(print_table_sizes=False)
        self.path.unlink()

    def __repr__(self):
        """String representing the number of rows in each table.

        Returns:
            str: the name and size of each table on its own row
        """
        s = ''
        for table in self.tables:
            s += f'{table}({self.count(table)})\n'
        return s
