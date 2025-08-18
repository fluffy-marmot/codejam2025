"""
Planet scene handling asteroid dodging gameplay and scanning mechanics.
"""

from player import Player, PlayerExplosion
from scene_classes import Scene, SceneManager
from spacemass import SpaceMass
from stars import StarSystem
from window import window
from consolelogger import getLogger
from .scene_common import get_player, get_scanner, get_asteroid_system, get_debris_system, draw_black_background, ResultsScreen, DeathScreen

log = getLogger(__name__, False)


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
        from .constants import ORBITING_PLANETS_SCENE
        
        log.debug(f"Finished planet {self.planet.name}! Reactivating orbiting planets scene.")
        self.scene_manager.activate_scene(ORBITING_PLANETS_SCENE)
        get_player().active = False
        self.results_overlay.active = True
        get_player().health += Player.FULL_HEALTH/3
        self.planet.switch_view()
        self.planet.complete = True

    def handle_player_death(self):
        """Handle when the player dies and clicks on the death screen."""
        from .constants import ORBITING_PLANETS_SCENE
        
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
