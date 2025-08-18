import math
import time
from collections import deque
from dataclasses import dataclass
from math import dist

from asteroid import Asteroid
from common import Position
from consolelogger import getLogger
from scene_classes import SceneObject
from window import SpriteSheet, window

log = getLogger(__name__)

class Player(SceneObject):
    """Controllable player sprite.

    Exposed globally as window.player so other modules can use it.
    Movement keys: WASD or Arrow keys.
    """

    FULL_HEALTH = 1000

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

        self.health = Player.FULL_HEALTH
        self.health_history = deque([Player.FULL_HEALTH] * 200)
        self.sprite = sprite
        self.set_position(x, y)
        self.default_pos = (x, y)
        self.speed = speed
        self.momentum = [0, 0]
        self.scale = scale
        self._half_w = 0
        self._half_h = 0
        self.hitbox_scale = hitbox_scale
        self.rotation = 0.0  # rotation in radians
        self.target_rotation = 0.0
        self.max_tilt = math.pi / 8  # Maximum tilt angle (22.5 degrees)
        self.rotation_speed = 8.0
        self.is_moving = False
        self.is_disabled = False
        self.bar_icon = bar_icon
        self.active = True
        self.invincible = False

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
        # DEBUG: instant death for testing
        if "k" in keys:
            self.health = 0

        # miliseconds to seconds since that's what was being used
        dt = (timestamp - self.last_timestamp) / 1000

        # Update target rotation based on horizontal movement
        if dx < 0:  # Moving left
            self.target_rotation = -self.max_tilt  # Tilt left
        elif dx > 0:  # Moving right
            self.target_rotation = self.max_tilt  # Tilt right
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
            if abs(self.momentum[0]) < 0.5:
                self.momentum[0] = 0
            if abs(self.momentum[1]) < 0.5:
                self.momentum[1] = 0

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
        if window.DEBUG_DRAW_HITBOXES:
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
            outer_height,
        )

        ctx.fillStyle = "#FF0000"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2,
            window.canvas.height - outer_height - padding + 2,
            inner_width * self.health_history.popleft() / Player.FULL_HEALTH,
            inner_height,
        )
        self.health_history.append(self.health)

        ctx.fillStyle = "#00FF00"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2,
            window.canvas.height - outer_height - padding + 2,
            inner_width * self.health / Player.FULL_HEALTH,
            inner_height,
        )

    def check_collision(self, asteroid: Asteroid):
        # skip if asteroid is too far in the background
        if asteroid.size < asteroid.target_size * 0.70:
            return
        # use invicible flag (toggled when planet is done)
        if self.invincible:
            return

        ast_x, ast_y, ast_radius = asteroid.get_hit_circle()
        player_x_min, player_x_max = self.x - self._half_w, self.x + self._half_w
        player_y_min, player_y_max = self.y - self._half_h, self.y + self._half_h

        hitbox_closest_x = max(player_x_min, min(ast_x, player_x_max))
        hitbox_closest_y = max(player_y_min, min(ast_y, player_y_max))

        # if the closest point on the rectangle is inside the asteroid's circle, we have collision:
        if (hitbox_closest_x - ast_x) ** 2 + (hitbox_closest_y - ast_y) ** 2 < ast_radius**2:
            distance_between_centers = dist((ast_x, ast_y), (self.x, self.y))
            # log.debug("Asteroid collision with distance %s", distance_between_centers)
            asteroid.health -= max(80, 240 - distance_between_centers)
            # Make Newton proud
            self.momentum[0] = (self.x - ast_x) / distance_between_centers * 5.0
            self.momentum[1] = (self.y - ast_y) / distance_between_centers * 5.0
            asteroid.velocity_x += (ast_x - self.x) / 2.0
            asteroid.velocity_y += (ast_y - self.y) / 2.0
            self.health = max(0, self.health - 100 / distance_between_centers * 5 * asteroid.damage_mul)
            
            # Reduce scanner progress when hit by asteroid
            if hasattr(window, 'scanner') and window.scanner:
                # Reduce progress by 2-6% of max progress based on damage taken
                damage_taken = 100 / distance_between_centers * 5 * asteroid.damage_mul
                progress_loss = window.scanner._bar_max * (0.02 + (damage_taken / 1000) * 0.04)
                window.scanner.scanning_progress = max(0, window.scanner.scanning_progress - progress_loss)
                # log.debug("Scanner progress reduced by %f due to asteroid collision", progress_loss)
            
            window.audio_handler.play_bang()
            window.debris.generate_debris(self.get_position(), Position(ast_x, ast_y))

    def nudge_towards(self, pos: Position, momentum_amount: float) -> None:
        distance = self.get_position().distance(pos)
        if distance == 0: return

        x_dir = (pos.x - self.x) / distance
        y_dir = (pos.y - self.y) / distance

        self.x += x_dir * 0.75
        self.y += y_dir * 0.75

        # x_dir = math.cos((pos.x - self.x )/(pos.y - self.y))
        # y_dir = math.sin((pos.x - self.x )/(pos.y - self.y))

        # if abs(self.momentum[0]) < 1:
        #     self.momentum[0] += x_dir * momentum_amount
        # if abs(self.momentum[1]) < 1:
        #     self.momentum[1] += y_dir * momentum_amount

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


