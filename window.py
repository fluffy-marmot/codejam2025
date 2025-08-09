import pygame
import sys
from input import Input
from ui import UIManager

class SimpleLogger:
    @staticmethod
    def log_message(message, level="INFO"):
        print(f"[{level}] {message}")
    
    @staticmethod
    def log_error(exception, message):
        print(f"[ERROR] {message}: {str(exception)}")

logger = SimpleLogger()

class Window:
    
    def __init__(self, screen_size=[512, 512]):
        # Initialize pygame first
        pygame.init()
        
        self.running = True
        
        self.clock = pygame.time.Clock()
        
        self.input = Input()
        
        self.screen_size = screen_size
        
        self.time = 0
        
        # Create UI manager
        self.ui_manager = UIManager(self)
        
        # Initialize pygame display
        self.screen = None
    
    def initialize(self):
        """Initialize pygame display"""
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Code Jam 2025")
    
    
    def render(self):
        if self.screen is not None:
            self.screen.fill((0, 0, 0))
            
    
    def update(self):
        pass

        
    def render_ui(self):
        try:
            # Get UI surface from the UI manager
            ui_surface = self.ui_manager.render()
            
            if ui_surface is None:
                logger.log_message("UI surface is None, cannot render UI", level="ERROR")
                return
            
            if self.screen is None:
                logger.log_message("Screen is not initialized, cannot render UI", level="ERROR")
                return
            
            # blit UI surface onto the main display
            self.screen.blit(ui_surface, (0, 0))
            
        except Exception as e:
            logger.log_error(e, "UI rendering failed")
    
    def run(self):
        try:
            self.initialize()
            
            FIXED_DELTA = 1/60
            accumulator = 0
            current_time = pygame.time.get_ticks() / 1000

            while self.running:
                try:
                    self.clock.tick()
                    
                    self.input.update()
                    self.ui_manager.update(self.input)
                    
                    new_time = pygame.time.get_ticks() / 1000
                    frame_time = new_time - current_time
                    current_time = new_time
                    
                    if frame_time > 0.25:
                        frame_time = 0.25
                        
                    self.time += frame_time
                    
                    self.delta_time = frame_time
                    self.update()
                    
                    # Clear screen and render
                    self.render()
                    
                    try:
                        pygame.time.wait(1)
                        self.render_ui()
                    except Exception as e:
                        logger.log_error(e, "UI overlay failed")
                    
                    pygame.display.flip()
                    
                    if self.input.quit:
                        self.running = False
                except Exception as e:
                    logger.log_error(e, "Error in main loop")
                
            pygame.quit()
        except Exception as e:
            logger.log_error(e, "Fatal error in run method")
            pygame.quit()
        finally:
            sys.exit()