__all__ = ("HorizonsAPIError", "ParsingError")


class HorizonsAPIError(Exception):
    """Base exception for Horizons API errors."""


class ParsingError(Exception):
    """Base exception for parsing errors."""
