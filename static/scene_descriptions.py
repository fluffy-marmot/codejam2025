from js import document, window  # type: ignore[attr-defined]

from scene_classes import Scene, SceneObject, SceneManager

from player import Player
from spacemass import SpaceMass
from solar_system import SolarSystem
from stars import StarSystem

# --------------------
# methods that may be useful across various scenes
# --------------------

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
        self.stars.populate(window.canvas.width, window.canvas.height)

    def render(self, ctx, timestamp):
        draw_black_background(ctx)

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

# --------------------
# create scene manager
# --------------------

def create_scene_manager() -> SceneManager:
    manager = SceneManager()

    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager)
    manager.add_scene(orbiting_planets_scene)
    manager.activate_scene(ORBITING_PLANETS_SCENE)

    return manager