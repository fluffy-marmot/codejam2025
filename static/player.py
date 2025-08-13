from js import window  # type: ignore
from consolelogger import getLogger

log = getLogger(__name__)

class Player:
    """Controllable player sprite.

    Exposed globally as window.player so other modules can use it.
    Movement keys: WASD or Arrow keys.
    """

    def __init__(self, sprite, x: float, y: float, speed: float = 100.0, scale: float = 0.1):
        self.sprite = sprite
        self.x = x
        self.y = y
        self.speed = speed
        self.scale = scale 
        self._half_w = 0
        self._half_h = 0

    def _update_sprite_dims(self):
        w = getattr(self.sprite, "width", 0) or 0
        h = getattr(self.sprite, "height", 0) or 0
        if w and h:
            self._half_w = (w * self.scale) / 2
            self._half_h = (h * self.scale) / 2

    def update(self, dt: float, controls):
        """Update player position based on pressed keys.

        dt: time delta (seconds)
        controls: GameControls instance for key state
        """
        if not self.sprite:
            return

        # update sprite dimensions if needed
        if not self._half_w or not self._half_h:
            self._update_sprite_dims()

        keys = controls.pressed
        dx = dy = 0.0
        if "w" in keys or "ArrowUp" in keys:
            dy -= 1
        if "s" in keys or "ArrowDown" in keys:
            dy += 1
        if "a" in keys or "ArrowLeft" in keys:
            dx -= 1
        if "d" in keys or "ArrowRight" in keys:
            dx += 1

        if dx or dy:
            # normalize diagonal movement
            mag = (dx * dx + dy * dy) ** 0.5
            dx /= mag
            dy /= mag
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

        # clamp inside canvas
        canvas = getattr(window, "gameCanvas", None)
        if canvas and self._half_w and self._half_h:
            max_x = canvas.width - self._half_w
            max_y = canvas.height - self._half_h
            self.x = min(max(self._half_w, self.x), max_x)
            self.y = min(max(self._half_h, self.y), max_y)

    def render(self, ctx):
        if not self.sprite:
            log.debug("Player render: no sprite")
            return
        
        if not self._half_w or not self._half_h:
            self._update_sprite_dims()
        
        draw_x = self.x - self._half_w
        draw_y = self.y - self._half_h
        scaled_w = self._half_w * 2
        scaled_h = self._half_h * 2
        log.debug("Drawing player at (%s,%s) size=%sx%s", draw_x, draw_y, scaled_w, scaled_h)
        ctx.drawImage(self.sprite, draw_x, draw_y, scaled_w, scaled_h)
        # # outline for visibility
        # ctx.strokeStyle = "white"  # type: ignore[attr-defined]
        # ctx.lineWidth = 2  # type: ignore[attr-defined]
        # ctx.strokeRect(draw_x, draw_y, scaled_w, scaled_h)  # type: ignore[attr-defined]

    def set_position(self, x: float, y: float):
        self.x = x
        self.y = y
        
    def get_position(self):
        return [self.x, self.y]
