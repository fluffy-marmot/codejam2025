import time

"""
using # type: ignore since these imports are only available in the pyodide environment and pylance
will complain about them otherwise
"""
from js import document, window  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from solar_system import SolarSystem # to be able to import other files they need to be added to pyscript.json

""" references to the useful html elements """
container = document.getElementById("canvasContainer")
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

solar_sys = SolarSystem([canvas.width, canvas.height])

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

    """ --- Do anything that needs to be drawn in this frame here --- """
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, width, height)

    solar_sys.update_orbits(0.20)
    solar_sys.render(ctx, timestamp)

    """ --- That was everything that needed to be drawn in tat frame --- """

    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

game_loop_proxy = create_proxy(game_loop)

# Start loop
window.requestAnimationFrame(game_loop_proxy)