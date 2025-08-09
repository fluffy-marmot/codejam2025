import pygame


class Input:
    
    def __init__(self):
        self.quit = False
        self.keys_down = []
        self.keys_held = []
        self.keys_up = []
        self.mouse_buttons = {
            "left": False,
            "right": False, 
            "middle": False
        }
        self.mouse_pos = (0, 0)
        self.mouse_motion = (0, 0)
        self.mouse_wheel_x = 0
        self.mouse_wheel_y = 0
        self.drag_start_pos = None
        self.is_dragging = False
        
        self.double_click = False
        self.last_click_time = 0
        self.double_click_threshold = 400  # milliseconds
        
        self.modifiers = {
            "shift": False,
            "ctrl": False,
            "alt": False
        }
        
    def reset_states(self):
        self.keys_down.clear()
        self.keys_up.clear()
        self.mouse_motion = (0, 0)
        self.mouse_wheel_y = 0
        
    def update(self):
        self.reset_states()
        
        # Update modifier keys
        mod_keys = pygame.key.get_mods()
        self.modifiers["shift"] = bool(mod_keys & pygame.KMOD_SHIFT)
        self.modifiers["ctrl"] = bool(mod_keys & pygame.KMOD_CTRL)
        self.modifiers["alt"] = bool(mod_keys & pygame.KMOD_ALT)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
            elif event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                if key_name not in self.keys_held:
                    self.keys_down.append(key_name)
                    self.keys_held.append(key_name)
            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key)
                if key_name in self.keys_held:
                    self.keys_held.remove(key_name)
                    self.keys_up.append(key_name)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._update_mouse(event.button, True)
                
                if event.button == 1:  # Left button
                    # Drag handling
                    self.drag_start_pos = event.pos
                    
                    # Double click detection
                    current_time = pygame.time.get_ticks()
                    if current_time - self.last_click_time < self.double_click_threshold:
                        self.double_click = True
                    self.last_click_time = current_time
            elif event.type == pygame.MOUSEBUTTONUP:
                self._update_mouse(event.button, False)
                if event.button == 1:  # Left button
                    self.is_dragging = False
                    self.drag_start_pos = None
            elif event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                self.mouse_motion = event.rel
                if self.drag_start_pos and self.mouse_buttons["left"]:
                    self.is_dragging = True
            elif event.type == pygame.MOUSEWHEEL:
                self.mouse_wheel_y = event.y
                
    def get_modifier(self, modifier):
        return self.modifiers.get(modifier, False)
    
    def _update_mouse(self, button, is_down):
        if button == 1:
            self.mouse_buttons["left"] = is_down
        elif button == 2:
            self.mouse_buttons["middle"] = is_down
        elif button == 3:
            self.mouse_buttons["right"] = is_down
            
    def key_down(self, key):
        return key in self.keys_down
    
    def key_up(self, key):
        return key in self.keys_up
    
    def key_held(self, key):
        return key in self.keys_held
    
    def get_mouse_states(self):
        return self.mouse_buttons
    
    def get_mouse_pos(self):
        return self.mouse_pos
    
    def get_mouse_dir(self):
        """Returns the dominant direction of mouse movement as a string"""
        dx, dy = self.mouse_motion
        
        if abs(dx) > abs(dy):
            if dx > 0:
                return "right"
            elif dx < 0:
                return "left"
        elif abs(dy) > abs(dx):
            if dy > 0:
                return "down"
            elif dy < 0:
                return "up"
        return "none"
    
    def get_drag_distance(self):
        """Returns the distance dragged from start position or None if not dragging"""
        if not self.is_dragging or not self.drag_start_pos:
            return None
        dx = self.mouse_pos[0] - self.drag_start_pos[0]
        dy = self.mouse_pos[1] - self.drag_start_pos[1]
        return (dx, dy)

    def get_drag_start_pos(self):
        """Returns the position where dragging began or None if not dragging"""
        return self.drag_start_pos
    
    def is_double_click(self):
        """Returns True if double click was detected this frame"""
        return self.double_click
    
    
    def __str__(self):
        """Returns a detailed string representation of the current input state for debugging"""
        lines = [
            "Input State:",
            "------------",
            f"Quit: {self.quit}",
            "",
            "Keyboard:",
            f"  Keys Down: {', '.join(self.keys_down) if self.keys_down else 'None'}",
            f"  Keys Held: {', '.join(self.keys_held) if self.keys_held else 'None'}",
            f"  Keys Up: {', '.join(self.keys_up) if self.keys_up else 'None'}",
            "",
            "Modifiers:",
            f"  Shift: {self.modifiers['shift']}",
            f"  Ctrl: {self.modifiers['ctrl']}",
            f"  Alt: {self.modifiers['alt']}",
            "",
            "Mouse:",
            f"  Position: {self.mouse_pos}",
            f"  Motion: {self.mouse_motion}",
            f"  Direction: {self.get_mouse_dir()}",
            f"  Left Button: {self.mouse_buttons['left']}",
            f"  Right Button: {self.mouse_buttons['right']}",
            f"  Middle Button: {self.mouse_buttons['middle']}",
            f"  Wheel X: {self.mouse_wheel_x}",
            f"  Wheel Y: {self.mouse_wheel_y}",
            "",
            "Dragging:",
            f"  Is Dragging: {self.is_dragging}",
            f"  Drag Start: {self.drag_start_pos}",
            f"  Drag Distance: {self.get_drag_distance()}",
            "",
            f"Double Click: {self.double_click}"
        ]
        return "\n".join(lines)

    # For convenience, you might also want to add a __repr__ method
    def __repr__(self):
        """Concise representation focusing on key state information"""
        return (f"Input(quit={self.quit}, "
                f"keys_down={len(self.keys_down)}, "
                f"keys_held={len(self.keys_held)}, "
                f"mouse_pos={self.mouse_pos}, "
                f"is_dragging={self.is_dragging})")