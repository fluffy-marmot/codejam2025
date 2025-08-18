"""
Script to extract sprites from recycle_items.png, resize them to 100x100 with padding,
and add them to the asteroid spritesheet.
"""

import os
from pathlib import Path

import numpy as np
from PIL import Image

cur_dir = Path(__file__).resolve().parent

def extract_recycle_sprites():
    """Extract individual sprites from recycle_items.png"""
    recycle_path = cur_dir.parent / "static" / "sprites" / "asteroid sprites" / "recycle_items.png"
    
    if not recycle_path.exists():
        print(f"Error: {recycle_path} not found")
        return []
    
    # Load the recycle items spritesheet
    recycle_sheet = Image.open(recycle_path)
    sheet_width, sheet_height = recycle_sheet.size
    
    print(f"Recycle spritesheet dimensions: {sheet_width}x{sheet_height}")
    
    # Estimate sprite size by looking at the image
    # We'll assume it's a horizontal strip of sprites
    # Let's try to detect individual sprites by looking for vertical gaps
    
    # Convert to numpy array for analysis
    sheet_array = np.array(recycle_sheet)
    
    # Check if there are transparent columns that separate sprites
    alpha_channel = sheet_array[:, :, 3] if sheet_array.shape[2] == 4 else np.ones((sheet_height, sheet_width)) * 255
    
    # Find columns that are completely transparent
    transparent_cols = np.all(alpha_channel == 0, axis=0)
    
    # Find transitions from non-transparent to transparent (sprite boundaries)
    boundaries = []
    in_sprite = False
    sprite_start = 0
    
    for col in range(sheet_width):
        if not transparent_cols[col] and not in_sprite:
            # Start of a sprite
            sprite_start = col
            in_sprite = True
        elif transparent_cols[col] and in_sprite:
            # End of a sprite
            boundaries.append((sprite_start, col))
            in_sprite = False
    
    # Handle case where last sprite goes to the edge
    if in_sprite:
        boundaries.append((sprite_start, sheet_width))
    
    print(f"Found {len(boundaries)} sprites with boundaries: {boundaries}")
    
    # If we can't detect boundaries automatically, assume equal-width sprites
    if not boundaries:
        # Let's assume 16 sprites in a horizontal row (common for item spritesheets)
        sprite_width = sheet_width // 16
        boundaries = [(i * sprite_width, (i + 1) * sprite_width) for i in range(16)]
        print(f"Using equal-width assumption: {sprite_width}px wide sprites")
    
    # Extract each sprite
    sprites = []
    for i, (start_x, end_x) in enumerate(boundaries):
        # Extract the sprite
        sprite = recycle_sheet.crop((start_x, 0, end_x, sheet_height))
        
        # Resize to 100x100 with padding
        resized_sprite = resize_with_padding(sprite, (100, 100))
        sprites.append(resized_sprite)
        
        # Save individual sprite for debugging
        debug_path = cur_dir.parent / "static" / "sprites" / "asteroid sprites" / f"recycle_{i:02d}.png"
        resized_sprite.save(debug_path)
        print(f"Saved recycle sprite {i} to {debug_path}")
    
    return sprites

def resize_with_padding(image, target_size):
    """Resize image to target size while maintaining aspect ratio and adding transparent padding"""
    target_width, target_height = target_size
    
    # Calculate scaling factor to fit within target size
    width_ratio = target_width / image.width
    height_ratio = target_height / image.height
    scale_factor = min(width_ratio, height_ratio)
    
    # Calculate new size after scaling
    new_width = int(image.width * scale_factor)
    new_height = int(image.height * scale_factor)
    
    # Resize the image
    resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create new image with transparent background
    result = Image.new("RGBA", target_size, (0, 0, 0, 0))
    
    # Center the resized image
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    
    result.paste(resized, (x_offset, y_offset), resized if resized.mode == 'RGBA' else None)
    
    return result

