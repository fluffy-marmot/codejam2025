import math

from js import window  # type: ignore
from spacemass import Position, SpaceMass

GRAVI_CONST = 0.67
planets = {planet["name"].lower(): planet for planet in window.planets}

from consolelogger import getLogger

log = getLogger(__name__)


class SolarSystem:
    def __init__(self, screen_size=[512, 512]):
        # Sun position (center of screen)
        self.sun_pos: Position = Position(screen_size[0] // 2, screen_size[1] // 2)

        # Sun
        self.sun = SpaceMass("sun", planets["sun"]["spritesheet"], 1000.0, 120.0, 0.0)
        self.sun.set_position(self.sun_pos)

        # Inner planets
        self.mercury = SpaceMass("mercury", planets["mercury"]["spritesheet"], 3.3, 10, 2.5)
        self.venus = SpaceMass("venus", planets["venus"]["spritesheet"], 48.7, 14, 2.0)
        self.earth = SpaceMass("earth", planets["earth"]["spritesheet"], 59.7, 16, 1.8)
        self.mars = SpaceMass("mars", planets["mars"]["spritesheet"], 6.4, 12, 1.5)

        # Outer planets
        self.jupiter = SpaceMass("jupiter", planets["jupiter"]["spritesheet"], 1898.0, 64.0, 1.0)
        self.saturn = SpaceMass("saturn", planets["saturn"]["spritesheet"], 568.0, 46.0, 0.8)
        self.uranus = SpaceMass("uranus", planets["uranus"]["spritesheet"], 86.8, 36.0, 0.6)
        self.neptune = SpaceMass("neptune", planets["neptune"]["spritesheet"], 102.0, 15.0, 0.4)

        self.planets = [
            self.mercury,
            self.venus,
            self.earth,
            self.mars,
            self.jupiter,
            self.saturn,
            self.uranus,
            self.neptune,
        ]

        # Initial positions (distance from sun in pixels)
        self.planet_distances = [110, 140, 160, 200, 270, 350, 420, 470]
        self.planet_angles: list[float] = [0, 45, 90, 135, 180, 225, 270, 315]

        # Initialize planet positions
        for i, planet in enumerate(self.planets):
            angle_rad = math.radians(self.planet_angles[i])
            x = self.sun_pos.x + self.planet_distances[i] * math.cos(angle_rad)
            y = self.sun_pos.y + self.planet_distances[i] * math.sin(angle_rad)
            self.planets[i].set_position(Position(x, y))

    def update(self):
        self.update_orbits(0.20)

    def update_orbits(self, dt: float):
        """Update planet positions using simple circular orbits"""
        for i, planet in enumerate(self.planets):
            angular_velocity = planet.initial_velocity * 0.01

            # Update angle
            self.planet_angles[i] += angular_velocity * dt * 60  # Scale for 60 FPS

            # Keep angle in range [0, 360)
            self.planet_angles[i] = self.planet_angles[i] % 360

            # Calculate new position using circular motion
            angle_rad = math.radians(self.planet_angles[i])
            x = self.sun_pos.x + self.planet_distances[i] * math.cos(angle_rad)
            y = self.sun_pos.y + self.planet_distances[i] * math.sin(angle_rad)

            # Update position
            self.planets[i].set_position(Position(x, y))

    def render(self, context, timestamp):
        """Render the entire solar system"""
        # Render sun at center
        self.sun.render(context, timestamp)

        # Render all planets
        for i, planet in enumerate(self.planets):
            planet.render(context, timestamp)

    def get_distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate the distance between two positions."""
        dx = pos2.x - pos1.x
        dy = pos2.y - pos1.y
        return math.sqrt(dx * dx + dy * dy)

    # I Couldn't get this to work 〒__〒
    def calculateGForce(self, planet_index: int):
        """Calculate gravitational force between the sun and a planet"""
        # Get planet position
        planet_pos = self.planets[planet_index].get_position()
        planet = self.planets[planet_index]

        # Calculate distance between sun and planet
        distance = self.get_distance(self.sun_pos, planet_pos)

        # Prevent division by zero
        if distance == 0:
            return 0

        # F = G * m1 * m2 / r^2
        force = GRAVI_CONST * self.sun.mass * planet.mass / (distance * distance)

        return force

    def get_clicked_object(self, click_pos: Position) -> SpaceMass | None:
        closest_planet = None
        closest_distance = float("inf")
        for i, planet in enumerate(self.planets):
            rect = planet.get_bounding_box()
            if rect.left <= click_pos.x <= rect.right and rect.top <= click_pos.y <= rect.bottom:
                # Calculate distance from click point to planet center
                planet_center = Position(rect.left + rect.width / 2, rect.top + rect.height / 2)
                distance = self.get_distance(click_pos, planet_center)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_planet = planet
        return closest_planet
