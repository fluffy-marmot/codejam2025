# Python Discord Code Jam 2025: Cool Cacti

## Overview
We created a space exploration game in the browser using Pyscript. The rendering is done through accessing the Pyscript binded Document Object Models, primarily using the CavnasContextRendering2D interface. 
See the [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D) for the properties and methods available.

"Building Blocks" we implemented for our game:
- Drawing shapes (eclipses, rectangles, etc)
- Audio
- Sprites/Spritesheets
## Frameworks Used
Pyscript, the approved framework, was used to interact with the webpage Canvas for rendering and to load the pyodide interpreter for running our project code.
Flask is used to dynamically load and serve our game's HTML template with pyscript information required for the game to run.

Suggestions:
Extra files (html, css, extra py files that would otherwise not be needed if not for pyodide)
Working with ctx (no autocomplete, docs are in JavaScript and not Py)
We need to hit this criteria here: "Which approved library/framework was used and how it was used"

## Usage

### Prerequisites to run
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
For alternative dependency managers, refer to the dependencies section in pyproject.toml


### Running the Application
Start the application with:
```bash
uv run app.py
```
Then navigate to the URL with the browser of your choice

## Theme
We achieved connection to the theme in 2 ways:
### Pyodide
Pyodide is inherently the wrong tool for the job, since libraries such as pygbag exist, or you could package your pygame with something like PyInstaller.

### The Game Theme
(Spoilers!) The introduction depicts aliens flying around space past the speed of light, about to turn on their super advanced intergalactic planet scanner. Today, it fails. Luckily, one of the aliens has a barcode scanner from his work, but they need to go orbit planets for some time to scan, rather than fly faster than light. Our game and its mechanics are centered around this barcode scanner that they must use. It's the "wrong tool for the job", since you really shouldn't be scanning planets with a supermarket barcode scanner. (Still works though, they are very advanced aliens!)

## Individual contributions
(Add your contributions here)

RealisticTurtle: Intro scene, Game scene, story, stars, scanning mechanics

Soosh: Library research, pyodide setup, colored stars

Dark Zero: main scene, sprites, player mechanics, asteroid logic, end scene

Doomy: Text boxes, end scene, experimented with marimo

## The game:
View the video at: https://www.youtube.com/watch?v=J8LKGUsTeAo

The video will display the game and its mechanics.
