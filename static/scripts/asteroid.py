import math
import random

from js import document  # type: ignore[attr-defined]
from common import Position, PlanetData
from scene_classes import SceneObject
from window import window, SpriteSheet
from consolelogger import getLogger

log = getLogger(__name__)

# Canvas dimensions
canvas = document.getElementById("gameCanvas")
container = document.getElementById("canvasContainer")
SCREEN_W, SCREEN_H = container.clientWidth, container.clientHeight

ASTEROID_SHEET = window.sprites["asteroids"]

# "magic numbers" obtained via a script in assets/make_spritesheets.py, end of the printout
# Updated to include recycle sprite collision radii (positions 104-119)
ASTEROID_RADII = [22, 26, 18, 19, 21, 25, 18, 23, 26, 20, 24, 13, 22, 18, 21, 23, 30, 19, 18, 18, 18, 21, 26, 
                  20, 21, 16, 24, 22, 18, 25, 18, 20, 19, 21, 22, 18, 24, 20, 23, 20, 22, 20, 24, 17, 16, 16, 
                  18, 21, 17, 22, 24, 25, 14, 24, 25, 14, 22, 23, 21, 18, 20, 18, 18, 19, 24, 23, 23, 27, 19, 
                  24, 25, 20, 23, 21, 25, 22, 19, 25, 21, 16, 30, 26, 24, 30, 23, 21, 20, 18, 25, 16, 24, 21, 
                  23, 18, 21, 24, 20, 23, 29, 20, 24, 22, 22, 19, 21, 37, 31, 43, 31, 32, 23, 24, 22, 20, 24, 21, 25, 33, 23, 21] # noqa


