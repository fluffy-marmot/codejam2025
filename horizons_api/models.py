from dataclasses import dataclass

__all__ = (
    "MajorBody",
    "ObjectData",
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
