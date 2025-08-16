from js import document, window  # type: ignore[attr-defined]

from consolelogger import getLogger
from scene_classes import Scene, SceneObject, SceneManager, CanvasRenderingContext2D

from common import Position, Rect
from debris import DebrisSystem
from player import Player
from spacemass import SpaceMass
from solar_system import SolarSystem
from stars import StarSystem
from sprites import SpriteSheet

log = getLogger(__name__)
sprites = window.sprites

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

# --------------------
# our main scene with the planets orbiting the sun
# --------------------

ORBITING_PLANETS_SCENE = "orbiting-planets-scene"


class OrbitingPlanetsScene(Scene):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager)

        self.solar_sys = SolarSystem([window.canvas.width, window.canvas.height])

        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=3,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.highlight_hovered_planet()

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

        # from this scene, be ready to switch to a big planet scene if planet is clicked
        self.switch_planet_scene()

    def highlight_hovered_planet(self):
        # Reset all planets' highlight state first
        for planet in self.solar_sys.planets:
            planet.highlighted = False

        planet = self.solar_sys.get_object_at_position(get_controls().mouse.move)
        if planet is not None:
            log.debug("Highlighting planet: %s", planet.name)
            planet.highlighted = True

    def switch_planet_scene(self):
        """Switch to the clicked planet scene if a planet is clicked."""
        if get_controls().click:
            planet = self.solar_sys.get_object_at_position(get_controls().mouse.click)
            if planet:
                log.debug("Clicked on: %s", planet.name)
                self.scene_manager.activate_scene(f"{planet.name}-planet-scene")
                get_player().reset_position()
                get_player().active = True
                get_asteroid_system().reset()
                get_debris_system().reset()

# --------------------
# game scene with zoomed in planet on left
# --------------------

class PlanetScene(Scene):
    def __init__(
        self,
        name: str,
        scene_manager: SceneManager,
        planet: SpaceMass,
    ):
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
        self.results = ResultsScreen(name=f"{planet.name}-results", scene_manager=scene_manager, planet=self.planet)
    
    def should_exit_scene(self) -> bool:
        # TODO temporary debug / demo function: click goes back to the OrbitingPlanets scene
        if get_controls().click:
            return True
        return False

    def render(self, ctx, timestamp):
        draw_black_background(ctx)
        self.stars.star_shift(timestamp, 5)
        self.stars.render(ctx, timestamp)
        if get_scanner().scanning:
            get_scanner().render_beam(ctx)
        self.planet.render(ctx, timestamp)

        # Update + render handles spawn and drawing
        get_asteroid_system().update_and_render(ctx, timestamp)
        get_player().render(ctx, timestamp)
        get_debris_system().update()
        get_debris_system().render(ctx, timestamp)

        get_scanner().render(ctx, timestamp)

        # Handle scene completion
        if get_scanner().finished:
            self.handle_scene_completion(timestamp)

        # Handle results screen display and interaction
        self.results.render(ctx, timestamp)
        if self.should_exit_scene():
            self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

        log.debug(self.planet.complete)

    def handle_scene_completion(self, timestamp):
        """Handle when the scanning is finished and planet is complete."""
        log.debug("done!")
        get_scanner().finished = False
        get_scanner().reset_bar()
        get_player().active = False
        self.results.active = True
        self.planet.complete = True

# --------------------
# text overlay scenes, such as scan results display
# --------------------