@dataclass
class ScanStatus:
    active: bool = False  # Whether the scan is active
    too_close: bool = False  # Whether the scan is valid
    player_interrupted: bool = False  # Whether the scan was interrupted
    locked: bool = False  # Whether the scan is locked

    @property
    def valid(self):
        return not self.too_close and not self.player_interrupted and not self.locked


class Scanner:
    def __init__(
        self,
        sprite: SpriteSheet,
        player: Player,
        min_x: float,
        scan_mult: float = 1,
        scale: float = 0.1,
        disable_ship_ms: float = 1000,
        beamwidth=100,
        scanning_dur_s=15,
    ):
        self.sprite = sprite
        self.scale = scale
        self.player = player
        self.min_x = min_x
        self.disable_ship_ms = disable_ship_ms
        self.disable_timer = 0
        
        # Core scanning parameters
        self.scanning_dur_ms = scanning_dur_s * 1000
        self.scan_mult = scan_mult
        self.beamwidth = beamwidth
        
        # State variables
        self.status = ScanStatus()
        self.scanning_progress = 0
        self.finished = False
        self._last_scan_tick = None
        
        # Calculate max based on current parameters
        self._update_bar_max()
    
    def _update_bar_max(self):
        """Update the maximum progress value based on current parameters"""
        self._bar_max = self.scanning_dur_ms * self.scan_mult

    def set_scan_parameters(self, scan_mult: float | None = None, scanning_dur_s: float | None = None):
        """Update scanning parameters and recalculate max value"""
        if scan_mult is not None:
            self.scan_mult = scan_mult
        if scanning_dur_s is not None:
            self.scanning_dur_ms = scanning_dur_s * 1000
        self._update_bar_max()

    def update(self, ctx, current_time):
        if self.finished:
            return

        keys = window.controls.pressed

        self.status.active = " " in keys
            
        self.status.too_close = self.player.x <= self.min_x
        self.status.player_interrupted = self.player.momentum != [0, 0]
        
        # Lock if interrupted and stay locked until released
        if self.status.player_interrupted:
            self.status.locked = True
        elif not self.status.active:
            self.status.locked = False

        if self.status.active and self.status.valid:
            self.player.is_disabled = True

            if self._last_scan_tick is None:
                self._last_scan_tick = current_time

            elapsed_since_last = current_time - self._last_scan_tick
            self.scanning_progress = min(self.scanning_progress + elapsed_since_last, self._bar_max)
            self._last_scan_tick = current_time
        else:
            self._last_scan_tick = None

        # Re-enable player if disable_time has elapsed or player is not scanning
        if current_time - self.disable_timer >= self.disable_ship_ms or not self.status.active:
            if " " not in keys:
                self.player.is_disabled = False
                self.disable_timer = current_time

    def render_beam(self, ctx):  # seprate function so it can go under the planet
        if not self.status.active or not self.status.valid:
            window.audio_handler.play_scan(pause_it=True)
            return
        
        window.audio_handler.play_scan()

        player_x, player_y = self.player.get_position()
        origin_x = player_x - 150
        origin_y = player_y - 10

        # Create animated pulsing effect based on time
        pulse = (math.sin(time.time() * 8) + 1) / 2  # 0 to 1
        beam_alpha = 0.3 + pulse * 0.3  # Vary alpha from 0.3 to 0.6

        # Create gradient for the beam
        gradient = ctx.createLinearGradient(origin_x, origin_y, 0, player_y)
        gradient.addColorStop(0, f"rgba(255, 100, 100, {beam_alpha})")
        gradient.addColorStop(0.5, f"rgba(255, 50, 50, {beam_alpha * 0.8})")
        gradient.addColorStop(1, f"rgba(255, 0, 0, {beam_alpha * 0.5})")

        # Main beam cone
        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.moveTo(origin_x, origin_y)
        ctx.lineTo(0, player_y - self.beamwidth)
        ctx.lineTo(0, player_y + self.beamwidth)
        ctx.closePath()
        ctx.fill()

        # Add animated scanning lines
        scan_cycle = (time.time() * 2) % 1  # 0 to 1, cycling every 0.5 seconds
        num_lines = 5

        for i in range(num_lines):
            line_progress = (scan_cycle + i * 0.2) % 1
            line_x = origin_x - line_progress * origin_x
            line_alpha = (1 - line_progress) * 0.8
            beam_height = self.beamwidth

            if line_alpha > 0.1:  # Only draw visible lines
                ctx.strokeStyle = f"rgba(255, 255, 255, {line_alpha})"
                ctx.lineWidth = 2
                ctx.beginPath()
                ctx.moveTo(line_x, player_y - beam_height)
                ctx.lineTo(line_x, player_y + beam_height)
                ctx.stroke()

        # Add edge glow effect
        ctx.strokeStyle = f"rgba(255, 150, 150, {beam_alpha * 0.6})"
        ctx.lineWidth = 3
        ctx.beginPath()
        ctx.moveTo(origin_x, origin_y)
        ctx.lineTo(0, player_y - self.beamwidth)
        ctx.moveTo(origin_x, origin_y)
        ctx.lineTo(0, player_y + self.beamwidth)
        ctx.stroke()

    def render(self, ctx, current_time):
        "Renders the scanner sprite and the progress bar"
        player_x, player_y = self.player.get_position()
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
            16,
        )

        ctx.lineWidth = 1
        ctx.strokeStyle = "#FFFFFF"
        ctx.strokeRect(
            window.canvas.width - outer_width - padding,
            window.canvas.height + outer_height - padding,
            outer_width,
            outer_height,
        )

        ctx.fillStyle = "#FF0000"
        ctx.fillRect(
            window.canvas.width - outer_width - padding + 2,
            window.canvas.height + outer_height - padding + 2,
            inner_width * self.scanning_progress / self._bar_max,
            inner_height,
        )

        if self.finished:
            return

        if self.status.active:
            if self.status.valid:
                scaled_w = self.sprite.width * self.scale
                scaled_h = self.sprite.height * self.scale
                ctx.drawImage(self.sprite.image, player_x - 175, player_y - 25, scaled_w, scaled_h)
            elif self.status.too_close:
                ctx.fillStyle = "white"
                ctx.font = "15px Courier New"
                ctx.fillText("Too close to planet!", player_x - 90, player_y - 50)

        if self.scanning_progress >= self._bar_max:
            log.debug(f"Done scanning")
            self.status.active = False
            self.finished = True

    def reset(self):
        self.finished = False
        self.scanning_progress = 0
        self._update_bar_max()
        
