from asteroid import AsteroidAttack
from consolelogger import getLogger
from controls import GameControls
from debris import DebrisSystem
from js import document  # type: ignore[attr-defined]
from player import Player, Scanner
from pyodide.ffi import create_proxy  # type: ignore[attr-defined]
from scene_classes import Scene
from scene_descriptions import create_scene_manager
from window import window

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
player = window.player = Player(
    window.get_sprite("player"), window.get_sprite("health"), canvas.width / 2, canvas.height / 2, scale=0.1
)
window.asteroids = AsteroidAttack(window.get_sprite("asteroids"), width, height, 256)
window.debris = DebrisSystem()

scanner = window.scanner = Scanner(window.get_sprite("scanner"), player, min_x=width * 0.45, scan_mult=1)
log.info("Created player at position (%s, %s)", player.x, player.y)

loadingLabel.style.display = "none"


def game_loop(timestamp: float) -> None:
    """Timestamp argument will be time since the html document began to load, in miliseconds."""

    # these should disable bilinear filtering smoothing, which isn't friendly to pixelated graphics
    ctx.imageSmoothingEnabled = False
    ctx.webkitImageSmoothingEnabled = False
    ctx.mozImageSmoothingEnabled = False
    ctx.msImageSmoothingEnabled = False

    active_scene: Scene = scene_manager.get_active_scene()
    active_scene.render(ctx, timestamp)

    # if a click event occurred and nothing made use of it during this loop, clear the click flag
    controls.click = False
    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

# Start loop
game_loop_proxy = create_proxy(game_loop)
window.requestAnimationFrame(game_loop_proxy)