class Asteroid(SceneObject):
    def __init__(
        self, sheet: SpriteSheet, 
        x: float, y: float, 
        vx: float, vy: float, 
        target_size_px: float, 
        sprite_index: int, 
        grid_cols: int = 11, 
        cell_size: float = 0, 
        grow_rate=6.0, 
        health: int = 450,
        damage_mul: float= 1.0
    ):
        super().__init__()
        super().set_position(x, y)
        self.sheet = sheet
        self.velocity_x = vx
        self.velocity_y = vy
        self.rotation = 0.0
        self.rotation_speed = random.uniform(-0.5, 0.5)
        self.target_size = target_size_px
        self.size = 5.0
        self.grow_rate = target_size_px / random.uniform(grow_rate - 1.8, grow_rate + 2.5)
        self.sprite_index = sprite_index
        self.grid_cols = grid_cols
        self.cell_size = cell_size
        self.hitbox_scale = 0.45
        self.hitbox_radius = ASTEROID_RADII[sprite_index]
        self._last_timestamp = None
        self.linger_time = 0.5
        self.full_size_reached_at = None
        self.health = random.uniform(health * 0.8, health * 1.2)
        self.damage_mul = random.uniform(damage_mul * 0.9, damage_mul * 1.1)

    def _ensure_cell_size(self):
        if not self.cell_size:
            if self.sheet.width:
                self.cell_size = max(1, int(self.sheet.width // self.grid_cols))

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
        ctx.drawImage(self.sheet.image, x, y, w, h, -size / 2, -size / 2, size, size)

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
        if self.health <= 0:
            window.debris.generate_debris(window.player.get_position(), self.get_position(), 4)
            window.debris.generate_debris(window.player.get_position(), self.get_position(), 3.75)
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
        self._max_asteroids = 50  # default max asteroids that can appear on the screen
        self.cell_size = 0
        self._use_grow_rate = 6.0 # default growth rate (how fast they appear to approach the player)
        self._use_health = 450 # default durability (affects asteroids being destroyed by impacts w/ player)
        self._use_damage_mul = 1.0

    def _spawn_one(self):
        # Don't spawn if at the limit
        if len(self.asteroids) >= self._max_asteroids:
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

        # Use recycle sprites (104-119) for Earth, regular asteroids (0-103) for other planets
        if hasattr(self, '_current_planet_name') and self._current_planet_name.lower() == 'earth':
            idx = random.randint(104, 119)  # Recycle sprites
            # Scale recycle items smaller since they're items, not large asteroids
            target = random.uniform(self.max_size * 0.25, self.max_size * 0.45)
            log.debug("Spawning recycle sprite %d for Earth with smaller target size %f", idx, target)
        else:
            idx = random.randint(0, 103)  # Regular asteroid sprites
            target = random.uniform(self.max_size * 0.7, self.max_size * 1.3)
            if hasattr(self, '_current_planet_name'):
                log.debug("Spawning asteroid sprite %d for %s", idx, self._current_planet_name)
            
        a = Asteroid(
            self.sheet, x, y, velocity_x, velocity_y, target, idx, 
            grow_rate=self._use_grow_rate,
            health=self._use_health,
            damage_mul=self._use_damage_mul
        )
        self.asteroids.append(a)

    # Spawn at interval and only if under limit
    def spawn_and_update(self, timestamp: float):
        # adjust spawnrate by a random factor so asteroids don't spawn at fixed intervals
        spawnrate = self.spawnrate * random.uniform(0.2, 1.0)
        
        # Increase spawn rate for smaller recycle items on Earth
        if hasattr(self, '_current_planet_name') and self._current_planet_name.lower() == 'earth':
            spawnrate *= 0.1  # 10x faster spawn rate for Earth recycle items (1/10 = 0.1)

        # slow down spawnrate for this attempt a bit if there already many asteroids active
        spawnrate = spawnrate * max(1, 1 + (len(self.asteroids) - 35) * 0.1)
        if self._last_spawn == 0.0 or (timestamp - self._last_spawn) >= spawnrate:
            if len(self.asteroids) < self._max_asteroids:
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

    def reset(self, planet_data: PlanetData):
        """ reset the asteroid management system with the given difficulty parameters """

        # Store the planet name for sprite selection
        self._current_planet_name = planet_data.name

        # the asteroid difficulty settings are on a 1-20 scale of ints
        asteroid_settings = planet_data.asteroid

        spawnrate = 500
        # clamp max between 10-80, default is 50 at difficulty 10
        max_asteroids = min(max(10, 5 * asteroid_settings.count), 80)

        # this determines how quickly asteroids seem to be approaching player (sprite growing in size)
        # NOTE: the relationship is inverse, smaller growth rate = faster approaching asteroids
        # a value of 6.0 feels like a pretty good rough default, not too slow
        use_grow_rate = max(1.2, 10.5 - (asteroid_settings.speed - 5) * 0.5)
        # how easily asteroids fall apart from collisions, default 450 health at level 10
        use_health = 50 + 40 * asteroid_settings.durability
        # range of 0.3 to 2.2 multiplier
        use_damage_mul = 0.2 + 0.1 * asteroid_settings.damage

        log.debug("Resetting asteroids with difficulty parameters for planet %s:", planet_data.name)
        log.debug("Max asteroids: %s (%s), default 50", max_asteroids, asteroid_settings.count)
        log.debug("Grow rate(approach speed): %s (%s), default 6.0", use_grow_rate, asteroid_settings.speed)
        log.debug("Asteroid durability: %s (%s), default 450", use_health, asteroid_settings.durability)
        log.debug("Damage multiplier: %s (%s), default 1.0", use_damage_mul, asteroid_settings.damage)
        
        # Special difficulty adjustments for Earth recycle items
        if planet_data.name.lower() == 'earth':
            max_asteroids = min(max_asteroids * 2, 120)  # Allow up to 2x more recycle items
            use_grow_rate *= 0.6  # Make them approach 40% faster
            use_health *= 1.5  # Make them 50% more durable
            use_damage_mul *= 1.3  # Increase damage by 30%
        
        self._max_asteroids = max_asteroids
        self._use_grow_rate = use_grow_rate
        self._use_health = use_health
        self._use_damage_mul = use_damage_mul

        self.asteroids.clear()
        self._last_spawn = 0.0
        self.cell_size = 0
