from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class Rect:
    left: float
    top: float
    width: float
    height: float

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


class Position(NamedTuple):
    x: float
    y: float
