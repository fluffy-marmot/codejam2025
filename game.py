from window import Window
from ui import *
import os

class SpaceGame(Window):
    
    def __init__(self, screen_size=[512, 512]):
        super().__init__(screen_size)
        
        # Spaceship properties
        self.spaceship_pos = [screen_size[0] // 2, screen_size[1] // 2]
        self.spaceship_speed = 150
        self.spaceship_image = None
        self.spaceship_rect = None
        
        # Add UI elements
        self.setup_ui()
        
    def initialize(self):
        """Initialize pygame display and load assets"""
        super().initialize()
        
        self.load_spaceship_image('spaceship.png')
        
    def load_spaceship_image(self, image:str):
        """Load the spaceship PNG image"""
        image_path = image
        if os.path.exists(image_path):
            self.spaceship_image = pygame.image.load(image_path).convert_alpha()
            # Scale it down if it's too big
            if self.spaceship_image.get_width() > 100:
                scale_factor = 100 / self.spaceship_image.get_width()
                new_width = int(self.spaceship_image.get_width() * scale_factor)
                new_height = int(self.spaceship_image.get_height() * scale_factor)
                self.spaceship_image = pygame.transform.scale(self.spaceship_image, (new_width, new_height))
            
            self.spaceship_rect = self.spaceship_image.get_rect()
            self.spaceship_rect.center = tuple(self.spaceship_pos)
            print(f"Loaded spaceship image: {self.spaceship_image.get_size()}")

    def update(self):
        """Update game logic"""
        # Handle spaceship movement
        self.handle_movement()
        
    
    def handle_movement(self):
        """Handle spaceship movement based on input"""
        if not self.spaceship_rect:
            return
            
        movement_speed = self.spaceship_speed * self.delta_time
        
        half_width = self.spaceship_rect.width // 2
        half_height = self.spaceship_rect.height // 2
        
        new_x_right = self.spaceship_pos[0] + movement_speed
        new_x_left = self.spaceship_pos[0] - movement_speed
        new_y_up = self.spaceship_pos[1] - movement_speed
        new_y_down = self.spaceship_pos[1] + movement_speed
        
        # Check for arrow key input with proper bounds checking (accounting for center position)
        if self.input.key_held("left") and new_x_left >= half_width:
            self.spaceship_pos[0] = new_x_left
        if self.input.key_held("right") and new_x_right <= self.screen_size[0] - half_width:
            self.spaceship_pos[0] = new_x_right
        if self.input.key_held("up") and new_y_up >= half_height:
            self.spaceship_pos[1] = new_y_up
        if self.input.key_held("down") and new_y_down <= self.screen_size[1] - half_height:
            self.spaceship_pos[1] = new_y_down
        
        # Update the spaceship rectangle position
        self.spaceship_rect.center = tuple(self.spaceship_pos)
        
        
    def setup_ui(self):
        """Setup UI elements"""
        instructions = Label(10, 10, "Use Arrow Keys to Move Spaceship", color=(255, 255, 255))
        self.ui_manager.add_element(instructions)
        
    def render(self):
        """Render the game"""
        if self.screen is not None:
            self.screen.fill((10, 10, 30))
            
            # Draw the spaceship
            if self.spaceship_image and self.spaceship_rect:
                self.screen.blit(self.spaceship_image, self.spaceship_rect)
                
def main():
    # Create the spaceship game
    game = SpaceGame(screen_size=[800, 600])
    
    # Run the game
    game.run()

if __name__ == "__main__":
    main()