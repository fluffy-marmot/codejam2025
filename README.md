# Python Discord Code Jam 2025: Cool Cacti

## overview
We created pygame-like functionality using pyodide. Using a context object, we are able to replicate JavaScript like functionality in python. See https://developer.mozilla.org/en-US/docs/Web/API for what methods ctx has. 

## purpose
Many aspiring python developers use pygame to improve their skills. However, it isn't so easy sharing their game with their less technical friends or family. They could use something like PyInstaller, but that requires people to trust executables (I don't really like this section tbh)

## Theme
We achieved connection to the theme in 2 ways:
### Pyodide
Pyodide is inherently the wrong tool for the job, since libraries such as Pygbag exist. (Guys, add some extra description as to how developing with Pyodide made it harder)
Suggestions:
Extra files (html, css, extra py files that would otherwise not be needed if not for Pyodide)
Working with ctx (no autocomplete, docs are in JavaScript and not Py)
### The game
(Spoilers!) The introduction depicts aliens flying around space past the speed of light, about to turn on their super advanced intergalatic planet scanner. Today, it fails. Luckily, one of the aliens has a barcode scanner from his work, but they need to go orbit planets for some time to scan, rather than fly faster than light. Our game and its mechanics are centered around this barcode scanner that they must use. It's the "wrong tool for the job", since you really shouldn't be scanning planets with a supermarket barcode scanner. (Still works though, they are very advanced aliens!)

## Individual contributions
RealisticTurtle: Intro scene, Game scene, story, stars, scanning mechanics

Soosh: Libary research, Pyodide setup, colored stars

Dark Zero: main scene, sprites, player mechanics, asteroids, end scene

Doomy: Text boxes, endscreen, experimented with Marimo

## installation and usage
Uhh idk theres no reqs.txt

## Gameplay:
View the video at: https://youtube.com/placeholder