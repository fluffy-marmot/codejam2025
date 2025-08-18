from functools import partial
import math
import re
import textwrap

from player import Player
from common import PlanetState, Position, Rect
from consolelogger import getLogger
from scene_classes import CanvasRenderingContext2D, Scene, SceneManager
from solar_system import SolarSystem
from spacemass import SpaceMass
from stars import StarSystem, StarSystem3d
from window import window
from js import document #type:ignore
canvas = document.getElementById("gameCanvas")
container = document.getElementById("canvasContainer")
SCREEN_W, SCREEN_H = container.clientWidth, container.clientHeight
log = getLogger(__name__, False)

# --------------------
# methods useful across various scenes
# --------------------


def get_controls():
    return window.controls


def get_player():
    return window.player


def get_asteroid_system():
    return window.asteroids


def get_debris_system():
    return window.debris


def get_scanner():
    return window.scanner


def draw_black_background(ctx):
    ctx.fillStyle = "black"
    ctx.fillRect(0, 0, window.canvas.width, window.canvas.height)

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


# --------------------
# our main scene with the planets orbiting the sun
# --------------------

ORBITING_PLANETS_SCENE = "orbiting-planets-scene"
FINAL_SCENE = "final-scene"


class OrbitingPlanetsScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager, solar_system: SolarSystem):
        super().__init__(name, scene_manager)

        self.solar_sys = solar_system

        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=3,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )
        self.planet_info_overlay = TextOverlay("planet-info-overlay", scene_manager, "")
        # attach a behavior to click event outside the overlay's button - hide the overlay
        self.planet_info_overlay.other_click_callable = self.planet_info_overlay.deactivate
        self.planet_info_overlay.set_button("Travel")
        self.planet_info_overlay.muted = False
        self.planet_info_overlay.center = True
        self.scene_manager = scene_manager
        # Debug button label
        self._debug_btn_label = "Complete All"

    def render(self, ctx, timestamp):
        window.audio_handler.play_music_main()

        draw_black_background(ctx)
        self.highlight_hovered_planet()

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

        # If all planets are complete, switch to the final scene
        if all(p.complete for p in self.solar_sys.planets):
            self.scene_manager.activate_scene(FINAL_SCENE)
            return

        # from this scene, be ready to switch to a big planet scene if planet is clicked
        if self.planet_info_overlay.active:
            self.planet_info_overlay.render(ctx, timestamp)
        else:
            self.check_planet_click()

        # Debug: button to set all planets to complete
        self._render_debug_complete_all_button(ctx)

    def _render_debug_complete_all_button(self, ctx):
        label = self._debug_btn_label
        ctx.save()
        ctx.font = "14px Courier New"
        text_width = ctx.measureText(label).width
        pad_x, pad_y = 10, 8
        x, y = 16, 16
        w, h = text_width + pad_x * 2, 30
        bounds = Rect(x, y, w, h)

        # Background
        ctx.fillStyle = "rgba(0, 0, 0, 0.75)"
        ctx.fillRect(*bounds)

        # Hover state
        is_hover = bounds.contains(get_controls().mouse.move)
        ctx.strokeStyle = "#ffff00" if is_hover else "#00ff00"
        ctx.lineWidth = 2
        ctx.strokeRect(*bounds)
        ctx.fillStyle = ctx.strokeStyle
        ctx.fillText(label, x + pad_x, y + h - 10)

        # Click handling
        if get_controls().click and bounds.contains(get_controls().mouse.click):
            for p in self.solar_sys.planets:
                p.complete = True
            log.debug("Debug: set all planet completions to True")
        ctx.restore()

    def check_planet_click(self):
        planet = self.solar_sys.get_object_at_position(get_controls().mouse.click)
        if get_controls().click and planet:
            planet_data = window.get_planet(planet.name)
            log.debug("Clicked on: %s", planet.name)
            if planet.complete:
                self.planet_info_overlay.set_button(None)
                self.planet_info_overlay.set_text(planet_data.info)
                self.planet_info_overlay.margins = Position(200, 50)
                self.planet_info_overlay.active = True
                self.planet_info_overlay.center = True
            else:
                self.planet_info_overlay.set_button("Travel")
                self.planet_info_overlay.button_click_callable = partial(self.switch_planet_scene, planet.name)
                self.planet_info_overlay.set_text("\n".join(planet_data.level))
                self.planet_info_overlay.margins = Position(300, 120)
                self.planet_info_overlay.active = True
                self.planet_info_overlay.center = False

    def highlight_hovered_planet(self):
        # Reset all planets' highlight state first
        for planet in self.solar_sys.planets:
            planet.highlighted = False

        planet = self.solar_sys.get_object_at_position(get_controls().mouse.move)
        if planet is not None and not self.planet_info_overlay.active:
            planet.highlighted = True

    def switch_planet_scene(self, planet_name):
        planet_scene_name = f"{planet_name}-planet-scene"
        log.debug("Activating planet scene: %s", planet_scene_name)

        planet = window.get_planet(planet_name)
        if planet is None:
            log.error("Planet not found: %s", planet_name)
            return

        log.debug(planet)
        self.planet_info_overlay.deactivate()
        self.scene_manager.activate_scene(planet_scene_name)
        self.solar_sys.get_planet(planet_name).switch_view()
        get_player().reset_position()
        get_player().active = True
        get_asteroid_system().reset(planet)
        get_debris_system().reset()
        get_scanner().set_scan_parameters(planet.scan_multiplier)
        get_scanner().reset()


