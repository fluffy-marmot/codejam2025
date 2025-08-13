from consolelogger import getLogger
from controls import GameControls
from js import document, window  # type: ignore[attr-defined]
from player import Player
from pyodide.ffi import create_proxy  # type: ignore[attr-defined]
from solar_system import SolarSystem
from stars import StarSystem

log = getLogger(__name__)

# References to the useful html elements
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight
canvas = document.getElementById("gameCanvas")
ctx = canvas.getContext("2d")


# TODO: the resizing and margins needs work, I suck with CSS / html layout
def resize_canvas(event=None) -> None:
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

window.controls = GameControls(canvas)
controls = window.controls
sprites = window.sprites
log.debug("Sprite URLs: %s", sprites)

solar_sys = SolarSystem([canvas.width, canvas.height])

player = Player(sprites["player"], canvas.width / 2, canvas.height / 2, scale=0.1)
window.player = player  # expose instance globally
log.info("Created player at position (%s, %s)", player.x, player.y)

# as number of stars increase, the radius should decrease
num_stars = 100
stars = StarSystem(
    num_stars=num_stars,
    radius_min=1,
    radius_max=3,
    pulse_freq_min=3,
    pulse_freq_max=6,
)
stars.populate(width, height)


def game_loop(timestamp: float) -> None:
    """Game loop that will run roughly 60 / sec, though the timing may be dependant on monitor refresh rates (?).

    When called, timestamp argument will be time since the html document began to load, measured in miliseconds.
    We can use ctx, a wrapper for an html canvas's context to draw things to the canvas, with e.g. methods like
    fillRect.
    """
    width, height = canvas.width, canvas.height

    # if controls.pressed:
    #     log.debug("Keys pressed: %s", controls.pressed)
    # log.debug(controls.mouse.move)

    # Not doing anything with this at the moment, but this returns the planet clicked, if any
    if controls.click:
        log.debug("Mouse click at: %s", controls.mouse.click)
        planet = solar_sys.get_object_at_position(controls.mouse.click)
        if planet:
            log.debug("Clicked on: %s", planet.name)

    """ --- Do anything that needs to be drawn in this frame here --- """
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, width, height)

    stars.render(ctx, timestamp)
    solar_sys.update_orbits(0.20)
    solar_sys.render(ctx, timestamp)

    if player:
        player.render(ctx, timestamp)
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
