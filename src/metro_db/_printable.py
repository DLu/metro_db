from tabulate import tabulate, multiline_formats

multiline_formats['fancy_outline'] = 'fancy_outline'  # Hack to fix tabulate bug


def print_table(self, table_name, num_rows=10, show_datatypes=False, style='fancy_outline'):
    query = f'SELECT * FROM {table_name}'
    if num_rows >= 0:
        query += f' LIMIT {num_rows}'
    results = list(self.query(query))
    headers = []
    for key in self.tables[table_name]:
        header = key
        if show_datatypes:
            header += '\n' + self.get_field_type(key)
        headers.append(header)
    count = self.count(table_name)

    extra_rows = num_rows >= 0 and count > num_rows
    if extra_rows:
        results.append([''] * len(headers))

    output = tabulate(results, headers=headers, tablefmt=style)
    lines = output.split('\n')
    length = max(len(s) for s in lines)
    print(('{:^' + str(length) + '}').format(table_name))
    for i, line in enumerate(lines):
        if i == len(lines) - 2 and extra_rows:
            msg = f'...and {count - num_rows:,} more rows'
            line = line[:2] + msg + line[2+len(msg):]
        print(line)
    print()
