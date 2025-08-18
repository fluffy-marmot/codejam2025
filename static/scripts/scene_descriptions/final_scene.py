"""
Final victory/credits scene.
"""

from scene_classes import Scene, SceneManager
from stars import StarSystem
from overlay import Credits
from window import window
from consolelogger import getLogger
from .scene_common import draw_black_background
from .constants import ORBITING_PLANETS_SCENE

log = getLogger(__name__, False)


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
