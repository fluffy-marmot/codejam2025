"""
Scene manager creation and setup.
"""

from scene_classes import SceneManager
from common import PlanetState
from solar_system import SolarSystem
from window import window
from .orbiting_planets_scene import OrbitingPlanetsScene
from .planet_scene import PlanetScene
from .start_scene import StartScene
from .final_scene import FinalScene
from .constants import ORBITING_PLANETS_SCENE, START_SCENE, FINAL_SCENE


def create_scene_manager() -> SceneManager:
    """
    Create all the scenes and add them to a scene manager that can be used to switch between them The object
    instance returned by this is used by the main game loop in game.py to check which scene is active when a
    frame is drawn and that scene's render method is called. Only one scene listed in the scene manager is
    active at a time, though scenes may have their own subscenes, such as textboxes that they render as part of
    their routine.
    """
    manager = SceneManager()
    planet_scene_state = PlanetState(0, window.canvas.height, 120.0, x=0, y=window.canvas.height // 2)
    solar_system = SolarSystem([window.canvas.width, window.canvas.height], planet_scene_state=planet_scene_state)
    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager, solar_system)
    start_scene = StartScene(START_SCENE, manager)
    manager.add_scene(start_scene)
    manager.add_scene(orbiting_planets_scene)
    # Final victory scene (activated when all planets complete)
    final_scene = FinalScene(FINAL_SCENE, manager)
    manager.add_scene(final_scene)

    for planet in solar_system.planets:
        big_planet_scene = PlanetScene(f"{planet.name}-planet-scene", manager, planet)
        manager.add_scene(big_planet_scene)

    manager.activate_scene(START_SCENE)  # initial scene
    return manager
