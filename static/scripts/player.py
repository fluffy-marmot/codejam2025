from js import window  # type: ignore[attr-defined]

from math import dist
from collections import deque
from common import Position
from consolelogger import getLogger
from scene_classes import SceneObject
from sprites import SpriteSheet
from asteroid import Asteroid
import math

log = getLogger(__name__)

FULL_HEALTH = 1000

class Player(SceneObject):
    """Controllable player sprite.

    Exposed globally as window.player so other modules can use it.
    Movement keys: WASD or Arrow keys.
    """

    def __init__(
        self, 
        sprite: SpriteSheet, 
        bar_icon: SpriteSheet, 
        x: float, 
        y: float, 
        speed: float = 100.0, 
        scale: float = 0.1, 
        hitbox_scale: float = 0.5, 
    ):
        super().__init__()

        self.health = FULL_HEALTH
        self.health_history = deque([FULL_HEALTH] * 200)
        self.sprite = sprite
        self.set_position(x, y)
        self.default_pos = (x, y)
        self.speed = speed
        self.momentum = [0, 0]
        self.scale = scale
        self._half_w = 0
        self._half_h = 0
        self.hitbox_scale = hitbox_scale
        self.rotation = 0.0          # rotation in radians
        self.target_rotation = 0.0
        self.max_tilt = math.pi / 8  # Maximum tilt angle (22.5 degrees)
        self.rotation_speed = 8.0 
        self.is_moving = False
        self.is_disabled = False
        self.bar_icon = bar_icon
        self.active = True

    def _update_sprite_dims(self):
        w = self.sprite.width
        h = self.sprite.height
        if w and h:
            self._half_w = (w * self.scale) / 2
            self._half_h = (h * self.scale) / 2

    def update(self, timestamp: float):
        """Update player position based on pressed keys.

        dt: time delta (seconds)
        controls: GameControls instance for key state
        """
        if not self.sprite:
            return

        # update sprite dimensions if needed
        if not self._half_w or not self._half_h:
            self._update_sprite_dims()

        keys = window.controls.pressed
        dx = dy = 0.0
        if not self.is_disabled:
            if "w" in keys or "ArrowUp" in keys:
                dy -= 1
            if "s" in keys or "ArrowDown" in keys:
                dy += 1
            if "a" in keys or "ArrowLeft" in keys:
                dx -= 1
            if "d" in keys or "ArrowRight" in keys:
                dx += 1

        # TODO: remove this, for testing momentum
        if "m" in keys:
            self.momentum[0] = self.momentum[1] = 5
        # DEBUG: switch hitbox visibility
        if "c" in keys:
            window.DEBUG_DRAW_HITBOXES = not window.DEBUG_DRAW_HITBOXES

        # miliseconds to seconds since that's what was being used
        dt = (timestamp - self.last_timestamp) / 1000
        
        # Update target rotation based on horizontal movement
        if dx < 0:  # Moving left
            self.target_rotation = -self.max_tilt  # Tilt left
        elif dx > 0:  # Moving right
            self.target_rotation = self.max_tilt   # Tilt right
        else:
            self.target_rotation = 0.0
        
        # Smoothly interpolate current rotation toward target
        rotation_diff = self.target_rotation - self.rotation
        self.rotation += rotation_diff * self.rotation_speed * dt
        
        if dx or dy:
            # normalize diagonal movement
            mag = (dx * dx + dy * dy) ** 0.5
            dx /= mag
            dy /= mag
            self.x += dx * self.speed * dt
            self.y += dy * self.speed * dt

            self.is_moving = True
        else:
            self.is_moving = False

        # update player position based on momentum (after they were hit and bumped by an asteroid)
        if self.momentum[0] or self.momentum[1]:
            self.x += self.momentum[0] * self.speed * dt
            self.y += self.momentum[1] * self.speed * dt
            self.momentum[0] *= 0.97
            self.momentum[1] *= 0.97
            if abs(self.momentum[0]) < 0.5: self.momentum[0] = 0
            if abs(self.momentum[1]) < 0.5: self.momentum[1] = 0

        # clamp inside canvas
        canvas = getattr(window, "gameCanvas", None)
        if canvas and self._half_w and self._half_h:
            max_x = canvas.width - self._half_w
            max_y = canvas.height - self._half_h
            self.x = min(max(self._half_w, self.x), max_x)
            self.y = min(max(self._half_h, self.y), max_y)

    def render(self, ctx, timestamp):
        if not self.sprite:
            log.debug("Player render: no sprite")
            return

        self.update(timestamp)

        if not self._half_w or not self._half_h:
            self._update_sprite_dims()

        scaled_w = self._half_w * 2
        scaled_h = self._half_h * 2

        # Save the canvas state before applying rotation
        ctx.save()
        
        # Move to player center and apply rotation
        ctx.translate(self.x, self.y)
        ctx.rotate(self.rotation)
        
        # Draw sprite centered at origin
        ctx.drawImage(self.sprite.image, -self._half_w, -self._half_h, scaled_w, scaled_h)

        # Debug draw hitbox
        if getattr(window, "DEBUG_DRAW_HITBOXES", False):
            ctx.strokeStyle = "white"
            ctx.lineWidth = 2
            ctx.strokeRect(-self._half_w, -self._half_h, scaled_w, scaled_h)
        
        # Restore canvas state (removes rotation and translation)
        ctx.restore()
        
        # Collision detection (done after restore so it's in world coordinates)
        if self.active:
            for asteroid in window.asteroids.asteroids:
                self.check_collision(asteroid)

        self.render_health_bar(ctx)

        super().render(ctx, timestamp)

    def render_health_bar(self, ctx):
        outer_width = window.canvas.width // 4
        outer_height = 12
        inner_width = outer_width - 4
        inner_height = outer_height - 4
        padding = 30

        ctx.drawImage(
                self.bar_icon.image,
                window.canvas.width - outer_width - padding - 30,
                window.canvas.height - outer_height - padding - 2,
            )
        
        ctx.lineWidth = 1
        ctx.strokeStyle = "#FFFFFF"
        ctx.strokeRect(
            window.canvas.width - outer_width - padding, 
            window.canvas.height - outer_height - padding,
            outer_width, 
            outer_height
        )

        ctx.fillStyle = "#FF0000"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2, 
            window.canvas.height - outer_height - padding + 2,
            inner_width * self.health_history.popleft() / FULL_HEALTH,
            inner_height
        )
        self.health_history.append(self.health)

        ctx.fillStyle = "#00FF00"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2, 
            window.canvas.height - outer_height - padding + 2,
            inner_width * self.health / FULL_HEALTH,
            inner_height
        )
    
    def check_collision(self, asteroid: Asteroid):
        # skip if asteroid is too far in the background
        if asteroid.size < asteroid.target_size * 0.70: return

        ast_x, ast_y, ast_radius = asteroid.get_hit_circle()
        player_x_min, player_x_max = self.x - self._half_w, self.x + self._half_w
        player_y_min, player_y_max = self.y - self._half_h, self.y + self._half_h

        hitbox_closest_x = max(player_x_min, min(ast_x, player_x_max))
        hitbox_closest_y = max(player_y_min, min(ast_y, player_y_max))

        # if the closest point on the rectangle is inside the asteroid's circle, we have collision:
        if (hitbox_closest_x - ast_x) ** 2 + (hitbox_closest_y - ast_y) ** 2 < ast_radius ** 2:
            distance_between_centers = dist((ast_x, ast_y), (self.x, self.y))
            self.momentum[0] = (self.x - ast_x) / distance_between_centers * 5.0
            self.momentum[1] = (self.y - ast_y) / distance_between_centers * 5.0
            self.health = max(0, self.health - 100 / distance_between_centers * 5)
            window.audio_handler.play_bang()
            window.debris.generate_debris(self.get_position(), Position(ast_x, ast_y))

    def get_hit_circle(self) -> tuple[float, float, float]:
        """Get the hit circle for the player"""
        if not self._half_w or not self._half_h:
            self._update_sprite_dims()
        r = min(self._half_w, self._half_h) * self.hitbox_scale
        return (self.x, self.y, r)

    def get_aabb(self) -> tuple[float, float, float, float]:
        """Get the axis-aligned bounding box (AABB) for the player"""
        if not self._half_w or not self._half_h:
            self._update_sprite_dims()
        hw = self._half_w * self.hitbox_scale
        hh = self._half_h * self.hitbox_scale
        return (self.x - hw, self.y - hh, self.x + hw, self.y + hh)

    def reset_position(self):
        self.x, self.y = self.default_pos
        self.rotation = 0.0
        self.target_rotation = 0.0

