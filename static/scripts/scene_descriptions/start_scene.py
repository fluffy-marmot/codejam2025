"""
Start scene with alien dialogue introduction.
"""

from .scene_common import get_player
from scene_classes import Scene, SceneManager
from stars import StarSystem, StarSystem3d
from overlay import Dialogue
from common import Position
from window import window
from consolelogger import getLogger
from .scene_common import draw_black_background
from .constants import ORBITING_PLANETS_SCENE

log = getLogger(__name__, False)


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
            # log.debug(f"bobbing, val={self.bobbing_offset}")
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
