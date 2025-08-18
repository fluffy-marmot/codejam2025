import re

from window import window
from common import Position, CanvasRenderingContext2D, Rect
from consolelogger import getLogger
from scene_classes import Scene, SceneManager
from spacemass import SpaceMass

log = getLogger(__name__)

def rgba_to_hex(rgba_str):
    """
    Convert "rgba(r, g, b, a)" to hex string "#RRGGBB".
    Alpha is ignored.
    """
    # Extract the numbers
    match = re.match(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\s*\)", rgba_str)
    if not match:
        raise ValueError(f"Invalid RGBA string: {rgba_str}")

    r, g, b = map(int, match.groups())
    return f"#{r:02X}{g:02X}{b:02X}"

class TextOverlay(Scene):
    DEFAULT = "No information found :("

    def __init__(self, name: str, scene_manager: SceneManager, text: str, color="rgba(0, 255, 0, 0.8)", rect=None, hint=None):
        super().__init__(name, scene_manager)
        self.bold = False
        self.color = color
        self.calculate_and_set_font()
        self.set_text(text)
        self.char_delay = 10  # milliseconds between characters
        self.margins = Position(200, 50)
        self.button_label = None
        self.button_click_callable = None
        self.other_click_callable = None
        self.deactivate()
        self.rect = rect # tuple: (x, y, width, height)
        self.muted = True
        self.center = False
        self.hint = hint
        
    def deactivate(self):
        self.active = False
        # pause text sound in case it was playing
        window.audio_handler.play_text(pause_it=True)

    def set_text(self, text: str):
        """ 
        Set a new text message for this object to display and resets relevant properties like the 
        current character position to be ready to start over. Text width is calculated for centered text
        rendering.
        """
        self.displayed_text = ""
        self.text = text
        self.char_index = 0
        self.last_char_time = 0

        # calculate text width in case we want centered text, we won't have to calculate it every frame
        self._prepare_font(window.ctx)
        self._text_width = max(window.ctx.measureText(line).width for line in self.text.split("\n"))

    def set_button(self, button_label: str | None):
        self.button_label = button_label

    def calculate_and_set_font(self) -> str:
        # Set text style based on window size
        base_size = min(window.canvas.width, window.canvas.height) / 50
        font_size = max(12, min(20, base_size))  # Scale between 12px and 20px
        self.font = {"size": font_size, "font": "'Courier New', monospace"}
        return self.font
    
    def update_textstream(self, timestamp):
        """Update streaming text"""

        if timestamp - self.last_char_time > self.char_delay and self.char_index < len(self.text):
            if not self.muted:
                window.audio_handler.play_text()
                
            chars_to_add = min(3, len(self.text) - self.char_index)
            self.displayed_text += self.text[self.char_index : self.char_index + chars_to_add]
            self.char_index += chars_to_add
            self.last_char_time = timestamp
            if self.char_index == len(self.text):
                window.audio_handler.play_text(pause_it=True)

    def _prepare_font(self, ctx):
        font = self.font or self.calculate_and_set_font()
        ctx.font = f"{'bold ' if self.bold else ''}{font['size']}px {font['font']}"
        ctx.fillStyle = rgba_to_hex(self.color)
        return font

    def render_and_handle_button(self, ctx: CanvasRenderingContext2D, overlay_bounds: Rect) -> Rect:
        """
        this function returns the button's bounding Rect as a byproduct, so it can be
        conveniently used to check for click events in the calling function
        """
        if not self.button_label:
            return None

        ctx.save()
        ctx.font = "14px Courier New"
        text_width = ctx.measureText(self.button_label).width

        button_bounds = Rect(overlay_bounds.right - (text_width + 30), overlay_bounds.bottom - 44, text_width + 20, 34)

        ctx.fillStyle = "rgba(0, 0, 0, 0.95)"
        ctx.fillRect(*button_bounds)

        # check whether mouse is currently moving over the button
        if button_bounds.contains(window.controls.mouse.move):
            ctx.fillStyle = "#ffff00"
        else:
            ctx.fillStyle = "#00ff00"

        ctx.fillText(self.button_label, button_bounds.left + 10, button_bounds.bottom - 10)
        ctx.strokeStyle = "rgba(0, 255, 0, 0.95)"
        ctx.lineWidth = 2
        ctx.strokeRect(*button_bounds)

        ctx.restore()
        return button_bounds

    def render(self, ctx: CanvasRenderingContext2D, timestamp):
        if not self.active or not self.text:
            return

        self.update_textstream(timestamp)

        if self.rect:
            x, y, width, height = self.rect
            overlay_bounds = Rect(x, y, width, height)
        else:
            overlay_width = window.canvas.width - 2 * self.margins.x
            overlay_height = window.canvas.height - 2 * self.margins.y
            overlay_bounds = Rect(self.margins.x, self.margins.y, overlay_width, overlay_height)

        # Draw transparent console background
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)"

        ctx.fillRect(*overlay_bounds)

        # Draw console border
        ctx.strokeStyle = self.color
        ctx.lineWidth = 2
        ctx.strokeRect(*overlay_bounds)
        ctx.strokeRect(
            overlay_bounds.left + 3, overlay_bounds.top + 3, overlay_bounds.width - 6, overlay_bounds.height - 6
        )

        font = self._prepare_font(ctx)

        # Draw streaming text
        lines = self.displayed_text.split("\n")
        line_height = font["size"] + 4
        
        if self.center:
            # Center both horizontally and vertically
            total_text_height = len(lines) * line_height
            start_y = overlay_bounds.top + (overlay_bounds.height - total_text_height) / 2 + font["size"]
            start_x = (window.canvas.width - self._text_width) / 2 
        else:
            start_y = overlay_bounds.top + font["size"] + 10  # use overlay_bounds.top
            start_x = overlay_bounds.left + 10 

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            if y_pos < overlay_bounds.bottom - 10:       # don't draw outside overlay
                ctx.fillText(line, start_x, y_pos)
        
        # Draw hint if any at bottom left
        if self.hint:
            ctx.fillText(self.hint, overlay_bounds.left + 10, overlay_bounds.bottom - 10)

        button_bounds = self.render_and_handle_button(ctx, overlay_bounds)
        if window.controls.click:
            # log.debug(self.button_click_callable)
            # log.debug(self.other_click_callable)
            # if a click occurred and we don't have a button or we clicked outside the button
            if button_bounds is None or not button_bounds.contains(window.controls.mouse.click):
                if self.other_click_callable is not None:
                    self.other_click_callable()
            # otherwise, button was clicked
            elif self.button_click_callable is not None:
                self.button_click_callable()


class ResultsScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        self.planet_data = window.get_planet(planet.name)
        text = self.planet_data.info if self.planet_data else ""
        super().__init__(name, scene_manager, text)
        # default sizing for scan results screen
        self.margins = Position(200, 50)
        
class DeathScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager, "GAME OVER", color="rgba(0, 255, 0, 0.9)")
        # Center the death screen
        self.margins = Position(150, 150)
        self.center = True
        self.muted = True  # This only refers to text terminal sound, not audio in general
        self.bold = True
    
    def calculate_and_set_font(self) -> str:
        base_size = min(window.canvas.width, window.canvas.height) / 15
        font_size = max(32, min(72, base_size))  # Scale between 32px and 72px
        self.font = {"size": font_size, "font": "'Courier New', monospace"}
        return self.font
    
    def render(self, ctx: CanvasRenderingContext2D, timestamp):
        window.audio_handler.play_music_death()
        super().render(ctx, timestamp)


class Dialogue(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, text: str):
        # Initialize the first line using the TextOverlay constructor
        lines = text.split("\n")
        first_line = lines[0] if lines else ""
        super().__init__(name, scene_manager, first_line)

        # Store all lines and keep track of current index
        self.lines = lines
        self.current_index = 0
        self.swap_color = False
        self.is_col1 = False
        self.switch_color()
        self.done = False
        
    def next(self):
        """Advance to the next line of dialogue."""
        self.current_index += 1
        if self.current_index < len(self.lines):
            self.switch_color()    
            # Use the TextOverlay method to set the next line
            self.set_text(self.lines[self.current_index].strip())
            self.active = True
        else:
            # No more lines
            self.done = True
            self.deactivate()

    def render(self, ctx: CanvasRenderingContext2D, timestamp):
        """Render the currently active line."""

        message_parts = self.lines[self.current_index].strip().split(' ')
        split_message = []
        len_text_line = 0
        partial_message = ''
    
        for part in message_parts:
            word_width = ctx.measureText(part + ' ').width  # include space
            if len_text_line + word_width <= self.rect[2]:
                partial_message += part + ' '
                len_text_line += word_width
            else:
                # save current line before adding the new word
                split_message.append(partial_message.rstrip())
                # start new line with current word
                partial_message = part + ' '
                len_text_line = word_width

        if partial_message:
            split_message.append(partial_message.rstrip())

        formatted_message = ''
        for part in split_message:
            formatted_message += part + '\n'
        self.text = formatted_message

        super().render(ctx, timestamp)
        
    def switch_color(self):
        self.is_col1 = not self.is_col1
        if self.is_col1:
            self.color = "rgba(0, 255, 0, 0.8)"  
        else:
            self.color = "rgba(170, 255, 0, 0.8)" 

class Credits:
    """Simple scrolling credits"""
    def __init__(self, credits_text: str, fill_color: str):
        self.credits_lines = credits_text.split("\n") if credits_text else ["No credits available"]
        self.scroll_speed = 0.4  # pixels per frame
        self.y_offset = window.canvas.height  * 0.7  # Start near bottom of screen
        self.line_height = 30
        self.fill_color = fill_color
        self.finished = False
        
    def update(self, timestamp):
        """Update the scroll position."""
        self.y_offset -= self.scroll_speed
        
        # Check if credits have finished scrolling
        if not self.finished:
            last_line_y = self.y_offset + (len(self.credits_lines) * self.line_height)
            # log.debug("Credits Last Line Y Offset: %s", last_line_y)
            if last_line_y < 0:
                self.finished = True
        
    def render(self, ctx, timestamp):
        """Render the scrolling credits."""
        if self.finished:
            return
        
        ctx.save()
        ctx.font = f"18px Courier New"
        ctx.fillStyle = self.fill_color
        ctx.textAlign = "center"
        
        # Draw each line of credits
        for i, line in enumerate(self.credits_lines):
            y_pos = self.y_offset + (i * self.line_height)
            # Only render if the line is visible on screen
            if -self.line_height <= y_pos <= window.canvas.height + self.line_height:
                ctx.fillText(line, window.canvas.width / 2, y_pos)
        
        ctx.restore()

