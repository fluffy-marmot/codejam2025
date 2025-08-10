from js import document, window # type: ignore
from pyodide.ffi import create_proxy # type: ignore

import math, time

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

# Game state
t0 = time.time()

def game_loop(timestamp):
    width, height = canvas.width, canvas.height

    # Clear
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    # Draw a moving circle
    t = time.time() - t0
    x = canvas.width/2 + math.sin(t*2) * 100
    y = canvas.height/2 + math.cos(t*2) * 100
    r = 30

    ctx.beginPath()
    ctx.arc(x, y, r, 0, math.pi * 2)
    ctx.fillStyle = "red"
    ctx.fill()

    # Schedule next frame
    window.requestAnimationFrame(game_loop_proxy)

game_loop_proxy = create_proxy(game_loop)

# Start loop
window.requestAnimationFrame(game_loop_proxy)