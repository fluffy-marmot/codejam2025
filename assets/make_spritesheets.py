"""
just a quick and dirty script to turn a series of 50 .png sprites into a single spritesheet file. We're not
using this otherwise and we may well not need it again, but this can live here just in case we generate more
planet sprites on that website
"""

from pathlib import Path
import os

from PIL import Image

cur_dir = Path(__file__).resolve().parent

# Planet spritesheets
for planet in "earth jupiter mars mercury neptune saturn sun uranus venus".split():
    planet_dir = cur_dir / f"{planet} sprites"
    if planet_dir.exists():
        first_frame = Image.open(planet_dir / "sprite_1.png")
        width, height = first_frame.size
        spritesheet = Image.new("RGBA", (width * 50, height), (0, 0, 0, 0))
        for fr in range(1, 51):
            frame = Image.open(planet_dir / f"sprite_{fr}.png")
            spritesheet.paste(frame, (width * (fr - 1), 0))
        
        spritesheet.save(cur_dir.parent / "static" / "sprites" / f"{planet}.png")

# Asteroid spritesheet
asteroid_dir = cur_dir.parent / "static" / "sprites" / "asteroid sprites"
if asteroid_dir.exists():
    # Get all PNG files in the asteroid directory
    asteroid_files = sorted([f for f in os.listdir(asteroid_dir) if f.endswith('.png')])
    
    if asteroid_files:
        # Load first asteroid to get dimensions
        first_asteroid = Image.open(asteroid_dir / asteroid_files[0])
        width, height = first_asteroid.size
        
        # Calculate grid layout (try to make roughly square)
        num_asteroids = len(asteroid_files)
        cols = int(num_asteroids ** 0.5) + 1
        rows = (num_asteroids + cols - 1) // cols
        
        print(f"Creating asteroid spritesheet: {cols}x{rows} grid for {num_asteroids} asteroids")
        
        # Create the spritesheet
        spritesheet = Image.new("RGBA", (width * cols, height * rows), (0, 0, 0, 0))
        
        # Paste each asteroid
        for i, filename in enumerate(asteroid_files):
            asteroid = Image.open(asteroid_dir / filename)
            
            # Calculate position in grid
            col = i % cols
            row = i // cols
            x = col * width
            y = row * height
            
            spritesheet.paste(asteroid, (x, y))
            print(f"Added {filename} at position ({col}, {row})")
        
        # Save the spritesheet
        output_path = cur_dir.parent / "static" / "sprites" / "asteroids.png"
        spritesheet.save(output_path)
        print(f"Asteroid spritesheet saved to: {output_path}")
        print(f"Grid dimensions: {cols} columns x {rows} rows")
        print(f"Each sprite: {width}x{height} pixels")
