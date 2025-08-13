"""
using # type: ignore since these imports are only available in the pyodide environment and pylance
will complain about them otherwise
"""
from js import document, window  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore

from consolelogger import getLogger
from controls import GameControls
from solar_system import SolarSystem
from stars import StarSystem
import time

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
controls = GameControls(canvas)
sprites = window.sprites

log.info("Sprite URLs: %s", sprites)

solar_sys = SolarSystem([canvas.width, canvas.height])
#as number of stars increase, the radius should decrease
num_stars = 100
stars = StarSystem(
    num_stars=num_stars,
    radius_min=1,
    radius_max=3,
    pulse_freq_min=3,
    pulse_freq_max=6,
)
stars.populate(width, height)
# Game state
t0 = time.time()

def game_loop(timestamp):
    """
    Game loop that will run roughly 60 / sec, though the timing may be dependant on monitor refresh rates?
    When called, timestamp argument will be time since the html document began to load, measured in miliseconds.
    We can use ctx, a wrapper for an html canvas's context to draw things to the canvas, with e.g. methods like
    fillRect.
    """
    width, height = canvas.width, canvas.height

    # if controls.pressed:
    #     log.debug("Keys pressed: %s", controls.pressed)
    # log.debug(controls.mouse.move)
    if controls.click:
        log.debug("Mouse click at: %s", controls.mouse.click)
        planet = solar_sys.get_clicked_object(controls.mouse.click)
        if planet:
            log.debug("Clicked on: %s", planet.name)

    """ --- Do anything that needs to be drawn in this frame here --- """
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, width, height)

    stars.render(ctx, timestamp)  
    solar_sys.update_orbits(0.20)
    solar_sys.render(ctx, timestamp)

    """ --- That was everything that needed to be drawn in that frame --- """

    # if a click event occurred and nothing made use of it during this loop, clear the click flag
    controls.click = False
    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

game_loop_proxy = create_proxy(game_loop)

# Start loop
window.requestAnimationFrame(game_loop_proxy)