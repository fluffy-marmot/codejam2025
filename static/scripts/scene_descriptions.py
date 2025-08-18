from functools import partial

from player import Player, PlayerExplosion
from common import PlanetState, Position, Rect
from consolelogger import getLogger
from scene_classes import Scene, SceneManager
from solar_system import SolarSystem
from spacemass import SpaceMass
from stars import StarSystem, StarSystem3d
from window import window
from overlay import TextOverlay, ResultsScreen, DeathScreen, Dialogue, Credits

from js import document #type:ignore
canvas = document.getElementById("gameCanvas")
container = document.getElementById("canvasContainer")
log = getLogger(__name__, False)

# --------------------
# methods useful across various scenes
# --------------------

ORBITING_PLANETS_SCENE = "orbiting-planets-scene"
FINAL_SCENE = "final-scene"
START_SCENE = "start-scene"

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

# --------------------
# our main scene with the planets orbiting the sun
# --------------------

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

# --------------------
# game scene with zoomed in planet on left
# --------------------

class PlanetScene(Scene):
    """
    Scene that handles the functionality of the part of the game where the player's ship is active and dodging
    asteroids. Also handles the scan results display as a child scene.
    """

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
        self.results_overlay.hint = "Click anywhere to continue"
        
        # Add death screen
        self.death_screen = DeathScreen(f"{planet.name}-death", scene_manager)
        self.death_screen.button_click_callable = self.handle_player_death
        self.death_screen.set_button("Play Again")
        
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
                window.audio_handler.play_explosion()
                # Start explosion animation at player position
                player_x, player_y = get_player().get_position()
                self.player_explosion.start_explosion(player_x, player_y)
                self.explosion_started = True
                get_player().invincible = True
                window.audio_handler.play_music_main(pause_it=True)
            
            # Render explosion instead of player
            if self.player_explosion.active:
                self.player_explosion.render(ctx, timestamp)
            # Only show death screen after explosion is finished
            elif self.player_explosion.finished:
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
            get_player().nudge_towards(self.planet.get_position(), 0.5)
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
        window.audio_handler.play_music_death(pause_it=True)        
        log.debug(f"Player died on {self.planet.name}! Returning to orbiting planets scene.")
        
        # Reset all planet completions when player dies
        orbiting_scene = next(scene for scene in self.scene_manager._scenes if scene.name == ORBITING_PLANETS_SCENE)
        for planet in orbiting_scene.solar_sys.planets:
            planet.complete = False
        log.debug("All planet completions reset due to player death")

        window.audio_handler.play_explosion(pause_it=True)     
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)
        get_player().active = False
        get_player().health = 1000  # Reset player health to FULL_HEALTH
        self.death_screen.deactivate()
        self.explosion_started = False  # Reset explosion state
        self.planet.switch_view()

        # special level interaction: finishing earth gives player full health back
        if self.planet.name.lower() == "earth":
            get_player().health = Player.FULL_HEALTH
        log.debug(window.audio_handler.music_death.paused)

# --------------------
# game intro scene with dialogue
# --------------------

