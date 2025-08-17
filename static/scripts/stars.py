import math
import random

from scene_classes import SceneObject
from window import window
from js import document #type: ignore
loadingLabel = document.getElementById("loadingLabel")
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight


class Star:
    def __init__(self, radius, x, y, pulse_freq, shade=0, fade_in=True) -> None:
        self.radius = radius
        self.frame_delay = 135
        self.pulse_freq = pulse_freq  # renaming of animation timer
        self.x = x
        self.y = y
        self.shade = shade  # defines r,g, and b
        self.alpha = 1
        self.color = "rgba(255, 255, 255, 1)"
        self.fade_in = fade_in
        self.animation_timer = 0
        self.glisten = False

    def render(self, ctx, timestamp, num_stars) -> None:
        # pulse
        if timestamp - self.animation_timer >= self.pulse_freq:
            self.animation_timer = timestamp
            if self.fade_in:
                self.shade += 1
            else:
                self.shade -= 1

            if self.shade > 255 or self.shade < 1:
                self.fade_in = not self.fade_in

            self.color = self.rgba_to_str(self.shade, self.shade, self.shade, self.alpha)

        # draw star
        ctx.fillStyle = self.color
        ctx.beginPath()
        ctx.ellipse(self.x, self.y, self.radius, self.radius, 0, 0, 2 * math.pi)
        ctx.fill()

        chance_glisten = random.randint(1, num_stars * 4)
        if chance_glisten == num_stars:
            self.glisten = True
        # glisten
        if self.shade > 240 and self.glisten:
            glisten_line_col = self.rgba_to_str(self.shade, self.shade, self.shade, 1)

            ctx.strokeStyle = glisten_line_col  # or any visible color
            ctx.lineWidth = 2  # thick enough to see
            ctx.beginPath()
            ctx.moveTo(self.x, self.y - self.radius - 5)  # start drawing curve a bit lower than star pos
            ctx.bezierCurveTo(
                self.x - self.radius,
                self.y - self.radius,
                self.x + self.radius,
                self.y + self.radius,
                self.x,
                self.y + self.radius + 5,
            )
            ctx.stroke()
        else:
            self.glisten = False

    def rgba_to_str(self, r: int, g: int, b: int, a: int) -> str:
        return f"rgba({r}, {g}, {b}, {a})"


class StarSystem(SceneObject):
    def __init__(self, num_stars, radius_min, radius_max, pulse_freq_min, pulse_freq_max, num_frames=50):
        super().__init__()

        self.num_frames = num_frames
        self.radius_min = radius_min
        self.radius_max = radius_max
        self.pulse_freq_min = pulse_freq_min
        self.pulse_freq_max = pulse_freq_max
        self.frame_delay = 135
        self.num_stars = num_stars
        self.animation_timer = 0
        self.stars: list[Star] = []  # will be filled with star object instances

        for _ in range(num_stars):
            self.stars.append(self.create_star("random", "random"))

    def render(self, ctx, timestamp) -> None:
        """Render every star."""
        for star in self.stars:
            star.render(ctx, timestamp, self.num_stars)

        if len(self.stars) == 0:
            raise ValueError("There are no stars! Did you populate?")

        super().render(ctx, timestamp)

    def create_star(self, x="random", y="random"):
        if x == "random":
            x = random.randint(0, window.canvas.width)
        if y == "random":
            y = random.randint(0, window.canvas.height)

        pulse_freq = random.randint(self.pulse_freq_min, self.pulse_freq_max)
        radius = random.randint(self.radius_min, self.radius_max)
        shade = random.randint(0, 255)
        fade_in = random.choice([True, False])
        return Star(radius, x, y, pulse_freq, shade=shade, fade_in=fade_in)

    def star_shift(self, current_time, shift_time):
        if current_time - self.animation_timer >= shift_time:
            self.animation_timer = current_time
            replacement_stars = []
            for index, star in enumerate(self.stars):
                star.x += 1
                if abs(star.x) > window.canvas.width or abs(star.y) > window.canvas.height:
                    self.stars.pop(index)
                    replacement_star = self.create_star(0, "random")
                    replacement_stars.append(replacement_star)

            for star in replacement_stars:
                self.stars.append(star)

    def star_scale(self, current_time, shift_time):
        if current_time - self.animation_timer >= shift_time:
            self.animation_timer = current_time

class Star3d(Star):
    def __init__(self, radius, x, y, z, pulse_freq, shade=0, fade_in=True):
        super().__init__(radius, x, y, pulse_freq, shade, fade_in)
        self.z = z

    def update(self, speed, max_depth):
        """Move the star closer by reducing z."""
        self.z -= speed
        if self.z <= 0:  # if it passes the camera, recycle
            self.z = max_depth
            self.x = random.uniform(-1, 1)
            self.y = random.uniform(-1, 1)

    def project(self, cx, cy, max_radius, scale):
        """Project 3D coords to 2D screen coords."""
        screen_x = cx + (self.x / self.z) * scale
        screen_y = cy + (self.y / self.z) * scale
        size = max(1, (1 / self.z) * scale * 0.5)  # star grows as z decreases
        if size > max_radius:
            size = max_radius

        return screen_x, screen_y, size


class StarSystem3d:
    def __init__(self, num_stars, max_depth=5, max_radius = 20):
        self.num_stars = num_stars
        self.max_depth = max_depth
        self.max_radius = max_radius
        self.stars: list[Star3d] = []
        for _ in range(num_stars):
            self.stars.append(self.create_star())

    def create_star(self):
        x = random.randint(-width//2, width//2)
        y = random.randint(-height//2, height//2)
        z = random.uniform(20, self.max_depth)
        pulse_freq = random.randint(30, 80)   # tweak as desired
        radius = 1
        shade = random.randint(150, 255)
        fade_in = True
        return Star3d(radius, x, y, z, pulse_freq, shade=shade, fade_in=fade_in)

    def render(self, ctx, speed=0.4, scale=300):
        cx = window.canvas.width / 2
        cy = window.canvas.height / 2

        for index, star in enumerate(self.stars):
            star.update(speed, self.max_depth)
            sx, sy, size = star.project(cx, cy, self.max_radius, scale)

            # If star leaves screen, recycle it
            if sx < 0 or sx > window.canvas.width or sy < 0 or sy > window.canvas.height:
                self.stars.pop(index)
                self.stars.append(self.create_star())

            # Draw star (brightens as it approaches)
            shade = int(255 * (1 - star.z / self.max_depth))
            ctx.fillStyle = f"rgba({shade}, {shade}, {shade}, 1)"
            ctx.beginPath()
            ctx.ellipse(sx, sy, size, size, 0, 0, 2 * math.pi)
            ctx.fill()

