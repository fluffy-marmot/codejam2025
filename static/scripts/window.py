"""Typed wrapper over window and stored objects

Use instead of importing directly from js

Usage
-------
from window import window
"""

from typing import TYPE_CHECKING, Any

from js import window  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from asteroid import AsteroidAttack
    from audio import AudioHandler
    from common import HTMLImageElement
    from controls import GameControls
    from debris import DebrisSystem
    from player import Player, Scanner

from common import SpriteSheet, AsteroidData, PlanetData


class SpritesInterface:
    """Interface for accessing window.sprites with SpriteSheet wrapping."""

    def __init__(self, js_window: Any) -> None:
        self._window = js_window

    def __getitem__(self, key: str) -> "SpriteSheet":
        """Access sprites as SpriteSheet objects."""
        return SpriteSheet(key, self._window.sprites[key])


class WindowInterface:
    """Typed interface for accessing window object properties with dynamic fallback.
    
    Sprites, AudioHandler, and Planets are internally managed and changes to them are not
    reflected in the underlying JS objects. Other properties are accessed directly from the JS
    window object.
    """

    def __init__(self, js_window: Any) -> None:
        self._window = js_window    
        self._sprites = SpritesInterface(js_window)  # Wrap sprites in SpritesInterface
        self.DEBUG_DRAW_HITBOXES: bool = getattr(js_window, "DEBUG_DRAW_HITBOXES", False)
        self.audio_handler = js_window.audio_handler
        self._planet_dataclasses: dict[str, PlanetData] = {}
        self._serialize_planets()

    def _serialize_planets(self) -> None:
        """Convert raw planet data from JS to PlanetData dataclass instances."""
        raw_planets = getattr(self._window, 'planets', [])
        self._planet_dataclasses = {}

        for planet_dict in raw_planets:
            planet = PlanetData.from_dict(planet_dict)
            self._planet_dataclasses[planet.name] = planet

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
    def planets(self) -> dict[str, PlanetData]:
        return self._planet_dataclasses

    @planets.setter
    def planets(self, value: dict[str, PlanetData]) -> None:
        self._planet_dataclasses = value

    def get_planet(self, name: str) -> PlanetData | None:
        return self._planet_dataclasses.get(name.title())

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
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            setattr(self._window, name, value)


# Create typed interface instance
window_interface = WindowInterface(window)

# Expose for backward compatibility
window = window_interface
