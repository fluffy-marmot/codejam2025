from functools import partial

from common import Position, Rect, PlanetState
from consolelogger import getLogger
from scene_classes import CanvasRenderingContext2D, Scene, SceneManager
from solar_system import SolarSystem
from spacemass import SpaceMass
from stars import StarSystem
from window import window
from js import document #type:ignore
import textwrap
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

def get_planet(name: str) -> dict[str, str] | None:
    for planet in window.planets:
        if planet["name"] == name.title():
            return planet
    return None

def rgba_to_hex(rgba_str):
    """
    Convert "rgba(r, g, b, a)" to hex string "#RRGGBB".
    Alpha is ignored.
    """
    import re

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
        self.scene_manager = scene_manager

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.highlight_hovered_planet()

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

        # from this scene, be ready to switch to a big planet scene if planet is clicked
        if self.planet_info_overlay.active:
            self.planet_info_overlay.render(ctx, timestamp)
        else:
            self.check_planet_click()

    def check_planet_click(self):
        if get_controls().click:
            planet = self.solar_sys.get_object_at_position(get_controls().mouse.click)
            if not planet.complete:
                log.debug("Clicked on: %s", planet.name)
                self.planet_info_overlay.button_click_callable = partial(self.switch_planet_scene, planet.name)
                self.planet_info_overlay.set_text("\n".join(get_planet(planet.name)["level"]))
                self.planet_info_overlay.margins = Position(300, 150)
                self.planet_info_overlay.active = True
            else:
                log.debug("Clicked on: %s", planet.name)
                print("Clicked on: %s", planet.name)
                self.planet_info_overlay = ResultsScreen(f"{planet.name}-results", self.scene_manager, planet)
                self.planet_info_overlay.set_text("\n".join(get_planet(planet.name)["level"]))
                self.planet_info_overlay.margins = Position(300, 150)
                self.planet_info_overlay.active = True
            
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

        self.planet_info_overlay.deactivate()
        self.scene_manager.activate_scene(planet_scene_name)
        self.solar_sys.get_planet(planet_name).switch_view()
        get_player().reset_position()
        get_player().active = True
        get_asteroid_system().reset()
        get_debris_system().reset()   
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
        

    def render(self, ctx, timestamp):
        
        draw_black_background(ctx)
        self.stars.star_shift(timestamp, 5)
        self.stars.render(ctx, timestamp)
        get_scanner().update(ctx, timestamp)
        get_scanner().render_beam(ctx)
        self.planet.render(ctx, timestamp)

        # Update + render handles spawn and drawing
        get_asteroid_system().update_and_render(ctx, timestamp)
        get_player().render(ctx, timestamp)
        get_debris_system().update()
        get_debris_system().render(ctx, timestamp)

        get_scanner().render(ctx, timestamp)

        # Activate the results sub-scene if scanner progress is complete
        if get_scanner().finished:
            print("your done with this planet")
            self.results_overlay.active = True
            get_player().invincible = True
        else:
            get_player().invincible = False

        # Handle results screen display and interaction
        self.results_overlay.render(ctx, timestamp)

    def handle_scene_completion(self):
        """Handle when the scanning is finished and planet is complete."""
        log.debug(f"Finished planet {self.planet.name}! Reactivating orbiting planets scene.")
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)
        get_player().active = False
        self.results_overlay.active = True
        self.planet.switch_view()
        self.planet.complete = True


# --------------------
# text overlay scenes, such as scan results display
# --------------------

class StartScence(Scene):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager)
        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=1,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )
        #self.player = get_player()
        
        dialouge = """Alien 1: Why does boss need so much planet data..?
        Alien 2: I dont know man
        Alien 1: Soosh is goated
        """
        
        self.dialogue_manager = Dialogue('dialouge', scene_manager, dialouge)
        self.dialogue_manager.active = True
        self.dialogue_manager.margins = Position(300, 150)
        

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.stars.render(ctx, timestamp)
        self.dialogue_manager.render(ctx, timestamp)
        self.dialogue_manager.rect=(0, SCREEN_H-150, SCREEN_W, 150)  # x, y, width, height
        if get_controls().click:
            self.dialogue_manager.next()
        
        if self.dialogue_manager.done:
            self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

class TextOverlay(Scene):
    DEFAULT = "No information found :("

    def __init__(self, name: str, scene_manager: SceneManager, text: str, color="rgba(0, 255, 0, 0.8)", rect=None):
        super().__init__(name, scene_manager)
        self.set_text(text)
        self.calculate_and_set_font()
        self.char_delay = 10  # milliseconds between characters
        self.margins = Position(200, 50)
        self.button_label = None
        self.button_click_callable = None
        self.other_click_callable = None
        self.deactivate()
        self.color = color
        self.rect = rect # tuple: (x, y, width, height)
    def deactivate(self):
        self.active = False

    def set_text(self, text: str):
        """ """
        self.displayed_text = ""
        self.text = text
        self.char_index = 0
        self.last_char_time = 0

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
            chars_to_add = min(3, len(self.text) - self.char_index)
            self.displayed_text += self.text[self.char_index : self.char_index + chars_to_add]
            self.char_index += chars_to_add
            self.last_char_time = timestamp

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
            print("I have a rectangle")
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

        font = self.font or self.calculate_and_set_font()
        ctx.font = f"{font['size']}px {font['font']}"
        ctx.fillStyle = rgba_to_hex(self.color)

        # Draw streaming text
        lines = self.displayed_text.split("\n")
        line_height = font["size"] + 4
        start_y = overlay_bounds.top + font["size"] + 10  # use overlay_bounds.top
        start_x = overlay_bounds.left + 10               # use overlay_bounds.left

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            if y_pos < overlay_bounds.bottom - 10:       # don't draw outside overlay
                ctx.fillText(line, start_x, y_pos)

        button_bounds = self.render_and_handle_button(ctx, overlay_bounds)
        if get_controls().click:
            log.debug(self.button_click_callable)
            log.debug(self.other_click_callable)
            # if a click occurred and we don't have a button or we clicked outside the button
            if button_bounds is None or not button_bounds.contains(get_controls().mouse.click):
                if self.other_click_callable is not None:
                    self.other_click_callable()
            # otherwise, button was clicked
            elif self.button_click_callable is not None:
                self.button_click_callable()


class ResultsScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        self.planet_data = get_planet(planet.name)
        text = get_planet(planet.name).get("info", TextOverlay.DEFAULT) if planet else TextOverlay.DEFAULT
        super().__init__(name, scene_manager, text)
        # default sizing for results screen
        self.margins = Position(200, 50)

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
        if self.active:
            print("rendering")
    
        else:
            print("wtf")
    
        
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
    start_scene = StartScence("start", manager)
    manager.add_scene(start_scene)
    manager.add_scene(orbiting_planets_scene)

    for planet in solar_system.planets:
        big_planet_scene = PlanetScene(f"{planet.name}-planet-scene", manager, planet)
        manager.add_scene(big_planet_scene)

    manager.activate_scene("start")  # initial scene
    return manager
