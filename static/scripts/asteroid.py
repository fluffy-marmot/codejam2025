import math
import random

from js import document, window  # type: ignore[attr-defined]

# Canvas dimensions
canvas = document.getElementById("gameCanvas")
container = document.getElementById("canvasContainer")
SCREEN_W, SCREEN_H = container.clientWidth, container.clientHeight

ASTEROID_SHEET = window.sprites["asteroids"]

# "magic numbers" obtained via a script in assets/make_spritesheets.py, end of the printout
ASTEROID_RADII = [22, 26, 18, 19, 21, 25, 18, 23, 26, 20, 24, 13, 22, 18, 21, 23, 30, 19, 18, 18, 18, 21, 26, 
                  20, 21, 16, 24, 22, 18, 25, 18, 20, 19, 21, 22, 18, 24, 20, 23, 20, 22, 20, 24, 17, 16, 16, 
                  18, 21, 17, 22, 24, 25, 14, 24, 25, 14, 22, 23, 21, 18, 20, 18, 18, 19, 24, 23, 23, 27, 19, 
                  24, 25, 20, 23, 21, 25, 22, 19, 25, 21, 16, 30, 26, 24, 30, 23, 21, 20, 18, 25, 16, 24, 21, 
                  23, 18, 21, 24, 20, 23, 29, 20, 24, 22, 22, 19]


class Asteroid:
    def __init__(self, sheet, x, y, vx, vy, target_size_px, sprite_index, grid_cols=11, cell_size=0):
        self.sheet = sheet
        self.x = x
        self.y = y
        self.velocity_x = vx
        self.velocity_y = vy
        self.rotation = 0.0
        self.rotation_speed = random.uniform(-0.5, 0.5)
        self.target_size = target_size_px
        self.size = 5.0
        self.grow_rate = target_size_px / random.uniform(3.0, 9.0)
        self.sprite_index = sprite_index
        self.grid_cols = grid_cols
        self.cell_size = cell_size
        self.hitbox_scale = 0.45
        self.hitbox_radius = ASTEROID_RADII[sprite_index]
        self._last_timestamp = None
        self.linger_time = 0.5
        self.full_size_reached_at = None

    def _ensure_cell_size(self):
        if not self.cell_size:
            width = getattr(self.sheet, "width", 0) or 0
            if width:
                self.cell_size = max(1, int(width // self.grid_cols))

    def _src_rect(self):
        self._ensure_cell_size()
        col = self.sprite_index % self.grid_cols
        row = self.sprite_index // self.grid_cols
        x = col * self.cell_size
        y = row * self.cell_size
        return x, y, self.cell_size, self.cell_size

    def update(self, timestamp: float):
        if self._last_timestamp is None:
            self._last_timestamp = timestamp
            return
        dt = (timestamp - self._last_timestamp) / 1000.0  # seconds
        self._last_timestamp = timestamp

        # Movement
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.rotation += self.rotation_speed * dt

        # Growth towards target size
        if self.size < self.target_size:
            self.size = self.size + self.grow_rate * dt
            if self.size >= self.target_size:
                self.full_size_reached_at = timestamp

    def render(self, ctx, timestamp_ms: float):
        self.update(timestamp_ms)
        self._ensure_cell_size()
        if not self.cell_size:
            return

        x, y, w, h = self._src_rect()
        size = self.size

        ctx.save()
        ctx.translate(self.x, self.y)
        ctx.rotate(self.rotation)

        # Draw centered
        ctx.drawImage(self.sheet, x, y, w, h, -size / 2, -size / 2, size, size)

        # Debug hit circle
        if getattr(window, "DEBUG_DRAW_HITBOXES", False):
            ctx.beginPath()
            ctx.strokeStyle = "#FF5555"
            ctx.lineWidth = 2
            ctx.arc(0, 0, size * self.hitbox_radius / 100 * 1, 0, 2 * math.pi)
            ctx.stroke()
        ctx.restore()

    def is_off_screen(self, w=SCREEN_W, h=SCREEN_H, margin=50) -> bool:
        return self.x < -margin or self.x > w + margin or self.y < -margin or self.y > h + margin

    def get_hit_circle(self):
        return (self.x, self.y, self.size * self.hitbox_radius / 100 * 1)

    def should_be_removed(self):
        """Check if asteroid should be removed (off screen or lingered too long)"""
        if self.is_off_screen():
            return True
        if self.full_size_reached_at and (self._last_timestamp - self.full_size_reached_at) > (
            self.linger_time * 1000
        ):
            return True
        return False


class AsteroidAttack:
    def __init__(self, spritesheet, width: int, height: int, max_size_px: float, spawnrate: int = 500):
        self.sheet = spritesheet
        self.w = width
        self.h = height
        self.max_size = max_size_px or 256
        self.spawnrate = spawnrate
        self.asteroids: list[Asteroid] = []
        self._last_spawn = 0.0
        self.max_asteroids = 50
        self.cell_size = 0

    def _spawn_one(self):
        # Don't spawn if at the limit
        if len(self.asteroids) >= self.max_asteroids:
            return

        # Planet area (left side)
        planet_width = self.w * 0.3
        space_start_x = planet_width + 50

        x = random.uniform(space_start_x, self.w)
        y = random.uniform(0, self.h)

        if x < (SCREEN_W / 2):
            velocity_x = random.uniform(-15, -5)
            if y < (SCREEN_H / 2):
                velocity_y = random.uniform(-15, -5)
            else:
                velocity_y = random.uniform(5, 15)
        else:
            velocity_x = random.uniform(5, 15)
            if y < (SCREEN_H / 2):
                velocity_y = random.uniform(-15, -5)
            else:
                velocity_y = random.uniform(5, 15)

        target = random.uniform(self.max_size * 0.7, self.max_size * 1.3)
        idx = random.randint(0, 103)  # randint is inclusive on both ends
        a = Asteroid(self.sheet, x, y, velocity_x, velocity_y, target, idx)
        self.asteroids.append(a)

    # Spawn at interval and only if under limit
    def spawn_and_update(self, timestamp: float):
        # adjust spawnrate by a random factor so asteroids don't spawn at fixed intervals
        spawnrate = self.spawnrate * random.uniform(0.2, 1.0)
        # slow down spawnrate for this attempt a bit if there already many asteroids active
        spawnrate = spawnrate * max(1, 1 + (len(self.asteroids) - 35) * 0.1)
        if self._last_spawn == 0.0 or (timestamp - self._last_spawn) >= spawnrate:
            if len(self.asteroids) < self.max_asteroids:
                self._last_spawn = timestamp
                self._spawn_one()

        # Remove asteroids
        before_count = len(self.asteroids)
        self.asteroids = [a for a in self.asteroids if not a.should_be_removed()]
        after_count = len(self.asteroids)

        # If we removed asteroids, we can spawn new ones
        if after_count < before_count:
            self._last_spawn = timestamp - (self.spawnrate * 0.7)

    def update_and_render(self, ctx, timestamp: float):
        self.spawn_and_update(timestamp)
        for a in self.asteroids:
            a.render(ctx, timestamp)

    def reset(self):
        self.asteroids.clear()
        self._last_spawn = 0.0
        self.cell_size = 0
