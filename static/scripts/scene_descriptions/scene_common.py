"""
Common utilities and constants shared across all scenes.
"""

from window import window
from scene_classes import Scene, SceneManager  
from overlay import TextOverlay, Dialogue, Credits, ResultsScreen, DeathScreen
from player import PlayerExplosion
from spacemass import SpaceMass
from consolelogger import getLogger
from common import Position
from stars import StarSystem3d
from .constants import ORBITING_PLANETS_SCENE, FINAL_SCENE, START_SCENE

log = getLogger(__name__, False)

# Scene constants are imported from constants.py to keep a single source of truth

# Common utility functions
def get_controls():
    return window.controls

def get_player():
    return window.player

def get_asteroid_system():
    return window.asteroids

def get_debris_system():
    return window.debris

def get_scanner():
    return window.scanner

def draw_black_background(ctx):
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, window.canvas.width, window.canvas.height)
