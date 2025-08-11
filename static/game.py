import time

from js import document, window  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
from solar_system import SolarSystem

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

resize_proxy = create_proxy(resize_canvas)
window.addEventListener("resize", resize_proxy)
resize_canvas()

solar_sys = SolarSystem([canvas.width, canvas.height])

# Game state
t0 = time.time()

def game_loop(timestamp):
    width, height = canvas.width, canvas.height

    # Clear
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    solar_sys.update_orbits(0.20)
    solar_sys.render(ctx, timestamp)

    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

game_loop_proxy = create_proxy(game_loop)

# Start loop
window.requestAnimationFrame(game_loop_proxy)