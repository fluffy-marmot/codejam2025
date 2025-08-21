# Python Discord Code Jam 2025: Cool Cacti

## Overview
We created pygame-like functionality using pyodide. Using a context object, we are able to replicate javascript-like functionality in Python. See https://developer.mozilla.org/en-US/docs/Web/API for what methods ctx has. The game itself is presented in the video. 

"Building Blocks" we implemented for our game:
- Drawing shapes (eclipses, rectangles, etc)
- Audio
- Sprites/Spritesheets
## Approved frameworks
We used pyodide 
(Soosh, please fill this part out)
(add some extra description as to how developing with pyodide made it harder)
Suggestions:
Extra files (html, css, extra py files that would otherwise not be needed if not for pyodide)
Working with ctx (no autocomplete, docs are in JavaScript and not Py)
We need to hit this criteria here: "Which approved library/framework was used and how it was used"

## Theme
We achieved connection to the theme in 2 ways:
### Pyodide
Pyodide is inherently the wrong tool for the job, since libraries such as pygbag exist, or you could package your pygame with something like PyInstaller.

### The game
(Spoilers!) The introduction depicts aliens flying around space past the speed of light, about to turn on their super advanced intergalactic planet scanner. Today, it fails. Luckily, one of the aliens has a barcode scanner from his work, but they need to go orbit planets for some time to scan, rather than fly faster than light. Our game and its mechanics are centered around this barcode scanner that they must use. It's the "wrong tool for the job", since you really shouldn't be scanning planets with a supermarket barcode scanner. (Still works though, they are very advanced aliens!)

## Individual contributions
(Add your contributions here)

RealisticTurtle: Intro scene, Game scene, story, stars, scanning mechanics

Soosh: Library research, pyodide setup, colored stars

Dark Zero: main scene, sprites, player mechanics, asteroid logic, end scene

Doomy: Text boxes, end scene, experimented with marimo

## Installation and usage
Uhh idk theres no reqs.txt

## The game:
View the video at: https://youtube.com/placeholder

The video will display the game and its mechanics.