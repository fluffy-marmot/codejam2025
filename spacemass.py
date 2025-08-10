import pygame
from pathlib import Path
import time

class SpaceMass():
    
    def __init__(self, path:str, mass:float, radius: float, init_velocity:float) -> None:
        
        self.rect = None
        self.sprites_path = Path(path)
        self.sprite_atlas = []
        self.mass = mass
        self.radius = radius
        self.initial_velocity = init_velocity
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_delay = 0.167  # (approximately 6 FPS)
        self.create_atlas()
        
    def create_atlas(self):
        for sp in self.sprites_path.iterdir():
            if sp.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                sprite = pygame.image.load(sp)
                self.sprite_atlas.append(sprite)
            
    def render(self, screen, pos:list):
        if not self.sprite_atlas:
            return
            
        # Update animation timing
        current_time = time.time()
        if current_time - self.animation_timer >= self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.sprite_atlas)
            self.animation_timer = current_time
        
        # Get current sprite
        current_sprite = self.sprite_atlas[self.current_frame]
        
        # Scale sprite based on radius
        sprite_size = int(self.radius * 2)
        scaled_sprite = pygame.transform.scale(current_sprite, (sprite_size, sprite_size))
        
        # Create rect for positioning
        rect = scaled_sprite.get_rect()
        rect.center = tuple(pos)
        
        screen.blit(scaled_sprite, rect)


