"""
using # type: ignore since these imports are only available in the pyodide environment and pylance
will complain about them otherwise
"""
from js import document, window  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore

from consolelogger import getLogger
from controls import GameControls
from solar_system import SolarSystem
from player import Player
from stars import StarSystem
import time
from gameplay import jupiter
from astriod import AsteriodAttack
log = getLogger(__name__)

""" references to the useful html elements """
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight
canvas = document.getElementById("gameCanvas")
ctx = canvas.getContext("2d")

# TODO: the resizing and margins needs work, I suck with CSS / html layout
def resize_canvas(event=None):
    width, height = container.clientWidth, container.clientHeight
    canvas.width = width
    canvas.height = height
    canvas.style.width = f"{width}px"
    canvas.style.height = f"{height}px"

"""
I'm not entirely clear on what this create_proxy is doing, but when passing python functions as callbacks to
"javascript" (well pyscript wrappers for javascript functionality) we need to wrap them in these proxy objects
instead of passing them as straight up python function references.
"""

resize_proxy = create_proxy(resize_canvas)
window.addEventListener("resize", resize_proxy)
resize_canvas()

"""
controls object gives access to what keys are being currently pressed, accessible properties:
-   controls.pressed is a set of strings representing keys and mouse buttons currently held down
    the strings for mouse buttons are given by GameControls.MOUSE_LEFT, etc.
-   controls.mouse gives access to all the coordinates of the last registered mouse event of each kind as the
    tuples controls.mouse.mousedown, controls.mouse.mouseup, controls.mouse.click, controls.mouse.move
-   use controls.mouse.move for best current coordinates of the mouse
-   additionally, controls.click is a boolean representing if a click just occurred. It is set to False at the
    end of each game loop if nothing makes use of the click event
-   use enable_logging=False if spam of mouse/key events in browser console gets annoying
"""
controls = GameControls(canvas, enable_logging=True)
sprites = window.sprites

log.info("Sprite URLs: %s", sprites)

solar_sys = SolarSystem([canvas.width, canvas.height])

# Player setup. index.html will assign window.player_sprite (an Image) before importing game.
player_sprite = getattr(window, "player_sprite", None)
log.info("Player sprite object: %s", player_sprite)
if player_sprite is not None:
    log.info("Player sprite src: %s", getattr(player_sprite, 'src', 'no src'))
    player = Player(player_sprite, canvas.width / 2, canvas.height / 2, scale=0.1)
    window.player = player  # expose instance globally
    log.info("Created player at position (%s, %s)", player.x, player.y)
else:
    log.error("No player_sprite found on window object!")
    player = None
    
#as number of stars increase, the radius should decrease
num_stars = 100
stars = StarSystem(
    num_stars=num_stars,
    radius_min=1,
    radius_max=3,
    pulse_freq_min=3,
    pulse_freq_max=6,
)
stars.populate()
# Game state
t0 = time.time()
rotational_speed = 135
jupiter.animation_timer = rotational_speed
my_attack = AsteriodAttack(2000)
def game_loop(timestamp):
    """
    Game loop that will run roughly 60 / sec, though the timing may be dependant on monitor refresh rates?
    When called, timestamp argument will be time since the html document began to load, measured in miliseconds.
    We can use ctx, a wrapper for an html canvas's context to draw things to the canvas, with e.g. methods like
    fillRect.
    """
    width, height = canvas.width, canvas.height
    ctx.imageSmoothingEnabled = False
    ctx.webkitImageSmoothingEnabled = False
    ctx.mozImageSmoothingEnabled = False
    ctx.msImageSmoothingEnabled = False
    # if controls.pressed:
    #     log.debug("Keys pressed: %s", controls.pressed)
    # log.debug(controls.mouse.move)

    """ --- Do anything that needs to be drawn in this frame here --- """
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, width, height)

    stars.render(ctx, timestamp)  
    stars.star_shift(timestamp, 5)
    # solar_sys.update_orbits(0.20)
    # solar_sys.render(ctx, timestamp)
    jupiter.render(ctx, timestamp)
    x, y = player.get_position()
    my_attack.generate_astriods(timestamp, 50, x, y, 50)
    my_attack.render(ctx, timestamp)
    # update + render player
    global last_time
    if not hasattr(game_loop, "_last_real_time"):
        game_loop._last_real_time = time.time()
    now_real = time.time()
    dt = now_real - game_loop._last_real_time
    game_loop._last_real_time = now_real
    if player:
        player.update(dt, controls)
        player.render(ctx)
    else:
        # Draw a debug indicator if no player
        ctx.fillStyle = "yellow"
        ctx.beginPath()
        ctx.arc(canvas.width / 2, canvas.height / 2, 15, 0, 6.283)
        ctx.fill()

    """ --- That was everything that needed to be drawn in that frame --- """

    # if a click event occurred and nothing made use of it during this loop, clear the click flag
    controls.click = False
    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

game_loop_proxy = create_proxy(game_loop)

# Start loop
window.requestAnimationFrame(game_loop_proxy)