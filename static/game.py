from js import document, window  # type: ignore[attr-defined]
from pyodide.ffi import create_proxy  # type: ignore[attr-defined]

from consolelogger import getLogger
from controls import GameControls
from player import Player
from solar_system import SolarSystem
from scene_classes import SceneManager, Scene
from scene_descriptions import create_scene_manager
from stars import StarSystem

log = getLogger(__name__)

# References to the useful html elements
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight
canvas = window.canvas = document.getElementById("gameCanvas")
ctx = window.ctx = window.canvas.getContext("2d")


# TODO: the resizing and margins needs work, I suck with CSS / html layout
def resize_canvas(event=None) -> None:
    width, height = container.clientWidth, container.clientHeight
    canvas.width = width
    canvas.height = height
    canvas.style.width = f"{width}px"
    canvas.style.height = f"{height}px"

resize_proxy = create_proxy(resize_canvas)
window.addEventListener("resize", resize_proxy)
resize_canvas()

"""
I'm not entirely clear on what this create_proxy is doing, but when passing python functions as callbacks to
"javascript" (well pyscript wrappers for javascript functionality) we need to wrap them in these proxy objects
instead of passing them as straight up python function references.
"""

# setup of important systems, expose them globally via window object
controls = window.controls = GameControls(canvas)
scene_manager = window.scene_manager = create_scene_manager()
sprites = window.sprites
player = window.player = Player(sprites["player"], canvas.width / 2, canvas.height / 2, scale=0.1)

log.info("Sprite URLs: %s", sprites)
log.info("Created player at position (%s, %s)", player.x, player.y)

def game_loop(timestamp: float) -> None:
    """
    timestamp argument will be time since the html document began to load, in miliseconds.
    """

    # if controls.pressed:
    #     log.debug("Keys pressed: %s", controls.pressed)
    # log.debug(controls.mouse.move)

    # Not doing anything with this at the moment, but this returns the planet clicked, if any
    """ TODO
    if controls.click:
        log.debug("Mouse click at: %s", controls.mouse.click)
        planet = solar_sys.get_object_at_position(controls.mouse.click)
        if planet:
            log.debug("Clicked on: %s", planet.name)
    """

    """ --- Do anything that needs to be drawn in this frame here --- """
    active_scene: Scene = scene_manager.get_active_scene()
    active_scene.render(ctx, timestamp)

    
    """ TODO
    if player:
        player.render(ctx, timestamp)
    else:
        # Draw a debug indicator if no player
        ctx.fillStyle = "yellow"
        ctx.beginPath()
        ctx.arc(canvas.width / 2, canvas.height / 2, 15, 0, 6.283)
        ctx.fill()
    """

    """ --- That was everything that needed to be drawn in that frame --- """

    # if a click event occurred and nothing made use of it during this loop, clear the click flag
    controls.click = False
    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)


# Start loop
game_loop_proxy = create_proxy(game_loop)
window.requestAnimationFrame(game_loop_proxy)
