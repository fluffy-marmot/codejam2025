from __future__ import annotations

from typing import Any, overload

from common import Position

HTMLImageElement = Any
CanvasRenderingContext2D = Any

# ====================================================
# Scene Object abstract class
# ====================================================


class SceneObject:
    def __init__(self):
        """every scene object keeps track of the last milisecond timestamp when it was rendered"""
        self.last_timestamp = 0

    def render(self, ctx: CanvasRenderingContext2D, timestamp: float):
        # update the last rendered timestamp
        self.last_timestamp = timestamp

    """ 
    A few subclasses use these position methods so moved them here for shared functionality.
    SceneObject subclasses where these don't make sense can just ignore them. (e.g. SolarSystem)
    """

    @overload
    def set_position(self, x: float, y: float): ...

    @overload
    def set_position(self, x: Position): ...

    def set_position(self, x_or_pos, y=None):
        if y is not None:
            x = x_or_pos
            self.x = x
            self.y = y
        else:
            pos = x_or_pos
            self.x = pos.x
            self.y = pos.y

    def get_position(self) -> Position:
        return Position(self.x, self.y)


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
        self._scenes: list[Scene] = []

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
