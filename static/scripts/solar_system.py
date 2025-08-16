import math

from common import Position, PlanetState
from sprites import SpriteSheet
from scene_classes import SceneObject

from spacemass import SpaceMass

GRAVI_CONST = 0.67

from consolelogger import getLogger

log = getLogger(__name__)


class SolarSystem(SceneObject):
    def __init__(self, screen_size=[512, 512], *, planet_scene_state: PlanetState):
        super().__init__()

        # Sun position (center of screen)
        self.sun_pos: Position = Position(screen_size[0] // 2, screen_size[1] // 2)

        # Sun
        self.sun = SpaceMass(SpriteSheet("sun"), PlanetState(1000.0, 120.0, 0.0), planet_scene_state)
        self.sun.set_position(self.sun_pos)

        # Inner planets
        self.mercury = SpaceMass(SpriteSheet("mercury"), PlanetState(3.3, 10, 2.5), planet_scene_state)
        self.venus = SpaceMass(SpriteSheet("venus"), PlanetState(48.7, 14, 2.0), planet_scene_state)
        self.earth = SpaceMass(SpriteSheet("earth"), PlanetState(59.7, 16, 1.8), planet_scene_state)
        self.mars = SpaceMass(SpriteSheet("mars"), PlanetState(6.4, 12, 1.5), planet_scene_state)

        # Outer planets
        self.jupiter = SpaceMass(SpriteSheet("jupiter"), PlanetState(1898.0, 64.0, 1.0), planet_scene_state)
        self.saturn = SpaceMass(SpriteSheet("saturn"), PlanetState(568.0, 46.0, 0.8), planet_scene_state)
        self.uranus = SpaceMass(SpriteSheet("uranus"), PlanetState(86.8, 36.0, 0.6), planet_scene_state)
        self.neptune = SpaceMass(SpriteSheet("neptune"), PlanetState(102.0, 15.0, 0.4), planet_scene_state)

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
        self.planet_angles: list[float] = [20, 220, 100, 45, 0, 155, 270, 15]

        # Initialize planet positions
        for i, planet in enumerate(self.planets):
            angle_rad = math.radians(self.planet_angles[i])
            x = self.sun_pos.x + self.planet_distances[i] * math.cos(angle_rad)
            y = self.sun_pos.y + self.planet_distances[i] * math.sin(angle_rad)
            planet.set_position(Position(x, y))

    def update(self):
        self.update_orbits(0.20)

    def get_planet(self, planet_name: str) -> SpaceMass:
        for planet in self.planets:
            if planet.name == planet_name:
                return planet

    def update_orbits(self, dt: float):
        """Update planet positions using simple circular orbits"""
        for i, planet in enumerate(self.planets):
            angular_velocity = planet.state.initial_velocity * 0.01

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

    def render(self, ctx, timestamp):
        """Render the entire solar system"""
        # Render sun at center
        self.sun.render(ctx, timestamp)

        # Render all planets
        highlighted_planet = None
        for planet in self.planets:
            if planet.highlighted:
                highlighted_planet = planet
                continue
            planet.render(ctx, timestamp)

        # If a planet is highlighted, draw it last, so its text label is in front of other planets
        if highlighted_planet:
            highlighted_planet.render(ctx, timestamp)

        super().render(ctx, timestamp)

    # I Couldn't get this to work 〒__〒
    def calculateGForce(self, planet_index: int) -> float:
        """Calculate gravitational force between the sun and a planet"""
        # Get planet position
        planet_pos = self.planets[planet_index].get_position()
        planet = self.planets[planet_index]

        # Calculate distance between sun and planet
        distance = planet_pos.distance(self.sun_pos)

        # Prevent division by zero
        if distance == 0:
            return 0

        # F = G * m1 * m2 / r^2
        force = GRAVI_CONST * self.sun.state.mass * planet.state.mass / (distance * distance)

        return force

    def get_object_at_position(self, pos: Position) -> SpaceMass | None:
        """Get the space object at the specified position, excluding the sun.

        Arguments:
            pos (Position): The position to check.

        Returns:
            The space object at the position if found, otherwise None.
        """
        closest_planet = None
        closest_distance = float("inf")
        for planet in self.planets:
            rect = planet.get_bounding_box()
            if rect.left <= pos.x <= rect.right and rect.top <= pos.y <= rect.bottom:
                # Calculate distance from click point to planet center
                planet_center = Position(rect.left + rect.width / 2, rect.top + rect.height / 2)
                distance = planet_center.distance(pos)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_planet = planet
        return closest_planet
