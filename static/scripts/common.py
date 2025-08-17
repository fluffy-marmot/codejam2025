from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Any

HTMLImageElement = Any
CanvasRenderingContext2D = Any

@dataclass
class Rect:
    left: float
    top: float
    width: float
    height: float

    def __iter__(self) -> Iterator[float]:
        yield self.left
        yield self.top
        yield self.width
        yield self.height

    def contains(self, point: Position) -> bool:
        return self.left <= point.x <= self.right and self.top <= point.y <= self.bottom

    @property
    def right(self) -> float:
        return self.left + self.width

    @right.setter
    def right(self, value: float) -> None:
        self.left = value - self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    @bottom.setter
    def bottom(self, value: float) -> None:
        self.top = value - self.height


@dataclass
class Position:
    x: float
    y: float

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __add__(self, other_pos: Position) -> Position:
        return Position(self.x + other_pos.x, self.y + other_pos.y)

    def midpoint(self, other_pos: Position) -> Position:
        return Position((self.x + other_pos.x) / 2, (self.y + other_pos.y) / 2)

    def distance(self, other_pos: Position) -> float:
        return ((self.x - other_pos.x) ** 2 + (self.y - other_pos.y) ** 2) ** 0.5


@dataclass
class PlanetState:
    """State for planet"""

    mass: float
    radius: float
    initial_velocity: float = 0.0
    x: float = 0
    y: float = 0
    angle: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
