from js import document, window  # type: ignore[attr-defined]

from consolelogger import getLogger
from scene_classes import Scene, SceneObject, SceneManager

from player import Player
from spacemass import SpaceMass
from solar_system import SolarSystem
from stars import StarSystem
from sprites import SpriteSheet

log = getLogger(__name__)
sprites = window.sprites

# --------------------
# methods that may be useful across various scenes
# --------------------


def get_controls():
    return window.controls


def get_player():
    return window.player


def draw_black_background(ctx):
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, window.canvas.width, window.canvas.height)


# --------------------
# our main scene with the planets orbiting the sun
# --------------------

ORBITING_PLANETS_SCENE = "orbiting-planets-scene"


class OrbitingPlanetsScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager)

        self.solar_sys = SolarSystem([window.canvas.width, window.canvas.height])

        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=3,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.highlight_hovered_planet()

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

        # from this scene, be ready to switch to a big planet scene if planet is clicked
        self.switch_planet_scene()

    def highlight_hovered_planet(self):
        # Reset all planets' highlight state first
        for planet in self.solar_sys.planets:
            planet.highlighted = False

        planet = self.solar_sys.get_object_at_position(get_controls().mouse.move)
        if planet is not None:
            log.debug("Highlighting planet: %s", planet.name)
            planet.highlighted = True

    def switch_planet_scene(self):
        """Switch to the clicked planet scene if a planet is clicked."""
        if get_controls().click:
            planet = self.solar_sys.get_object_at_position(get_controls().mouse.click)
            if planet:
                log.debug("Clicked on: %s", planet.name)
                self.scene_manager.activate_scene(f"{planet.name}-planet-scene")


# --------------------
# game scene with zoomed in planet on left
# --------------------


class PlanetScene(Scene):
    def __init__(
        self,
        name: str,
        scene_manager: SceneManager,
        planet: SpaceMass,
    ):
        super().__init__(name, scene_manager)

        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=3,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )
        self.planet = planet
        planet.set_position(0, window.canvas.height // 2)

    def render(self, ctx, timestamp):
        draw_black_background(ctx)

        self.stars.star_shift(timestamp, 5)
        self.stars.render(ctx, timestamp)
        self.planet.render(ctx, timestamp)

        # TODO: temporary debug\demo functionality: click goes back to the OrbitingPlanets scene
        if get_controls().click:
            self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)


# --------------------
# create scene manager
# --------------------


def create_scene_manager() -> SceneManager:
    """
    Create all the scenes and add them to a scene manager that can be used to switch between them
    """
    manager = SceneManager()

    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager)
    manager.add_scene(orbiting_planets_scene)

    for planet in "mercury venus earth mars jupiter saturn neptune uranus".split():
        spacemass = SpaceMass(SpriteSheet(planet), 0, window.canvas.height, 1.0)
        big_planet_scene = PlanetScene(f"{planet}-planet-scene", manager, spacemass)
        manager.add_scene(big_planet_scene)

    manager.activate_scene(ORBITING_PLANETS_SCENE)  # initial scene
    return manager
