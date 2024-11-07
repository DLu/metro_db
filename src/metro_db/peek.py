import argparse
import argcomplete
import pathlib
from tabulate import tabulate, multiline_formats

from . import SQLiteDB

try:
    import magic

    def is_database_file(path):
        return magic.from_file(path).startswith('SQLite')
except ModuleNotFoundError:
    def is_database_file(path):
        return path.suffix in ['.db', '.sql']


multiline_formats['fancy_outline'] = 'fancy_outline'  # Hack to fix tabulate bug


def db_path_completer(prefix, **kwargs):
    current = pathlib.Path(prefix)
    folder = current.parent
    pattern = current.name + '*'
    options = []
    for option_path in folder.glob(pattern):
        if option_path.is_file() and is_database_file(option_path):
            options.append(str(option_path))

    return options


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path').completer = db_path_completer
    parser.add_argument('n', nargs='?', default=10, type=int,
                        help='Number of rows of each table to display. -1 for all')
    parser.add_argument('-s', '--style', choices=['simple', 'grid', 'plain', 'fancy_outline'], default='fancy_outline')
    parser.add_argument('-t', '--tables', metavar='table', nargs='+')
    parser.add_argument('-d', '--show-datatypes', action='store_true')
    argcomplete.autocomplete(parser, always_complete_options=False)
    args = parser.parse_args(argv)

    db = SQLiteDB(args.db_path, uri_query='mode=rw')
    db.infer_database_structure()

    for table in db.lookup_all('name', 'sqlite_master', 'WHERE type="table"'):
        if args.tables and table not in args.tables:
            continue
        query = f'SELECT * FROM {table}'
        if args.n >= 0:
            query += f' LIMIT {args.n}'

        results = list(db.query(query))
        headers = []
        for key in db.tables[table]:
            header = key
            if args.show_datatypes:
                header += '\n' + db.get_field_type(key)
            headers.append(header)
        count = db.count(table)
        if args.n >= 0 and count > args.n:
            extra_row = [f'...{count - args.n} more...']
            while len(extra_row) < len(headers):
                extra_row.append('...')
            results.append(extra_row)
        output = tabulate(results, headers=headers, tablefmt=args.style)
        length = max(len(s) for s in output.split('\n'))
        print(('{:^' + str(length) + '}').format(table))
        print(output)
        print()
