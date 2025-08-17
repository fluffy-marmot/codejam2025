from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

HTMLImageElement = Any
CanvasRenderingContext2D = Any

@dataclass
class AsteroidData:
    """Dataclass for asteroid data from asteroids.json. Difficulty stuff is on a 1-20 scale"""
    
    count: int
    speed: int
    damage: int
    durability: int

@dataclass
class PlanetData:
    """Dataclass for planet data from planets.json"""
    
    id: int
    name: str
    sprite: str
    x: float = 0.0
    y: float = 0.0
    info: str = ""
    level: list[str] = field(default_factory=list)
    scan_multiplier: float = 1.0
    asteroid: AsteroidData | None = None
    spritesheet: SpriteSheet | None = None  # JS Image object added in HTML
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlanetData':
        """Create PlanetData from dictionary, handling nested asteroid data."""
        data = data.copy()
        # Handle nested asteroid data
        asteroid_data = None
        if 'asteroid' in data:
            asteroid_dict = data.pop('asteroid')  # Remove from data to avoid duplicate in **data
            asteroid_data = AsteroidData(**asteroid_dict)
        
        # Create instance with unpacked dictionary
        return cls(asteroid=asteroid_data, **data)

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


class SpriteSheet:
    """Wrapper for individual sprites with enhanced functionality."""

    def __init__(self, key: str, image: "HTMLImageElement"):
        self.key = key.lower()
        self.image = image

    @property
    def height(self):
        """Height of the sprite image."""
        return self.image.height

    @property
    def width(self):
        """Width of the sprite image."""
        return self.image.width

    @property
    def frame_size(self):
        """Size of each frame (assuming square frames)."""
        return self.height

    @property
    def is_loaded(self):
        return self.height > 0 and self.width > 0

    @property
    def num_frames(self):
        """Number of frames in the spritesheet."""
        if not self.is_loaded:
            return 1
        return self.width // self.frame_size

    def get_frame_position(self, frame: int) -> Position:
        """Get the position of a specific frame in the spritesheet with overflow handling."""
        if self.num_frames == 0:
            return Position(0, 0)
        frame_index = frame % self.num_frames
        x = frame_index * self.frame_size
        return Position(x, 0)

    # Delegate other attributes to the underlying image
    def __getattr__(self, name):
        return getattr(self.image, name)