class PlayerExplosion():
    def __init__(self):
        self.explosion_sprite = window.get_sprite("Explosion Animation")
        self.active = False
        self.current_frame = 0
        self.frame_count = 11  # Number of frames
        self.frame_duration = 100  # milliseconds per frame
        self.last_frame_time = 0
        self.position = (0, 0)
        self.scale = 4.0
        self.finished = False
    
    def start_explosion(self, x: float, y: float):
        """Start the explosion animation at the given position"""
        self.active = True
        self.current_frame = 0
        self.position = (x, y)
        self.last_frame_time = 0
        self.finished = False
    
    def update(self, timestamp: float):
        """Update the explosion animation"""
        if not self.active or self.finished:
            return
        
        if timestamp - self.last_frame_time >= self.frame_duration:
            self.current_frame += 1
            self.last_frame_time = timestamp
            
            if self.current_frame >= self.frame_count:
                self.finished = True
                self.active = False
    
    def render(self, ctx, timestamp: float):
        """Render the current explosion frame"""
        if not self.active or self.finished:
            return
        
        self.update(timestamp)
        
        frame_width = self.explosion_sprite.width // self.frame_count
        frame_height = self.explosion_sprite.height
        
        source_x = self.current_frame * frame_width
        source_y = 0
        
        scaled_width = frame_width * self.scale
        scaled_height = frame_height * self.scale
        
        ctx.drawImage(
            self.explosion_sprite.image,
            source_x, source_y, frame_width, frame_height,  # source rectangle
            self.position[0] - scaled_width/2, self.position[1] - scaled_height/2,  # destination position
            scaled_width, scaled_height  # destination size
        )
