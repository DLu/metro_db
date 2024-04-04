import argparse
from tabulate import tabulate, multiline_formats

from . import SQLiteDB

multiline_formats['fancy_outline'] = 'fancy_outline'  # Hack to fix tabulate bug


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path')
    parser.add_argument('n', nargs='?', default=10, type=int,
                        help='Number of rows of each table to display. -1 for all')
    parser.add_argument('-s', '--style', choices=['simple', 'grid', 'plain', 'fancy_outline'], default='fancy_outline')
    args = parser.parse_args(argv)

    db = SQLiteDB(args.db_path)
    db.infer_database_structure()

    for table in db.lookup_all('name', 'sqlite_master', 'WHERE type="table"'):
        query = f'SELECT * FROM {table}'
        if args.n >= 0:
            query += f' LIMIT {args.n}'

        results = list(db.query(query))
        headers = []
        for key in db.tables[table]:
            type_name = db.get_field_type(key)
            headers.append(f'{key}\n({type_name})')
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
