from typing import overload

from common import Position, Rect
from scene_classes import SceneObject

class SpaceMass(SceneObject):
    def __init__(
        self, name: str, spritesheet, mass: float, radius: float, init_velocity: float, num_frames=50
    ) -> None:
        super().__init__()

        self.name = name
        self.spritesheet = spritesheet
        self.num_frames = num_frames
        self.mass = mass
        self.radius = radius
        self.initial_velocity = init_velocity
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_delay = 135  # (approximately 6 FPS)
        self.x = 0
        self.y = 0
        self.highlighted = False

    @overload
    def set_position(self, x: float, y: float): ...

    @overload
    def set_position(self, x: Position): ...

    def set_position(self, x, y=None):
        if y is not None:
            self.x = x
            self.y = y
        else:
            self.x = x.x
            self.y = x.y

    def get_position(self) -> Position:
        return Position(self.x, self.y)

    def get_bounding_box(self) -> Rect:
        # Scale sprite based on radius
        sprite_size = int(self.radius) / 80.0
        frame_size = self.spritesheet.height

        left = self.x - frame_size // 2 * sprite_size
        top = self.y - frame_size // 2 * sprite_size
        size = frame_size * sprite_size

        return Rect(left, top, size, size)

    def render(self, ctx, timestamp):
        # Update animation timing
        if timestamp - self.animation_timer >= self.frame_delay:
            self.current_frame = (self.current_frame + 1) % self.num_frames
            self.animation_timer = timestamp

        # assuming they're square, not best way to go about this, but we're using square sprites so far
        frame_size = self.spritesheet.height
        bounds = self.get_bounding_box()

        ctx.drawImage(
            self.spritesheet,
            frame_size * self.current_frame,  # left in spritesheet
            0,
            frame_size,
            frame_size,
            bounds.left,
            bounds.top,
            bounds.width,
            bounds.height,
        )

        highlight = "#ffff00" # yellow highlight
        offset = 5
        # Draw highlight effect if planet is highlighted
        if self.highlighted:
            ctx.save()
            ctx.strokeStyle = highlight 
            ctx.shadowColor = highlight
            ctx.lineWidth = 3
            ctx.shadowBlur = 10
            
            # Draw a circle around the planet
            center_x = bounds.left + bounds.width / 2
            center_y = bounds.top + bounds.height / 2
            radius = bounds.width / 2 + offset  # Slightly larger than the planet

            ctx.beginPath()
            ctx.arc(center_x, center_y, radius, 0, 2 * 3.14159)
            ctx.stroke()
            ctx.restore()

        super().render(ctx, timestamp)