class StartScene(Scene):
    """Scene for handling the alien dialogue for introducing the game."""

    def __init__(self, name: str, scene_manager: SceneManager, bobbing_timer = 135, bobbing_max = 20):
        super().__init__(name, scene_manager)
        self.stars = StarSystem(
            num_stars=100,  # as number of stars increase, the radius should decrease
            radius_min=1,
            radius_max=1,
            pulse_freq_min=3,
            pulse_freq_max=6,
        )

        self.dialogue_manager = Dialogue('dialogue', scene_manager, window.lore)
        self.dialogue_manager.active = True
        self.dialogue_manager.margins = Position(300, 150)
        self.dialogue_manager.rect=(0, window.canvas.height-150, window.canvas.width, 150)
        self.dialogue_manager.set_button("Skip Intro")
        self.dialogue_manager.button_click_callable = self.finalize_scene
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
            log.debug(f"bobbing, val={self.bobbing_offset}")
            self.animation_timer = timestamp
            if self.is_bobbing_up:
                self.bobbing_offset += 1
            else:
                self.bobbing_offset -= 1

            player.y = (window.canvas.height // 2 + self.bobbing_offset)

            if abs(self.bobbing_offset) > self.bobbing_max:
                self.is_bobbing_up = not self.is_bobbing_up
        
        draw_black_background(ctx)
        #self.stars.render(ctx, timestamp)
        self.dialogue_manager.render(ctx, timestamp)
       
        self.starsystem.render(ctx, speed=0.3, scale=70)
        player.render(ctx, timestamp)
        if window.controls.click:
            self.dialogue_manager.next()
            window.audio_handler.play_music_thematic()

        if self.dialogue_manager.done:
            self.finalize_scene()
    
    def finalize_scene(self):
        window.audio_handler.play_music_thematic(pause_it=True)
        window.audio_handler.play_music_main()
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

# --------------------
# final \ credits scene
# --------------------

class FinalScene(Scene):
    """Scene for the final credits."""
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__(name, scene_manager)
        # Sparse stars for space backdrop
        self.stars = StarSystem(
            num_stars=200,
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
        self.fill_color = "#00FF00"
        
        # Moon sprite for lunar surface
        try:
            self.moon_sprite = window.get_sprite("moon")
        except Exception:
            self.moon_sprite = None

        self.credits = Credits(window.credits, self.fill_color)

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
            target_size = int(min(window.canvas.width, window.canvas.height) * 0.15)
            dw = dh = target_size
            dx = window.canvas.width * 0.65  # Right side of screen
            dy = window.canvas.height * 0.15  # Upper portion

            ctx.drawImage(
                self.earth_sprite.image,
                sx, sy, frame_size, frame_size,
                dx, dy, dw, dh
            )

    def _draw_lunar_surface(self, ctx):
        # Draw lunar surface with the top portion visible, like looking across the lunar terrain
        if self.moon_sprite and getattr(self.moon_sprite, "is_loaded", False):
            # Position moon sprite so its upper portion is visible as foreground terrain
            surface_height = window.canvas.height * 0.5
            
            # Scale to fill screen width
            scale = (window.canvas.width / self.moon_sprite.width)
            sprite_scaled_height = self.moon_sprite.height * scale
            
            # Position so the moon extends below the screen, showing only the top portion
            dy = window.canvas.height - surface_height
            
            ctx.drawImage(
                self.moon_sprite.image,
                0, 0, self.moon_sprite.width, self.moon_sprite.height,
                window.canvas.width - (window.canvas.width * scale)/1.25, dy,   # target left, top
                window.canvas.width * scale, sprite_scaled_height               # target width, height
            )

    def render(self, ctx, timestamp):
        window.audio_handler.play_music_main(pause_it=True)
        window.audio_handler.play_music_thematic()

        draw_black_background(ctx)
        
        # Sparse stars
        self.stars.render(ctx, timestamp)

        # Update and render scrolling credits before lunar surface
        self.credits.update(timestamp)
        self.credits.render(ctx, timestamp)

        # Draw lunar surface after credits so it appears as foreground
        self._draw_lunar_surface(ctx)
        
        # Draw Earth in the distance
        self._draw_earth(ctx, timestamp)

        if self.credits.finished:
            ctx.font = f"{max(12, int(min(window.canvas.width, window.canvas.height)) * 0.025)}px Courier New"
            instruction = "Click anywhere to return to solar system"
            ctx.fillText(instruction, window.canvas.width * 0.05, window.canvas.height * 0.25)
            ctx.restore()

            # Handle click to go back to orbiting planets scene
            if window.controls.click:
                # Reset all planet completions so we don't immediately return to final scene
                orbiting_scene = next(scene for scene in self.scene_manager._scenes if scene.name == ORBITING_PLANETS_SCENE)
                for planet in orbiting_scene.solar_sys.planets:
                    planet.complete = False
                log.debug("Reset all planet completions when returning from final scene")
                self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)

# --------------------
# create scene manager
# --------------------

def create_scene_manager() -> SceneManager:
    """
    Create all the scenes and add them to a scene manager that can be used to switch between them The object
    instance returned by this is used by the main game loop in game.py to check which scene is active when a
    frame is drawn and that scene's render method is called. Only one scene listed in the scene manager is
    active at a time, though scenes may have their own subscenes, such as textboxes that they render as part of
    their routine.
    """
    manager = SceneManager()
    planet_scene_state = PlanetState(0, window.canvas.height, 120.0, x=0, y=window.canvas.height // 2)
    solar_system = SolarSystem([window.canvas.width, window.canvas.height], planet_scene_state=planet_scene_state)
    orbiting_planets_scene = OrbitingPlanetsScene(ORBITING_PLANETS_SCENE, manager, solar_system)
    start_scene = StartScene(START_SCENE, manager)
    manager.add_scene(start_scene)
    manager.add_scene(orbiting_planets_scene)
    # Final victory scene (activated when all planets complete)
    final_scene = FinalScene(FINAL_SCENE, manager)
    manager.add_scene(final_scene)

    for planet in solar_system.planets:
        big_planet_scene = PlanetScene(f"{planet.name}-planet-scene", manager, planet)
        manager.add_scene(big_planet_scene)

    manager.activate_scene(START_SCENE)  # initial scene
    return manager
