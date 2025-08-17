from common import PlanetState, Rect
from consolelogger import getLogger
from scene_classes import SceneObject
from sprites import SpriteSheet

log = getLogger(__name__)


class SpaceMass(SceneObject):
    def __init__(self, spritesheet: SpriteSheet, orbit_state: PlanetState, planet_scene_state: PlanetState) -> None:
        super().__init__()

        self.spritesheet = spritesheet
        self.name = spritesheet.key

        self.state: PlanetState = orbit_state
        self._saved_state: PlanetState = planet_scene_state

        self.x = self.state.x
        self.y = self.state.y

        self.current_frame = 0
        self.animation_timer = 0
        self.frame_delay = 135  # (approximately 6 FPS)

        self.highlighted = False
        self.complete = False

        # State management

    def get_bounding_box(self) -> Rect:
        # Scale sprite based on radius
        sprite_size = int(self.state.radius) / 80.0
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
            if self.complete:
                log.debug("planet complete")
                highlight = "#00ff00"
            else:
                log.debug("planet not complete")
                highlight = "#ffff00"  # yellow highlight
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

    def switch_view(self) -> None:
        """Configure planet view"""
        self.state.x, self.state.y = self.x, self.y
        self.state, self._saved_state = self._saved_state, self.state
        self.x, self.y = self.state.x, self.state.y
        self.highlighted = False  # Clear highlighting when switching views
