import logging
import re

from .models import MajorBody

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _find_separator_index(lines: list[str]) -> int | None:
    """Find the separator line and the starting index of the data rows.

    Args:
        lines: A list of strings from the API output.

    Returns:
        The index of the separator line
        Returns None if the separator can't be found.

    """
    header_line_index = -1
    separator_line_index = -1
    for i, line in enumerate(lines):
        if "ID#" in line and "Name" in line:
            header_line_index = i
        if "-" in line and header_line_index != -1:
            separator_line_index = i
            break

    if separator_line_index == -1 or header_line_index + 1 != separator_line_index:
        return None

    return separator_line_index


def _get_column_boundaries(separator_line: str, column_names: list[str]) -> dict[str, tuple[int, int]] | None:
    """Determine column boundaries from the separator line using its dash groups.

    Args:
        separator_line: The string containing dashes that define column widths.
        column_names: A list of column names to find boundaries for.

    Returns:
        A dictionary mapping column names to their (start, end) boundaries.
        Returns None if the expected number of columns isn't found.

    """
    dash_groups = re.finditer(r"-+", separator_line)
    boundaries = [match.span() for match in dash_groups]

    if len(boundaries) < len(column_names):
        logger.warning("Found only %d columns, expected %d.", len(boundaries), len(column_names))
        return None

    return {name: boundaries[i] for i, name in enumerate(column_names)}


def _parse_row(line: str, column_boundaries: list[tuple[int, int]]) -> MajorBody | None:
    """Parse a single data row string into a MajorBody object.

    Arguments:
        line: The string for a single data row.
        column_boundaries: A list with the start/end boundaries for each column.

    Returns:
        A MajorBody object representing the parsed celestial body, or None if the row is invalid.

    """
    if not line.strip():
        return None

    try:
        body = tuple(line[interval[0] : interval[1]].strip() for interval in column_boundaries)
    except (IndexError, KeyError):  # Line is malformed or shorter than expected
        return None

    if not body:
        return None

    return MajorBody(*body)


def parse_body_table(table_text: str) -> list[MajorBody]:
    """Parse the text output from the NASA/JPL Horizons API into a list of objects.

    This function orchestrates the parsing process by calling helper functions to:
    1. Find the data section.
    2. Determine column boundaries.
    3. Parse each data row individually.

    Arguments:
        table_text: The multi-line string data from the Horizons API.

    Returns:
        A list of dictionaries, where each dictionary represents a celestial body.

    """
    lines = table_text.strip().split("\n")

    column_names = ["id", "name", "designation", "aliases"]
    separator_line_index = _find_separator_index(lines)
    if separator_line_index is None:
        logger.warning("Could not find header or separator line. Unable to parse.")
        return []
    data_start_index = separator_line_index + 1
    column_slices = _get_column_boundaries(lines[separator_line_index], column_names)
    if not column_slices:
        logger.warning("Could not determine column boundaries. Parsing may be incomplete.")
        return []

    data_lines = lines[data_start_index:]

    parsed_objects = []
    for line in data_lines:
        body = _parse_row(line, list(column_slices.values()))
        if body:
            parsed_objects.append(body)

    return parsed_objects
