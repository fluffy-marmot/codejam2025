import math
import random

from js import document  # type: ignore[attr-defined]

from scene_classes import SceneObject

canvas = document.getElementById("gameCanvas")
ctx = canvas.getContext("2d")


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
        self.stars: list[Star] = []  # will be filled with star classes

    def populate(self, width, height) -> None:
        """Create a list of many Stars."""
        for _ in range(self.num_stars):
            x = random.randint(0, width)
            y = random.randint(0, height)
            pulse_freq = random.randint(self.pulse_freq_min, self.pulse_freq_max)
            radius = random.randint(self.radius_min, self.radius_max)
            shade = random.randint(0, 255)
            fade_in = random.choice([True, False])
            star = Star(radius, x, y, pulse_freq, shade=shade, fade_in=fade_in)
            self.stars.append(star)

    def render(self, ctx, timestamp) -> None:
        """Render every star."""
        for star in self.stars:
            star.render(ctx, timestamp, self.num_stars)

        if len(self.stars) == 0:
            raise ValueError("There are no stars! Did you populate?")

        super().render(ctx, timestamp)