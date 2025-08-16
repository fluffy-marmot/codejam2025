from common import Rect
from scene_classes import SceneObject
from sprites import SpriteSheet


class SpaceMass(SceneObject):
    def __init__(self, spritesheet: SpriteSheet, mass: float, radius: float, init_velocity: float) -> None:
        super().__init__()

        self.spritesheet = spritesheet
        self.name = spritesheet.key

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
        self.complete = False

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
            self.current_frame = (self.current_frame + 1) % self.spritesheet.num_frames
            self.animation_timer = timestamp

        bounds = self.get_bounding_box()
        frame_position = self.spritesheet.get_frame_position(self.current_frame)
        ctx.drawImage(
            self.spritesheet.image,
            frame_position.x,
            frame_position.y,
            self.spritesheet.frame_size,
            self.spritesheet.frame_size,
            bounds.left,
            bounds.top,
            bounds.width,
            bounds.height,
        )
        if self.complete:
            highlight = "#00ff00"
        else:
            highlight = "#ffff00"  # yellow highlight
            
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

            # draw planet name labels when hovering over
            ctx.shadowBlur = 0
            ctx.beginPath()
            ctx.moveTo(center_x, center_y - radius)
            ctx.lineTo(center_x + 10, center_y - radius - 10)
            ctx.font = "14px Courier New"
            ctx.fillStyle = highlight
            text_width = ctx.measureText(self.name.capitalize()).width
            ctx.lineTo(center_x + 15 + text_width, center_y - radius - 10)
            ctx.fillText(self.name.capitalize(), center_x + 15, center_y - radius - 15)
            ctx.stroke()

            ctx.restore()

        super().render(ctx, timestamp)