# --------------------
# game scene with zoomed in planet on left
# --------------------


class PlanetScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        super().__init__(name, scene_manager)

        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=3,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )
        self.planet = planet
        planet.set_position(0, window.canvas.height // 2)
        self.results_overlay = ResultsScreen(f"{planet.name}-results", scene_manager, self.planet)
        self.results_overlay.other_click_callable = self.handle_scene_completion
        self.results_overlay.muted = False
        self.results_overlay.center = True
        
        # Add death screen
        self.death_screen = DeathScreen(f"{planet.name}-death", scene_manager)
        self.death_screen.button_click_callable = self.handle_player_death
        self.death_screen.set_button("Play Again")
        self.death_sound_played = False  # Track if death sound has been played
        
        # Add explosion animation
        self.player_explosion = PlayerExplosion()
        self.explosion_started = False

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.stars.star_shift(timestamp, 5)
        self.stars.render(ctx, timestamp)
        get_scanner().update(ctx, timestamp)
        get_scanner().render_beam(ctx)
        self.planet.render(ctx, timestamp)

        # Update + render handles spawn and drawing
        get_asteroid_system().update_and_render(ctx, timestamp)
        self.check_special_level_interactions(timestamp)
        
        # Check for player death first
        if get_player().health <= 0:
            if not self.explosion_started:
                # Start explosion animation at player position
                player_x, player_y = get_player().get_position()
                self.player_explosion.start_explosion(player_x, player_y)
                self.explosion_started = True
                get_player().invincible = True
            
            # Render explosion instead of player
            if self.player_explosion.active:
                self.player_explosion.render(ctx, timestamp)
            # Only show death screen after explosion is finished
            elif self.player_explosion.finished:
                if not self.death_sound_played:
                    window.audio_handler.play_death()
                    self.death_sound_played = True
                self.death_screen.active = True
        else:
            # Normal player rendering when alive
            get_player().render(ctx, timestamp)
        
        get_debris_system().update()
        get_debris_system().render(ctx, timestamp)

        get_scanner().render(ctx, timestamp)

        # Activate the results sub-scene if scanner progress is complete
        if get_scanner().finished:
            self.results_overlay.active = True
            get_player().invincible = True
        elif get_player().health > 0:  # Only reset invincibility if player is alive
            get_player().invincible = False

        # Handle death screen display and interaction
        if self.death_screen.active:
            self.death_screen.render(ctx, timestamp)
        # Handle results screen display and interaction
        self.results_overlay.render(ctx, timestamp)
    
    def check_special_level_interactions(self, timestamp: int):
        """
        Handle special level interactions

        This is probably not best place to handle the special level stuff like Jupiter gravity affecting
        player and Mercury slowly damaging player, but it's crunch time so whatever works :)
        """
        # nudge player in the direction of jupiter if on the left 2/3 of the screen
        if self.planet.name.lower() == "jupiter":
            get_player().nudge_towards(self.planet.get_position(), 0.6)
        elif self.planet.name.lower() == "mercury":
            get_player().health = max(0, get_player().health - (timestamp - self.last_timestamp) / 1_200_000)

    def handle_scene_completion(self):
        """Handle when the scanning is finished and planet is complete."""
        log.debug(f"Finished planet {self.planet.name}! Reactivating orbiting planets scene.")
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)
        get_player().active = False
        self.results_overlay.active = True
        self.planet.switch_view()
        self.planet.complete = True

    def handle_player_death(self):
        """Handle when the player dies and clicks on the death screen."""
        log.debug(f"Player died on {self.planet.name}! Returning to orbiting planets scene.")
        
        # Reset all planet completions when player dies
        orbiting_scene = next(scene for scene in self.scene_manager._scenes if scene.name == ORBITING_PLANETS_SCENE)
        for planet in orbiting_scene.solar_sys.planets:
            planet.complete = False
        log.debug("All planet completions reset due to player death")
        
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)
        get_player().active = False
        get_player().health = 1000  # Reset player health to FULL_HEALTH
        self.death_screen.deactivate()
        self.death_sound_played = False  # Reset for next time
        self.explosion_started = False  # Reset explosion state
        self.planet.switch_view()

        # special level interaction: finishing earth gives player full health back
        if self.planet.name.lower() == "earth":
            get_player().health = Player.FULL_HEALTH


