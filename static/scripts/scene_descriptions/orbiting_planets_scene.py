"""
OrbitingPlanetsScene - The main menu scene where planets orbit around the sun.
"""

from functools import partial
from consolelogger import getLogger
from scene_classes import Scene, SceneManager
from solar_system import SolarSystem
from stars import StarSystem
from common import Position, Rect
from overlay import TextOverlay
from window import window
from .scene_common import *

log = getLogger(__name__, False)


class OrbitingPlanetsScene(Scene):
    """
    Scene that handles the functionality of the part of the game where planets are orbiting around the sun
    and the player can select a level by clicking planets
    """

    def __init__(self, name: str, scene_manager: SceneManager, solar_system: SolarSystem):
        super().__init__(name, scene_manager)

        self.solar_sys = solar_system

        self.stars = StarSystem(
            num_stars=400,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=2,
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
        self._debug_btn_label = "" # disable the extra button by default

        self.show_cheats_menu()

    # just a temporary function for demo-ing project
    def show_cheats_menu(self):
        cheats_info = """
Hello, thanks for checking out our project!
In order to more easily demo the functionality 
of different parts of the game, we have included
the following cheats:

In planet overview screen:
[C] - Instantly jump to credits / victory screen

During ship flight:
[C] - Toggle collision boxes (for fun)
[K] - Kill the player (can start a new game)
[F] - Finish the current planet scan
"""
        self.planet_info_overlay.set_button(None)
        self.planet_info_overlay.set_text(cheats_info)
        self.planet_info_overlay.margins = Position(300, 150)
        self.planet_info_overlay.active = True
        self.planet_info_overlay.center = False

    def render(self, ctx, timestamp):

        # some temporary functionality for testing
        if "c" in window.controls.pressed:
            self.scene_manager.activate_scene(FINAL_SCENE)
        window.audio_handler.play_music_main()

        draw_black_background(ctx)
        self.highlight_hovered_planet()

        self.stars.render(ctx, timestamp)
        self.solar_sys.update_orbits(0.20)
        self.solar_sys.render(ctx, timestamp)

        # If all planets are complete, switch to the final scene
        if all(p.complete for p in self.solar_sys.planets):
            self.scene_manager.activate_scene(FINAL_SCENE)
            self._debug_btn_label = "View Credits Again"
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
        if not label: return
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
        if window.controls.click and bounds.contains(window.controls.mouse.click):
            for p in self.solar_sys.planets:
                p.complete = True
            log.debug("Debug: set all planet completions to True")
        ctx.restore()

    def check_planet_click(self):
        """Check whether a UI action needs to occur due to a click event."""

        planet = self.solar_sys.get_object_at_position(window.controls.mouse.click)
        if window.controls.click and planet:
            planet_data = window.get_planet(planet.name)
            log.debug("Clicked on: %s", planet.name)
            self.planet_info_overlay.hint = "Click anywhere to close"
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

        planet = self.solar_sys.get_object_at_position(window.controls.mouse.move)
        if planet is not None and not self.planet_info_overlay.active:
            planet.highlighted = True

    def switch_planet_scene(self, planet_name):
        """Prepare what is needed to transition to a gameplay scene."""

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