class Scanner:
    def __init__(self, sprite: SpriteSheet, player: Player, scale: float = 0.1,
                 disable_ship_ms: float = 1000, beamwidth=100, scanning_dur_s=5):
        self.sprite = sprite
        self.scale = scale
        self.player = player
        self.scaled_w = self.sprite.width * self.scale
        self.scaled_h = self.sprite.height * self.scale
        self.disable_ship_ms = disable_ship_ms
        self.disable_timer = 0
        self.beamwidth = beamwidth
        self.scanningdur = scanning_dur_s * 1000  # ms
        self.scanning_progress = 0                
        self.bar_max = self.scanningdur
        self.last_scan_tick = None                 
        self.finished = False #when the bar is full
        self.scanning = False

    def render_beam(self, ctx): #seprate function so it can go under the planet
        player_x, player_y = self.player.get_position()
        ctx.fillStyle = "rgba(255, 0, 0, 0.5)"
        origin_x = player_x - 175
        origin_y = player_y - 15
        ctx.beginPath()
        ctx.moveTo(origin_x, origin_y)
        ctx.lineTo(0, player_y - self.beamwidth)
        ctx.moveTo(origin_x, origin_y)
        ctx.lineTo(0, player_y + self.beamwidth)
        ctx.lineTo(0, player_y - self.beamwidth)
        ctx.fill()

    def render(self, ctx, current_time):
        "renders the scanner sprite and the bar"
        player_x, player_y = self.player.get_position()
        keys = window.controls.pressed

        if " " in keys and not self.player.is_moving:
            self.scanning = True
            # scanner image
            ctx.drawImage(
                self.sprite.image,
                player_x - 175,
                player_y - 25,
                self.scaled_w,
                self.scaled_h
            )

            self.player.is_disabled = True

            if self.last_scan_tick is None:
                self.last_scan_tick = current_time

            elapsed_since_last = current_time - self.last_scan_tick
            self.scanning_progress = min(self.scanning_progress + elapsed_since_last, self.bar_max)
            self.last_scan_tick = current_time


        else:
            self.last_scan_tick = None
            self.scanning = False

        if current_time - self.disable_timer >= self.disable_ship_ms:
            self.disable_timer = current_time
            if " " not in keys:
                self.player.is_disabled = False

        # progress bar
        outer_width = window.canvas.width // 4
        outer_height = 12
        inner_width = outer_width - 4
        inner_height = outer_height - 4
        padding = 30

        ctx.drawImage(
                self.sprite.image,
                window.canvas.width - outer_width - padding - 30,
                window.canvas.height + outer_height - padding - 2,
                16,
                16
            )
        
        ctx.lineWidth = 1
        ctx.strokeStyle = "#FFFFFF"
        ctx.strokeRect(
            window.canvas.width - outer_width - padding,
            window.canvas.height + outer_height - padding,
            outer_width,
            outer_height
        )

        ctx.fillStyle = "#FF0000"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2,
            window.canvas.height + outer_height - padding + 2,
            inner_width * self.scanning_progress / self.bar_max,
            inner_height
        )

        if self.scanning_progress >= self.bar_max and not self.finished:
            log.debug("Scanner progress complete")
            self.finished = True
    def reset_bar(self):
        self.scanning_progress = 0