# --------------------
# text overlay scenes, such as scan results display
# --------------------

class StartScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager, bobbing_timer = 135, bobbing_max = 20):
        super().__init__(name, scene_manager)
        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=1,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )
        #self.player = get_player()
        
        dialogue = """Alien 1: Why does boss need so much planet data..?
        Alien 2: I dont know man
        Alien 1: Soosh is goated
        """
        
        self.dialogue_manager = Dialogue('dialogue', scene_manager, dialogue)
        self.dialogue_manager.active = True
        self.dialogue_manager.margins = Position(300, 150)
        self.starsystem = StarSystem3d(100, max_depth=100)
        self.player = None
        self.bobbing_timer = bobbing_timer
        self.bobbing_max = bobbing_max
        self.is_bobbing_up = True
        self.bobbing_offset = 0
        self.animation_timer = 0
    def render(self, ctx, timestamp):
        if self.player is None:
            player = get_player()
            player.is_disabled = True
        
        if timestamp - self.animation_timer >= self.bobbing_timer:
            print(f"bobbing, val={self.bobbing_offset}")
            self.animation_timer = timestamp
            if self.is_bobbing_up:
                self.bobbing_offset += 1
            else:
                self.bobbing_offset -= 1

            player.y = (SCREEN_H//2 + self.bobbing_offset)

            if abs(self.bobbing_offset) > self.bobbing_max:
                self.is_bobbing_up = not self.is_bobbing_up
            
                
        draw_black_background(ctx)
        #self.stars.render(ctx, timestamp)
        self.dialogue_manager.render(ctx, timestamp)
        self.dialogue_manager.rect=(0, SCREEN_H-150, SCREEN_W, 150)  # x, y, width, height
        self.starsystem.render(ctx, speed=0.3, scale=70)
        player.render(ctx, timestamp)
        if get_controls().click:
            self.dialogue_manager.next()
        
        if self.dialogue_manager.done:
            self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

class TextOverlay(Scene):
    DEFAULT = "No information found :("

    def __init__(self, name: str, scene_manager: SceneManager, text: str, color="rgba(0, 255, 0, 0.8)", rect=None):
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
        if button_bounds.contains(get_controls().mouse.move):
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

        button_bounds = self.render_and_handle_button(ctx, overlay_bounds)
        if get_controls().click:
            # log.debug(self.button_click_callable)
            # log.debug(self.other_click_callable)
            # if a click occurred and we don't have a button or we clicked outside the button
            if button_bounds is None or not button_bounds.contains(get_controls().mouse.click):
                if self.other_click_callable is not None:
                    self.other_click_callable()
            # otherwise, button was clicked
            elif self.button_click_callable is not None:
                self.button_click_callable()


class ResultsScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        self.planet_data = window.get_planet(planet.name)
        text = self.planet_data.info if self.planet_data else TextOverlay.DEFAULT
        super().__init__(name, scene_manager, text)
        # default sizing for scan results screen
        self.margins = Position(200, 50)

class DeathScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager, "YOU DIED", color="rgba(0, 255, 0, 0.9)")
        # Center the death screen
        self.margins = Position(150, 150)
        self.center = True
        self.muted = False  # Play sound when death screen appears
        self.bold = True
    
    def calculate_and_set_font(self) -> str:
        base_size = min(window.canvas.width, window.canvas.height) / 15
        font_size = max(32, min(72, base_size))  # Scale between 32px and 72px
        self.font = {"size": font_size, "font": "'Courier New', monospace"}
        return self.font

