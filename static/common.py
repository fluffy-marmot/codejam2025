from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class Rect:
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int


class Position(NamedTuple):
    x: float
    y: float
