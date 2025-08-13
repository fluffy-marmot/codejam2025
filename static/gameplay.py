from spacemass import SpaceMass
from js import window, document #type: ignore
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight
planets = {planet["name"].lower(): planet for planet in window.planets}
jupiter = SpaceMass(planets["jupiter"]["spritesheet"], 1898.0, height, 1.0)
jupiter.set_position([0, height//2])
