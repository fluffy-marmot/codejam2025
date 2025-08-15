from js import window  # type: ignore[attr-defined]
from common import Position

from scene_classes import HTMLImageElement
from consolelogger import getLogger

log = getLogger(__name__)


class SpriteSheet:
    """Wrapper for individual sprites with enhanced functionality."""

    def __init__(self, key: str):
        self.key = key.lower()
        self.image: HTMLImageElement = window.sprites[self.key]

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
            log.warning("Frame size is zero for sprite '%s'", self.key)
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
