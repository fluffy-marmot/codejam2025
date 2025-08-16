from consolelogger import getLogger
from controls import GameControls
from asteroid import AsteroidAttack
from debris import DebrisSystem
from player import Player, Scanner
from js import document, window  # type: ignore[attr-defined]
from pyodide.ffi import create_proxy  # type: ignore[attr-defined]
from sprites import SpriteSheet
from scene_classes import Scene
from scene_descriptions import create_scene_manager

log = getLogger(__name__)

# References to the useful html elements
loadingLabel = document.getElementById("loadingLabel")
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight
canvas = window.canvas
ctx = window.ctx = window.canvas.getContext("2d")

window.DEBUG_DRAW_HITBOXES = False


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
player = window.player = Player(
    SpriteSheet("player"), SpriteSheet("health"), canvas.width / 2, canvas.height / 2, scale=0.1
)
window.asteroids = AsteroidAttack(sprites["asteroids"], width, height, 256)
window.debris = DebrisSystem()


scanner = window.scanner = Scanner(SpriteSheet("scanner"), player)
log.info("Sprite URLs: %s", sprites)
log.info("Created player at position (%s, %s)", player.x, player.y)

loadingLabel.style.display = "none"

def game_loop(timestamp: float) -> None:
    """
    timestamp argument will be time since the html document began to load, in miliseconds.
    """

    """ --- Do anything that needs to be drawn in this frame here --- """

    # these should disable bilinear filtering smoothing, which isn't friendly to pixelated graphics
    ctx.imageSmoothingEnabled = False
    ctx.webkitImageSmoothingEnabled = False
    ctx.mozImageSmoothingEnabled = False
    ctx.msImageSmoothingEnabled = False

    active_scene: Scene = scene_manager.get_active_scene()
    active_scene.render(ctx, timestamp)

    # please keep any scene-specific rendering inside the render method of each scene
    # code to render asteroids and player was moved to render method of class PlanetScene

    """ --- That was everything that needed to be drawn in that frame --- """

    # if a click event occurred and nothing made use of it during this loop, clear the click flag
    controls.click = False
    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)


# Start loop
game_loop_proxy = create_proxy(game_loop)
window.requestAnimationFrame(game_loop_proxy)
