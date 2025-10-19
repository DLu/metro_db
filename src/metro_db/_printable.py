from tabulate import tabulate, multiline_formats

multiline_formats['fancy_outline'] = 'fancy_outline'  # Hack to fix tabulate bug


def get_max_line_width(lines):
    return max(len(s) for s in lines)


def fit_to_width(headers, results, max_width, style):
    for number_of_columns in range(len(headers), 0, -1):
        i_headers = headers[:number_of_columns]
        i_results = [list(row[:number_of_columns]) for row in results]
        if number_of_columns < len(headers):
            i_headers += [f'...\nand\n{len(headers)-number_of_columns:,}\nmore\ncols']
            for i_result in i_results:
                i_result.append('')

        output = tabulate(i_results, headers=i_headers, tablefmt=style)
        if max_width is None or get_max_line_width(output.split('\n')) <= max_width:
            return output


def print_table(self, table_name, num_rows=10, hide_datatypes=False, style='fancy_outline', max_width=None):
    query = f'SELECT * FROM {table_name}'
    if num_rows >= 0:
        query += f' LIMIT {num_rows}'
    results = list(self.query(query))
    headers = []
    for key in self.tables[table_name]:
        header = key
        if not hide_datatypes:
            type_ = self.get_field_type(key)
            header += f'\n({type_})'
        headers.append(header)

    output = fit_to_width(headers, results, max_width, style)
    lines = output.split('\n')
    length = get_max_line_width(lines)
    # Print header
    print(('{:^' + str(length) + '}').format(table_name))

    # Print most of the table
    print('\n'.join(lines[:-1]))

    # Print "and more rows" as needed
    count = self.count(table_name)
    if num_rows >= 0 and count > num_rows:
        line = lines[-2]
        lc = line[0]
        blank_line = ''.join((lc if c == lc else ' ') for c in line)
        msg = f'...and {count - num_rows:,} more rows'
        line = blank_line[:2] + msg + blank_line[2+len(msg):]
        print(line)

    # Print last line
    print(lines[-1])
    print()