def rebuild_asteroid_spritesheet():
    """Rebuild the asteroid spritesheet including the new recycle sprites"""
    asteroid_dir = cur_dir.parent / "static" / "sprites" / "asteroid sprites"
    
    # Get all existing asteroid PNG files (excluding recycle_items.png and newly created recycle_XX.png)
    all_files = [f for f in os.listdir(asteroid_dir) if f.endswith(".png")]
    asteroid_files = [f for f in all_files if f != "recycle_items.png" and not f.startswith("recycle_")]
    
    print(f"Found {len(asteroid_files)} original asteroid files")
    
    # Extract recycle sprites
    recycle_sprites = extract_recycle_sprites()
    print(f"Extracted {len(recycle_sprites)} recycle sprites")
    
    # Load all asteroid images
    all_sprites = []
    collision_radii = []
    
    # Add original asteroids
    for filename in sorted(asteroid_files):
        asteroid = Image.open(asteroid_dir / filename)
        all_sprites.append(asteroid)
        
        # Calculate collision radius based on non-transparent pixels
        pixel_alpha_values = np.array(asteroid)[:, :, 3] if np.array(asteroid).shape[2] == 4 else np.ones(asteroid.size[::-1]) * 255
        non_transparent_count = np.sum(pixel_alpha_values > 0)
        collision_radii.append(int(np.sqrt(non_transparent_count / np.pi)))
    
    # Add recycle sprites
    for i, sprite in enumerate(recycle_sprites):
        all_sprites.append(sprite)
        
        # Calculate collision radius for recycle sprites
        pixel_alpha_values = np.array(sprite)[:, :, 3]
        non_transparent_count = np.sum(pixel_alpha_values > 0)
        collision_radii.append(int(np.sqrt(non_transparent_count / np.pi)))
    
    # Create the combined spritesheet
    if all_sprites:
        # Assume all sprites are now the same size (100x100 for recycle, variable for asteroids)
        # We need to standardize - let's make everything 100x100
        standardized_sprites = []
        
        for sprite in all_sprites:
            if sprite.size != (100, 100):
                # Resize asteroid sprites to 100x100 with padding
                standardized_sprite = resize_with_padding(sprite, (100, 100))
                standardized_sprites.append(standardized_sprite)
            else:
                standardized_sprites.append(sprite)
        
        # Calculate grid layout
        num_sprites = len(standardized_sprites)
        cols = int(num_sprites**0.5) + 1
        rows = (num_sprites + cols - 1) // cols
        
        print(f"Creating combined spritesheet: {cols}x{rows} grid for {num_sprites} sprites")
        
        # Create the spritesheet
        sprite_size = 100  # All sprites are now 100x100
        spritesheet = Image.new("RGBA", (sprite_size * cols, sprite_size * rows), (0, 0, 0, 0))
        
        # Paste each sprite
        for i, sprite in enumerate(standardized_sprites):
            col = i % cols
            row = i // cols
            x = col * sprite_size
            y = row * sprite_size
            
            spritesheet.paste(sprite, (x, y))
            
            sprite_type = "recycle" if i >= len(asteroid_files) else "asteroid"
            print(f"Added {sprite_type} sprite {i} at position ({col}, {row})")
        
        # Save the new spritesheet
        output_path = cur_dir.parent / "static" / "sprites" / "asteroids.png"
        spritesheet.save(output_path)
        print(f"Combined spritesheet saved to: {output_path}")
        print(f"Grid dimensions: {cols} columns x {rows} rows")
        print(f"Each sprite: {sprite_size}x{sprite_size} pixels")
        print(f"Total sprites: {len(asteroid_files)} asteroids + {len(recycle_sprites)} recycle items = {num_sprites}")
        
        print("Collision radii:")
        print(collision_radii)
        
        return True
    else:
        print("No sprites found to process")
        return False

if __name__ == "__main__":
    success = rebuild_asteroid_spritesheet()
    if success:
        print("Successfully rebuilt asteroid spritesheet with recycle items!")
    else:
        print("Failed to rebuild spritesheet")
