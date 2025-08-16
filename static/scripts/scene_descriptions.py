from consolelogger import getLogger
from common import PlanetState
from solar_system import SolarSystem
from spacemass import SpaceMass
from stars import StarSystem
from js import window  # type: ignore[attr-defined]
from sprites import SpriteSheet

from scene_classes import CanvasRenderingContext2D, Scene, SceneManager

log = getLogger(__name__, False)
sprites = window.sprites

# --------------------
# methods that may be useful across various scenes
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
                planet.switch_view()
                self.scene_manager.activate_scene(f"{planet.name}-planet-scene")
                get_player().reset_position()
                get_player().active = True
                get_asteroid_system().reset()
                get_debris_system().reset()


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
        self.results = ResultsScreen(name=f"{planet.name}-results", scene_manager=scene_manager, planet=self.planet)

    def should_exit_scene(self) -> bool:
        # TODO temporary debug / demo function: click goes back to the OrbitingPlanets scene
        if get_controls().click:  # and self.planet.complete: , commented out for quick switch
            return True
        return False

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

        # Handle scene completion
        if get_scanner().finished:
            self.handle_scene_completion(timestamp)

        if self.results.active:
            self.results.render(ctx, timestamp)
        if self.should_exit_scene():
            get_scanner().reset()
            self.planet.switch_view()
            self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

        log.debug(self.planet.complete)

    def handle_scene_completion(self, timestamp):
        """Handle when the scanning is finished and planet is complete."""
        get_player().active = False
        self.results.active = True
        self.planet.complete = True


class ResultsScreen(Scene):
    def __init__(self, name: str, scene_manager: SceneManager, planet: SpaceMass):
        super().__init__(name, scene_manager)
        default = "No information found :("
        self.scene_manager = scene_manager
        self.planet_data = get_planet(planet.name)
        self.text = self.planet_data.get("info", default) if self.planet_data else default
        self.displayed_text = ""
        self.char_index = 0
        self.last_char_time = 0
        self.char_delay = 10  # milliseconds between characters
        self.active = False

    def render(self, ctx: CanvasRenderingContext2D, timestamp):
        if not self.active or not self.text:
            return

        # Update streaming text
        if timestamp - self.last_char_time > self.char_delay and self.char_index < len(self.text):
            chars_to_add = min(3, len(self.text) - self.char_index)
            self.displayed_text += self.text[self.char_index : self.char_index + chars_to_add]
            self.char_index += chars_to_add
            self.last_char_time = timestamp

        # Draw transparent console background
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)"
        px = 200
        py = 50
        ctx.fillRect(px, py, window.canvas.width - 2 * px, window.canvas.height - 2 * py)

        # Draw console border
        ctx.strokeStyle = "rgba(0, 255, 0, 0.8)"
        ctx.lineWidth = 2
        ctx.strokeRect(px, py, window.canvas.width - 2 * px, window.canvas.height - 2 * py)

        # Set text style based on window size
        base_size = min(window.canvas.width, window.canvas.height) / 50
        font_size = max(12, min(20, base_size))  # Scale between 12px and 20px
        ctx.fillStyle = "#00ff00"
        ctx.font = f"{font_size}px 'Courier New', monospace"

        # Draw streaming text
        lines = self.displayed_text.split("\n")
        line_height = font_size + 4
        start_y = py + font_size + 10

        for i, line in enumerate(lines):
            y_pos = start_y + i * line_height
            if y_pos < window.canvas.height - py - 20:  # Don't draw outside bounds
                ctx.fillText(line, px + 20, y_pos)


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
    manager.add_scene(orbiting_planets_scene)

    for planet in solar_system.planets:
        big_planet_scene = PlanetScene(f"{planet.name}-planet-scene", manager, planet)
        manager.add_scene(big_planet_scene)

    manager.activate_scene(ORBITING_PLANETS_SCENE)  # initial scene
    return manager
