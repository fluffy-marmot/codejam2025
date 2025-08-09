import pygame

class SimpleLogger:
    @staticmethod
    def log_message(message, level="INFO"):
        print(f"[{level}] {message}")
    
    @staticmethod
    def log_error(exception, message):
        print(f"[ERROR] {message}: {str(exception)}")

logger = SimpleLogger()

def normalize_color(color):
    """Convert various color formats to PyGame compatible format"""
    try:
        if isinstance(color, tuple) or isinstance(color, list):
            if len(color) == 4:
                # RGBA format - return both color and alpha
                r, g, b, a = color
                return pygame.Color(r, g, b), a
            elif len(color) == 3:
                # RGB format
                return pygame.Color(color[0], color[1], color[2]), 255
            else:
                error_msg = f"Invalid color format {color}, using default"
                logger.log_message(error_msg, "WARNING")
                return pygame.Color(255, 255, 255), 255
        return color, 255  # Already a PyGame Color or other compatible format
    except Exception as e:
        logger.log_error(e, f"Failed to normalize color: {color}")
        return pygame.Color(255, 255, 255), 255  # Return default white color


class UIElement:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        
    def update(self, input):
        pass
    
    def render(self, surface):
        pass

class Button(UIElement):
    def __init__(self, x, y, width, height, text, callback, color=(255, 255, 255), hover_color=(130, 130, 130), font_family=None, text_color=(0, 0, 0, 1), elevation=6, font_size=24):
        super().__init__(x, y, width, height)
        self.text = text
        self.callback = callback

        try:
            # Ensure colors are properly formatted for PyGame
            self.color, self.color_alpha = normalize_color(color)
            self.hover_color, self.hover_alpha = normalize_color(hover_color)
            self.current_color = self.color
            self.text_color, self.text_alpha = normalize_color(text_color)
            
            # Create separate rectangles for 3D effect
            self.top_rect = pygame.Rect(x, y, width, height)
            self.bottom_rect = pygame.Rect(x, y + elevation, width, height)
            self.elevation = elevation
            self.dynamic_elevation = elevation
            self.original_y_pos = y
            
            self.top_color = self.current_color
            self.bottom_color = pygame.Color(
                max(0, self.current_color.r - 40),
                max(0, self.current_color.g - 40),
                max(0, self.current_color.b - 40)
            )
            
            # Set alpha from color if provided
            if self.color_alpha < 255:
                self.alpha = self.color_alpha
            
            # Load font
            try:
                self.font = pygame.font.Font(font_family, font_size) if font_family else pygame.font.SysFont('Arial', 24)
            except Exception as e:
                error_msg = f"Could not load font '{font_family}', falling back to default"
                logger.log_error(e, error_msg)
                self.font = pygame.font.SysFont('Arial', font_size)
                
            self.is_pressed = False  # Track press state
        except Exception as e:
            logger.log_error(e, f"Failed to initialize Button at ({x}, {y})")
            raise
        
    def update(self, input):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)
        
        # Update visual state
        self.current_color = self.hover_color if hover else self.color
        self.bottom_color = pygame.Color(
            max(0, self.current_color.r - 40),
            max(0, self.current_color.g - 40),
            max(0, self.current_color.b - 40)
        )
        
        # Handle button press with state tracking to prevent multiple triggers
        if hover:
            if input.mouse_buttons["left"]:  # Left click
                if not self.is_pressed:  # Only trigger once when first pressed
                    self.is_pressed = True
                    self.dynamic_elevation = 0
                    self.callback()
            else:
                self.is_pressed = False
                self.dynamic_elevation = self.elevation

        else:
            self.is_pressed = False
            self.dynamic_elevation = self.elevation
            
        # Update button rectangles
        self.top_rect.y = self.original_y_pos - self.dynamic_elevation
        self.bottom_rect.y = self.original_y_pos
    
    def render(self, surface):
        if not self.visible:
            return
        
        try:
            # For transparency effects, we can create a temporary surface
            if hasattr(self, 'alpha') and self.alpha < 255:
                # Create a temporary surface with per-pixel alpha
                temp_surface = pygame.Surface((self.rect.width, self.rect.height + self.elevation), pygame.SRCALPHA)
                
                # Extract RGB from PyGame Color object and create proper RGBA tuple
                rgba_color = (self.current_color.r, self.current_color.g, self.current_color.b, self.alpha)
                bottom_rgba = (self.bottom_color.r, self.bottom_color.g, self.bottom_color.b, self.alpha)
                
                # Draw bottom rect first (shadow/3D effect)
                if self.dynamic_elevation > 0:
                    pygame.draw.rect(temp_surface, bottom_rgba, 
                                    pygame.Rect(0, self.elevation, self.rect.width, self.rect.height), 
                                    border_radius=3)
                
                # Draw top button
                pygame.draw.rect(temp_surface, rgba_color, 
                                pygame.Rect(0, self.elevation - self.dynamic_elevation, 
                                          self.rect.width, self.rect.height), 
                                border_radius=3)
                
                # Draw borders
                pygame.draw.rect(temp_surface, (50, 50, 50), 
                                pygame.Rect(0, self.elevation - self.dynamic_elevation, 
                                          self.rect.width, self.rect.height), 
                                width=2, border_radius=3)
                
                # Render text to temp surface
                try:
                    text_surf = self.font.render(self.text, True, self.text_color)
                    text_rect = text_surf.get_rect(center=(self.rect.width//2, 
                                                         (self.rect.height//2) + (self.elevation - self.dynamic_elevation)))
                    temp_surface.blit(text_surf, text_rect)
                except Exception as e:
                    logger.log_error(e, f"Error rendering button text: {self.text}")
                
                # Blit the temp surface onto the main surface
                surface.blit(temp_surface, (self.rect.x, self.rect.y - self.elevation))
            else:
                # Draw bottom rect first (shadow/3D effect)
                if self.dynamic_elevation > 0:
                    pygame.draw.rect(surface, self.bottom_color, 
                                    pygame.Rect(self.rect.x, self.original_y_pos, 
                                             self.rect.width, self.rect.height), 
                                    border_radius=3)
                
                # Draw top button
                top_rect = pygame.Rect(self.rect.x, self.original_y_pos - self.dynamic_elevation, 
                                     self.rect.width, self.rect.height)
                pygame.draw.rect(surface, self.current_color, top_rect, border_radius=3)
                pygame.draw.rect(surface, pygame.Color(50, 50, 50), top_rect, width=2, border_radius=3)
                
                # Render text
                try:
                    text_surf = self.font.render(self.text, True, self.text_color)
                    text_rect = text_surf.get_rect(center=top_rect.center)
                    surface.blit(text_surf, text_rect)
                except Exception as e:
                    logger.log_error(e, f"Error rendering button text: {self.text}")
        except Exception as e:
            logger.log_error(e, f"Error rendering button: {self.text}")

class Label(UIElement):
    def __init__(self, x, y, text, color=(255, 255, 255), font_size=20, font_family=None):
        try:
            # Normalize color
            self.color, self.alpha = normalize_color(color)
            
            # Load font
            try:
                self.font = pygame.font.Font(font_family, font_size) if font_family else pygame.font.SysFont('Arial', font_size)
            except Exception as e:
                error_msg = f"Could not load font '{font_family}', falling back to default"
                logger.log_error(e, error_msg)
                self.font = pygame.font.SysFont('Arial', font_size)
            
            # Create text surface to determine size
            text_surf = self.font.render(text, True, self.color)
            super().__init__(x, y, text_surf.get_width(), text_surf.get_height())
            self.text = text
        except Exception as e:
            logger.log_error(e, f"Failed to initialize Label: '{text}' at ({x}, {y})")
            super().__init__(x, y, 100, 20)  # Default size if rendering failed
            self.text = text
    
    def render(self, surface):
        if not self.visible:
            return
            
        try:
            # Check if we need to handle alpha
            if hasattr(self, 'alpha') and self.alpha < 255:
                # Create text with alpha
                text_surf = self.font.render(self.text, True, self.color)
                
                # Apply alpha by creating a surface with per-pixel alpha
                alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
                alpha_surf.fill((255, 255, 255, 0))  # Transparent
                
                # Blit with alpha
                alpha_surf.blit(text_surf, (0, 0))
                # Set alpha for the entire surface
                alpha_surf.set_alpha(self.alpha)
                
                # Blit to destination
                surface.blit(alpha_surf, self.rect)
            else:
                # Standard rendering for opaque text
                text_surf = self.font.render(self.text, True, self.color)
                surface.blit(text_surf, self.rect)
        except Exception as e:
            logger.log_error(e, f"Error rendering label: {self.text}")
            
class UIManager:
    def __init__(self, window):
        self.window = window
        self.elements = []
        self.cursor_scale = 1
        self.drag_weight = 0
        self.ui_surface = pygame.Surface(window.screen_size, pygame.SRCALPHA)
    
    def add_element(self, element):
        self.elements.append(element)
        return element
        
    def update(self, input):
        for element in self.elements:
            element.update(input)
    
    def render(self):
        # Clear with completely transparent background
        self.ui_surface.fill((0, 0, 0, 0))
        
        # Render all elements
        for element in self.elements:
            element.render(self.ui_surface)
            
        if self.window.input.mouse_wheel_y != 0:
            value = self.window.input.mouse_wheel_y
            if value > 0:
                self.cursor_scale += round(value/10, 2)
            elif value < 0:
                self.cursor_scale += round(value/10, 2)
        pygame.draw.circle(self.ui_surface, (0, 255, 0), self.window.input.get_mouse_pos(), radius=10*self.cursor_scale, width=1)
        if self.window.input.is_dragging and self.window.input.drag_start_pos:
            pygame.draw.line(
                self.ui_surface,
                (0, 255, 0),
                self.window.input.drag_start_pos,
                self.window.input.get_mouse_pos(),
                2
            )
        return self.ui_surface

