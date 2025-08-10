import logging
import re
from abc import ABC, abstractmethod

from .exceptions import ParsingError
from .models import MajorBody, ObjectData, VectorData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for all parsers."""

    @abstractmethod
    def parse(self, text: str) -> object:
        """Parse the given text and return structured data."""
        raise NotImplementedError


class MajorBodyTableParser(BaseParser):
    """Parse a table of major bodies from the Horizons API."""

    def parse(self, text: str) -> list[MajorBody]:
        """Parse the text output from the NASA/JPL Horizons API into a list of objects.

        This function orchestrates the parsing process by calling helper methods to:
        1. Find the data section.
        2. Determine column boundaries.
        3. Parse each data row individually.

        Arguments:
            text: The multi-line string data from the Horizons API.

        Returns:
            A list of MajorBody objects.

        """
        lines = text.strip().split("\n")

        separator_line_index = self._find_separator_index(lines)
        if separator_line_index is None:
            logger.warning("Could not find header or separator line. Unable to parse.")
            return []
        data_start_index = separator_line_index + 1
        data_end_index = self._find_data_end_index(lines, data_start_index)
        column_boundaries = self._get_column_boundaries(lines[separator_line_index])
        if not column_boundaries:
            logger.warning("Could not determine column boundaries. Parsing may be incomplete.")
            return []

        data_lines = lines[data_start_index:data_end_index]

        parsed_objects = []
        for line in data_lines:
            body = self._parse_row(line, column_boundaries)
            if body:
                parsed_objects.append(body)

        return parsed_objects

    def _find_separator_index(self, lines: list[str]) -> int | None:
        """Find the separator line and the starting index of the data rows."""
        header_line_index = -1
        separator_line_index = -1
        for i, line in enumerate(lines):
            if "ID#" in line and "Name" in line:
                header_line_index = i
            if "---" in line and header_line_index != -1:
                separator_line_index = i
                break

        if separator_line_index == -1 or header_line_index + 1 != separator_line_index:
            return None

        return separator_line_index

    def _find_data_end_index(self, lines: list[str], start_index: int) -> int:
        """Find the end index of the data rows."""
        for i in range(start_index, len(lines)):
            if not lines[i].strip():
                return i
        return len(lines)

    def _get_column_boundaries(self, separator_line: str) -> list[tuple[int, int]] | None:
        """Determine column boundaries from the separator line using its dash groups."""
        dash_groups = re.finditer(r"-+", separator_line)
        return [match.span() for match in dash_groups]

    def _parse_row(self, line: str, column_boundaries: list[tuple[int, int]]) -> MajorBody | None:
        """Parse a single data row string into a MajorBody object."""
        if not line.strip():
            return None

        try:
            body_data = [line[start:end].strip() for start, end in column_boundaries]
        except IndexError:  # Line is malformed or shorter than expected
            return None

        if not body_data or not body_data[0]:
            return None

        return MajorBody(*body_data)


class ObjectDataParser(BaseParser):
    """Parses the physical characteristics of an object."""

    def parse(self, text: str) -> ObjectData:
        """Parse the text to find the object's radius."""
        radius_match = re.search(r"Radius \(km\)\s*=\s*([\d\.]+)", text)
        radius = float(radius_match.group(1)) if radius_match else None
        return ObjectData(radius=radius)


class VectorDataParser(BaseParser):
    """Parses vector data from the API response."""

    def parse(self, text: str) -> VectorData | None:
        """Parse the text to find X, Y, and Z vector components."""
        # TODO: should probably add error checking for the re searches and horizons queries
        # looking for patterns like "X =-2367823E+10" or "Y = 27178E-02" since the API returns coordinates
        # in scientific notation
        pattern = r"\s*=\s*(-?[\d\.]+E[\+-]\d\d)"
        x_match = re.search("X" + pattern, text)
        y_match = re.search("Y" + pattern, text)
        z_match = re.search("Z" + pattern, text)

        if not (x_match and y_match and z_match):
            msg = "Failed to find all vector components in the text."
            logger.warning(msg)
            raise ParsingError(msg)

        return VectorData(x=float(x_match.group(1)), y=float(y_match.group(1)), z=float(z_match.group(1)))
