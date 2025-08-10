from dataclasses import dataclass
from datetime import datetime

__all__ = (
    "MajorBody",
    "ObjectData",
    "TimePeriod",
    "VectorData",
)


@dataclass
class MajorBody:
    """Represents a major body in the solar system."""

    id: str
    name: str | None = None
    designation: str | None = None
    aliases: str | None = None


@dataclass
class ObjectData:
    """Represents physical characteristics of a celestial body."""

    radius: float | None = None


@dataclass
class VectorData:
    """Represents position and velocity vectors."""

    x: float
    y: float
    z: float | None = None


@dataclass
class TimePeriod:
    """Represents a time period for ephemeris data."""

    start: datetime
    end: datetime
    step: str = "2d"
