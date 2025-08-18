# scene_descriptions package for backwards compatibility  
# Import all the classes and functions from individual modules
from scene_descriptions.orbiting_planets_scene import OrbitingPlanetsScene
from scene_descriptions.planet_scene import PlanetScene
from scene_descriptions.start_scene import StartScene
from scene_descriptions.final_scene import FinalScene
from scene_descriptions.scene_manager import create_scene_manager
from scene_descriptions.constants import ORBITING_PLANETS_SCENE, START_SCENE, FINAL_SCENE
from scene_descriptions.scene_common import (
    get_controls, get_player, get_asteroid_system, 
    get_debris_system, get_scanner, draw_black_background,
    ResultsScreen, DeathScreen
)
