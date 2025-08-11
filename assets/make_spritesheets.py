# just a quick and dirty script to turn all these sprite files into simpler spritesheets

from pathlib import Path

from PIL import Image

cur_dir = Path(__name__).resolve().parent

for planet in "earth jupiter mars mercury neptune saturn sun uranus venus".split():
    planet_dir = cur_dir / f"{planet} sprites"
    first_frame = Image.open(planet_dir / "sprite_1.png")
    width, height = first_frame.size
    spritesheet = Image.new("RGBA", (width * 50, height), (0, 0, 0, 0))
    for fr in range(1, 51):
        frame = Image.open(planet_dir / f"sprite_{fr}.png")
        spritesheet.paste(frame, (width * (fr - 1), 0))
    
    spritesheet.save(cur_dir.parent / "static" / "sprites" / f"{planet}.png")