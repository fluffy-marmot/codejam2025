from typing import Any, TypedDict, TYPE_CHECKING
from js import window  # type: ignore[attr-defined] 

if TYPE_CHECKING:
    from controls import GameControls
    from player import Player, Scanner
    from asteroid import AsteroidAttack
    from debris import DebrisSystem
    from audio import AudioHandler
    from common import HTMLImageElement, CanvasRenderingContext2D
    
from common import Position


class SpriteSheet:
    """Wrapper for individual sprites with enhanced functionality."""

    def __init__(self, key: str, image: 'HTMLImageElement'):
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

class SpritesInterface:
    """Interface for accessing window.sprites with SpriteSheet wrapping."""
    
    def __init__(self, js_window: Any) -> None:
        self._window = js_window
    
    def __getitem__(self, key: str) -> "SpriteSheet":
        """Access sprites as SpriteSheet objects."""
        return SpriteSheet(key, self._window.sprites[key])

class PlanetData(TypedDict, total=False):
    """Type definition for planet data from planets.json"""
    id: int
    name: str
    sprite: str
    x: float
    y: float
    info: str
    level: list[str]
    spritesheet: SpriteSheet  # JS Image object added in HTML


class WindowInterface:
    """Typed interface for accessing window object properties with dynamic fallback."""
    
    def __init__(self, js_window: Any) -> None:
        self._window = js_window
        self._sprites = SpritesInterface(js_window)  # Wrap sprites in SpritesInterface
        self.DEBUG_DRAW_HITBOXES: bool = getattr(js_window, "DEBUG_DRAW_HITBOXES", False)
        self.audio_handler = js_window.audio_handler

    @property
    def audio_handler(self) -> "AudioHandler":
        return self._window.audio_handler

    @audio_handler.setter
    def audio_handler(self, value: "AudioHandler") -> None:
        self._window.audio_handler = value
    
    @property
    def controls(self) -> "GameControls":
        return self._window.controls
    
    @controls.setter
    def controls(self, value: "GameControls") -> None:
        self._window.controls = value
    
    @property
    def player(self) -> "Player":
        return self._window.player
    
    @player.setter
    def player(self, value: "Player") -> None:
        self._window.player = value
    
    @property
    def asteroids(self) -> "AsteroidAttack":
        return self._window.asteroids
    
    @asteroids.setter
    def asteroids(self, value: "AsteroidAttack") -> None:
        self._window.asteroids = value
    
    @property
    def debris(self) -> "DebrisSystem":
        return self._window.debris
    
    @debris.setter
    def debris(self, value: "DebrisSystem") -> None:
        self._window.debris = value
    
    @property
    def scanner(self) -> "Scanner":
        return self._window.scanner
    
    @scanner.setter
    def scanner(self, value: "Scanner") -> None:
        self._window.scanner = value
    
    @property
    def planets(self) -> list[PlanetData]:
        return self._window.planets
    
    @planets.setter
    def planets(self, value: list[PlanetData]) -> None:
        self._window.planets = value
    
    @property
    def sprites(self) -> SpritesInterface:
        """Access sprites as SpriteSheet objects."""
        return self._sprites
    
    def get_sprite(self, key: str) -> SpriteSheet:
        """Get a sprite by key - more intuitive than sprites[key]."""
        return self._sprites[key]
    
    def __getattr__(self, name: str) -> Any:
        """Dynamic fallback for accessing any window property."""
        return getattr(self._window, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Dynamic fallback for setting any window property."""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            setattr(self._window, name, value)


# Create typed interface instance
window_interface = WindowInterface(window)

# Expose for backward compatibility
window = window_interface