class PlayerExplosion:
    def __init__(self):
        self.explosion_sprite = window.get_sprite("Explosion Animation")
        self.active = False
        self.current_frame = 0
        self.frame_count = 11  # Number of frames
        self.frame_duration = 100  # milliseconds per frame
        self.last_frame_time = 0
        self.position = (0, 0)
        self.scale = 4.0
        self.finished = False
    
    def start_explosion(self, x: float, y: float):
        """Start the explosion animation at the given position"""
        self.active = True
        self.current_frame = 0
        self.position = (x, y)
        self.last_frame_time = 0
        self.finished = False
    
    def update(self, timestamp: float):
        """Update the explosion animation"""
        if not self.active or self.finished:
            return
        
        if timestamp - self.last_frame_time >= self.frame_duration:
            self.current_frame += 1
            self.last_frame_time = timestamp
            
            if self.current_frame >= self.frame_count:
                self.finished = True
                self.active = False
    
    def render(self, ctx, timestamp: float):
        """Render the current explosion frame"""
        if not self.active or self.finished:
            return
        
        self.update(timestamp)
        
        frame_width = self.explosion_sprite.width // self.frame_count
        frame_height = self.explosion_sprite.height
        
        source_x = self.current_frame * frame_width
        source_y = 0
        
        scaled_width = frame_width * self.scale
        scaled_height = frame_height * self.scale
        
        ctx.drawImage(
            self.explosion_sprite.image,
            source_x, source_y, frame_width, frame_height,  # source rectangle
            self.position[0] - scaled_width/2, self.position[1] - scaled_height/2,  # destination position
            scaled_width, scaled_height  # destination size
        )

class FinalScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager)
        # Sparse stars for space backdrop
        self.stars = StarSystem(
            num_stars=80,
            radius_min=1,
            radius_max=2,
            pulse_freq_min=10,
            pulse_freq_max=50,
        )
        # Rotating Earth spritesheet
        self.earth_sprite = window.get_sprite("earth")
        self.earth_frame = 0
        self.earth_frame_duration = 200
        self.earth_last_frame_time = 0
        
        # Moon sprite for lunar surface
        try:
            self.moon_sprite = window.get_sprite("moon")
        except Exception:
            self.moon_sprite = None

    def _draw_earth(self, ctx, timestamp):
        # Advance frame based on time
        if self.earth_sprite and self.earth_sprite.is_loaded:
            if self.earth_last_frame_time == 0:
                self.earth_last_frame_time = timestamp
            if timestamp - self.earth_last_frame_time >= self.earth_frame_duration:
                self.earth_frame = (self.earth_frame + 1) % max(1, self.earth_sprite.num_frames)
                self.earth_last_frame_time = timestamp

            frame_size = self.earth_sprite.frame_size if self.earth_sprite.num_frames > 1 else self.earth_sprite.height
            sx = (self.earth_frame % max(1, self.earth_sprite.num_frames)) * frame_size
            sy = 0

            # Position Earth in upper-right, smaller size like the reference image
            target_size = int(min(SCREEN_W, SCREEN_H) * 0.15)
            dw = dh = target_size
            dx = SCREEN_W * 0.65  # Right side of screen
            dy = SCREEN_H * 0.15  # Upper portion

            ctx.drawImage(
                self.earth_sprite.image,
                sx, sy, frame_size, frame_size,
                dx, dy, dw, dh
            )

    def _draw_lunar_surface(self, ctx):
        # Draw lunar surface with the top portion visible, like looking across the lunar terrain
        if self.moon_sprite and getattr(self.moon_sprite, "is_loaded", False):
            # Position moon sprite so its upper portion is visible as foreground terrain
            surface_height = SCREEN_H * 0.5
            
            # Scale to fill screen width
            scale = (SCREEN_W / self.moon_sprite.width)
            sprite_scaled_height = self.moon_sprite.height * scale
            
            # Position so the moon extends below the screen, showing only the top portion
            dy = SCREEN_H - surface_height
            
            ctx.drawImage(
                self.moon_sprite.image,
                0, 0, self.moon_sprite.width, self.moon_sprite.height,
                SCREEN_W - (SCREEN_W * scale)/1.25, dy, SCREEN_W * scale, sprite_scaled_height
            )

    def render(self, ctx, timestamp):
        # Deep space black background
        ctx.fillStyle = "#000000"
        ctx.fillRect(0, 0, SCREEN_W, SCREEN_H)
        
        # Sparse stars
        self.stars.render(ctx, timestamp)

        # Draw lunar surface first
        self._draw_lunar_surface(ctx)
        
        # Draw Earth in the distance
        self._draw_earth(ctx, timestamp)

        # Mission complete text
        ctx.save()
        ctx.font = f"bold {max(18, int(min(SCREEN_W, SCREEN_H) * 0.04))}px Courier New"
        ctx.fillStyle = "#00FF00"
        message = "Mission Complete"
        tw = ctx.measureText(message).width
        # Position text in the left side
        ctx.fillText(message, SCREEN_W * 0.05, SCREEN_H * 0.15)
        ctx.restore()

class Dialogue(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, text: str):
        # Initialize the first line using the TextOverlay constructor
        lines = text.split("\n")
        first_line = lines[0] if lines else TextOverlay.DEFAULT
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
        if self.current_index < len(self.lines) - 1:
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
        # PLEASE USE LOG INSTEAD OF PRINT
        # if self.active:
        #     print("rendering")
    
        # else:
        #     print("wtf")
    
        
        super().render(ctx, timestamp)

    def switch_color(self):
        self.is_col1 = not self.is_col1
        if self.is_col1:
            self.color = "rgba(255, 0, 0, 0.8)"  
        else:
            self.color = "rgba(0, 0, 255, 0.8)" 

# --------------------
# create scene manager
# --------------------

def create_scene_manager() -> SceneManager:
    """
    Create all the scenes and add them to a scene manager that can be used to switch between them
    """
    manager = SceneManager()
    planet_scene_state = PlanetState(0, window.canvas.height, 120.0, x=0, y=window.canvas.height // 2)
    solar_system = SolarSystem([window.canvas.width, window.canvas.height], planet_scene_state=planet_scene_state)
    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager, solar_system)
    start_scene = StartScene("start", manager)
    manager.add_scene(start_scene)
    manager.add_scene(orbiting_planets_scene)
    # Final victory scene (activated when all planets complete)
    final_scene = FinalScene(FINAL_SCENE, manager)
    manager.add_scene(final_scene)

    for planet in solar_system.planets:
        big_planet_scene = PlanetScene(f"{planet.name}-planet-scene", manager, planet)
        manager.add_scene(big_planet_scene)

    manager.activate_scene("start")  # initial scene
    return manager