class TextOverlay(Scene):

    DEFAULT = "No information found :("

    def __init__(self, name: str, scene_manager: SceneManager, text: str):
        super().__init__(name, scene_manager)
        self.set_text(text)
        self.char_delay = 10  # milliseconds between characters
        self.active = False
        self.margins = Position(200, 50)
        self.button_label = None

    def set_text(self, text: str):
        """ """
        self.displayed_text = ""
        self.text = text
        self.char_index = 0
        self.last_char_time = 0

    def set_button(self, button_label: str | None):
        self.button_label = button_label

    def update_textstream(self, timestamp):
        """ Update streaming text """ 
        if timestamp - self.last_char_time > self.char_delay and self.char_index < len(self.text):
            chars_to_add = min(3, len(self.text) - self.char_index)
            self.displayed_text += self.text[self.char_index:self.char_index + chars_to_add]
            self.char_index += chars_to_add
            self.last_char_time = timestamp

    def render_and_handle_button(self, ctx: CanvasRenderingContext2D, overlay_bounds: Rect):
        if not self.button_label: return

        ctx.save()
        ctx.font = "14px Courier New"
        text_width = ctx.measureText(self.button_label).width

        button_rect = Rect(overlay_bounds.right - (text_width + 20), 
                           overlay_bounds.bottom - 34, text_width + 10, 24 )
        
        ctx.fillstyle = "rgba(0, 0, 0, 0.95)"
        ctx.fillrect(*button_rect)

        # check whether mouse is currently moving over the button
        if button_rect.contains(get_controls().mouse.move):
            ctx.fillstyle = "ffff00"
            if get_controls().click:
                ... # handle button being clicked
        else:
            ctx.fillstyle = "00ff00"

        ctx.fillText(self.button_label, button_rect.left + 10, button_rect.bottom - 10)
        ctx.strokeStyle = "rgba(0, 255, 0, 0.95)"
        ctx.lineWidth = 2
        ctx.strokeRect(*button_rect)
        
        



        ctx.restore()



    def render(self, ctx: CanvasRenderingContext2D, timestamp):
        if not self.active or not self.text:
            return
            
        self.update_textstream(timestamp)

        overlay_width = window.canvas.width - 2 * self.margins.x
        overlay_height = window.canvas.height - 2 * self.margins.y
        overlay_bounds = Rect(self.margins.x, self.margins.y, overlay_width, overlay_height)
        
        # Draw transparent console background
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)"
        
        ctx.fillRect(*overlay_bounds)

        # Draw console border
        ctx.strokeStyle = "rgba(0, 255, 0, 0.8)"
        ctx.lineWidth = 2
        ctx.strokeRect(*overlay_bounds)
        
        # Set text style based on window size
        base_size = min(window.canvas.width, window.canvas.height) / 50
        font_size = max(12, min(20, base_size))  # Scale between 12px and 20px
        ctx.fillStyle = "#00ff00"
        ctx.font = f"{font_size}px 'Courier New', monospace"
        
        # Draw streaming text
        lines = self.displayed_text.split('\n')
        line_height = font_size + 4
        start_y = self.margins.y + font_size + 10
        
        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            if y_pos < window.canvas.height - self.margins.y - 20:  # Don't draw outside bounds
                ctx.fillText(line, self.margins.x + 20, y_pos)

        self.render_and_handle_button()


class ResultsScreen(TextOverlay):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        self.planet_data = get_planet(planet.name)
        text = get_planet(planet.name).get("info", TextOverlay.DEFAULT) if planet else TextOverlay.DEFAULT
        super().__init__(name, scene_manager, text)
        # default sizing for results screen
        self.margins = Position(200, 50)

# --------------------
# create scene manager
# --------------------

def create_scene_manager() -> SceneManager:
    """
    Create all the scenes and add them to a scene manager that can be used to switch between them
    """
    manager = SceneManager()

    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager)
    manager.add_scene(orbiting_planets_scene)

    for planet in "mercury venus earth mars jupiter saturn neptune uranus".split():
        spacemass = SpaceMass(SpriteSheet(planet), 0, window.canvas.height, 1.0)
        big_planet_scene = PlanetScene(f"{planet}-planet-scene", manager, spacemass)
        manager.add_scene(big_planet_scene)

    manager.activate_scene(ORBITING_PLANETS_SCENE)  # initial scene
    return manager
