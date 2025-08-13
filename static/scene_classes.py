from __future__ import annotations
from typing import Any

HTMLImageElement = Any
CanvasRenderingContext2D = Any

# ====================================================
# Scene Object abstract class
# ====================================================

class SceneObject:
    def __init__(self):

        """ every scene object keeps track of the last milisecond timestamp when it was rendered """
        self.last_timestamp = 0

    def render(self, ctx: CanvasRenderingContext2D, timestamp: float):
        ...
        # update the last rendered timestamp
        self.last_timestamp = timestamp

# --------------------
# Scene Class
# --------------------

class Scene(SceneObject):
    def __init__(self, name: str, scene_manager: SceneManager):
        super().__init__()
        self.name = name
        self.active = False
        self.scene_manager = scene_manager

# --------------------
# Scene Manager Class
# --------------------

class SceneManager:
    def __init__(self):
        self._scenes = []

    def add_scene(self, scene: Scene):
        self._scenes.append(scene)

    def activate_scene(self, scene_name):
        """
        Deactivate all scenes, and only activate the one with the provided name
        """
        for scene in self._scenes:
            scene.active = False
        next(scene for scene in self._scenes if scene.name == scene_name).active = True
    
    def get_active_scene(self):
        return next(scene for scene in self._scenes if scene.active)