import argparse
import argcomplete
import pathlib

from . import SQLiteDB

try:
    import magic

    def is_database_file(path):
        return magic.from_file(path).startswith('SQLite')
except ModuleNotFoundError:
    def is_database_file(path):
        return path.suffix in ['.db', '.sql']


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

        db.print_table(table, args.n, args.show_datatypes, args.style)
