# Planet Scanners: Python Discord Code Jam 2025

We created a simple sprite-based, space-themed game using pyscript backed by pyodide and its JavaScript wrapper
capabilities to leverage JavaScript's convenient API for rendering graphics on HTML canvas elements, playing
audio, and accessing user input. We hope this can demo as an alternative to the use of a pygame wrapper such as
pygbag, without the need for its extra layer of abstraction, as the browser-side functionality of our game doesn't use anything
but the Python standard library and the pyscript & pyodide modules for accessing JavaScript functionality

### The Game

The introduction depicts aliens flying around space past the speed of light, about to turn on their super
advanced intergalactic planet scanner. Today, it fails! Luckily, one of the aliens has an old Earth-based
barcode scanner - the "wrong tool for the
job", that will have to do today. In the solar system overview screen, seen below, the player can select each of the solar system's planets in turn and must complete
a scan for that planet to complete a mission.
![Planet selection screen](/readme_images/game1.png)
The gameplay (shown in the image below) is a variation of the classic asteroids game, where
the player must dodge incoming asteroids to avoid ship damage and stay immobile while holding down the Spacebar
to progress scanning.
An animated rotating planet combined with the movement of stars off-screen in the opposite direction creates a
simple but effective perspective of the player ship orbiting a planet.
![Planet selection screen](/readme_images/game2.png)

![Planet selection screen](/readme_images/game3.png)

## Intended Event Frameworks

We used pyscript backed by the pyodide interpreter. We were pleasantly surprised by how few pyscript-specific
oddities we ran into. Using the provided JavaScript wrapper capabilities felt almost as natural as writing
JavaScript directly into the Python files, except writing in Python! To serve our single page game app, we
included an ultra-minimalistic Flask backend for convenience in designing, though with a little refactoring our page could
also be served statically. There is some very minimalistic HTML and CSS to more or less create an HTML canvas to
draw on with the appropriate styling and create the initial setup for importing our in-browser Python scripts.
It was necessary to provide the contents of a [pyscript.json](/static/pyscript.json) file to the config attribute of the <py-script> tag
of our [index.html](/templates/index.html) to let the pyscript environment allow the proper imports of modules into one another.

## Installation and Usage

### Prerequisites to Run
- Python 3.12
- [uv](https://github.com/astral-sh/uv) is recommended for the package manager
- An active internet connection (to fetch the pyodide interpreter and pyscript modules from the pyscript CDN)
### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/fluffy-marmot/codejam2025
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```
### Without uv
The dependencies are listed in [`pyproject.toml`](pyproject.toml). Since the only server-side dependency for running the
project is flask (pyscript is obtained automatically in browser as needed via CDN), the
project can be run after cloning it by simply using
```bash
pip install flask
python app.py
```
### Running the Game
Running the [app.py](/app.py) file starts the simple flask server to serve the single html page, which should be at
[http://127.0.0.1:5000](http://127.0.0.1:5000) if testing it locally. We also have a version of our game hosted
at [https://caius.pythonanywhere.com/codejam/](https://caius.pythonanywhere.com/codejam/) although this has been
slightly modified from the current repository to run as a single app within an already existing Django project.
None of the files in the `/static/` directory of the hosted version have been modified, therefore in-browser functionality
should be the same.

## Individual Contributions

RealisticTurtle: storyboarding, intro scene and story, game scene, star system, scanning mechanics

Soosh: library research, core functionality (audio and input modules, gameloop, scene system), code integration, debris
system

Dark Zero: planet selection scene, sprites, spritesheet helper scripts, player mechanics, asteroid
implementation, collision logic, end scene

Doomy: dynamic textboxes, end scene and credits, Horizons API functionality,
refactoring and maintenance, scanner refinement

## Game Demonstration

This video is a quick demonstration of our game and its mechanics by our teammade RealisticTurtle

View the demo on [Youtube](https://www.youtube.com/watch?v=J8LKGUsTeAo)