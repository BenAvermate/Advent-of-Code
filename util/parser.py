def parse_by_line(input_string):
    yield from input_string.splitlines()

def parse_by_paragraph(input_string):
    paragraphs = input_string.split("\n\n")
    for paragraph in paragraphs:
        yield paragraph

def parse_to_grid(input_string, row_delimiter="\n", col_delimiter=""):
    rows = parse_by_line(input_string)
    grid = []
    for row in rows:
        if col_delimiter:
            grid.append(row.split(col_delimiter))
        else:
            grid.append(list(row))
    return grid

def parse_to_coordinates(input_string, empty_value):
    rows = parse_by_line(input_string)
    coordinates = {}
    for y, row in enumerate(rows):
        for x, value in enumerate(row):
            if value != empty_value:
                coordinates[complex(x, y)] = value
    return coordinates