from js import document, window  # type: ignore
from pyodide.ffi import create_proxy  # type: ignore
# from pyscript import Element # type: ignore

from dataclasses import dataclass
from time import time

from consolelogger import getLogger

log = getLogger(__name__)

@dataclass
class MousePositions:
    mousedown: tuple
    mouseup: tuple
    click: tuple
    move: tuple

class GameControls:

    MOUSE_LEFT = "mouse_left"
    MOUSE_RIGHT = "mouse_right"
    MOUSE_MIDDLE = "mouse_middle"

    # just to use internally in the class to translate the 0, 1, 2 javascript convention
    mouse_button_map = { 0: MOUSE_LEFT, 1: MOUSE_MIDDLE, 2: MOUSE_RIGHT }

    def __init__(self, canvas, enable_logging=False):

        # keep track of what keys \ mouse buttons are currently pressed in this variable
        self.pressed = set()
        # keep track of the last coordinates used by all mouse events
        self.mouse = MousePositions( (0, 0), (0, 0), (0, 0), (0, 0) )
        # keep track of whether a click has occurred
        self.click = False

        # enable logging of mouse and key events in the console for debug purposes
        self._logging = enable_logging
        self._last_mousemove_log = 0
        
        on_canvas_mousedown_proxy = create_proxy(self.on_canvas_mousedown)
        on_canvas_mouseup_proxy = create_proxy(self.on_canvas_mouseup)
        on_canvas_click_proxy = create_proxy(self.on_canvas_click)
        on_canvas_mousemove_proxy = create_proxy(self.on_canvas_mousemove)
        on_keydown_proxy = create_proxy(self.on_keydown)
        on_keyup_proxy = create_proxy(self.on_keyup)

        canvas.addEventListener("mousedown", on_canvas_mousedown_proxy)
        canvas.addEventListener("mouseup", on_canvas_mouseup_proxy)
        canvas.addEventListener("click", on_canvas_click_proxy)
        canvas.addEventListener("mousemove", on_canvas_mousemove_proxy)
        canvas.addEventListener("keydown", on_keydown_proxy)
        canvas.addEventListener("keyup", on_keyup_proxy)


    def on_canvas_mousedown(self, event):
        self.mouse.move = (event.clientX, event.clientY)
        self.mouse.mousedown = (event.clientX, event.clientY)

        if event.button in self.mouse_button_map:
            button = self.mouse_button_map[event.button]
            self.pressed.add(button)
        
            if self._logging:
                log.debug("mousedown %s %s, %s", button, event.clientX, event.clientY)

    def on_canvas_mouseup(self, event):
        self.mouse.move = (event.clientX, event.clientY)
        self.mouse.mouseup = (event.clientX, event.clientY)

        if event.button in self.mouse_button_map:
            button = self.mouse_button_map[event.button]
            if button in self.pressed: self.pressed.remove(button)
        
            if self._logging:
                log.debug("mouseup %s %s, %s", button, event.clientX, event.clientY)

    def on_canvas_click(self, event):
        self.mouse.move = (event.clientX, event.clientY)
        self.mouse.click = (event.clientX, event.clientY)

        self.click = True
        if self._logging:
            log.debug("click %s, %s", event.clientX, event.clientY)

    def on_canvas_mousemove(self, event):
        self.mouse.move = (event.clientX, event.clientY)

        # throttle number of mousemove logs to prevent spamming the debug log
        if self._logging and (now:=time()) - self._last_mousemove_log > 2.5:
            log.debug("mousemove %s, %s", event.clientX, event.clientY)
            self._last_mousemove_log = now

        # TODO: check event.buttons here (tells which buttons are pressed during mouse move) if mouse is pressed
        # down on canvas, then moved off, and button is unpressed while off the canvas, mouse buttons may be
        # flagged as down when they aren't anymore, checking event.buttons would be a good way to 'unstuck' them

    def on_keydown(self, event):
        self.pressed.add(event.key)
        if self._logging:
            log.debug("keydown %s", event.key)

    def on_keyup(self, event):
        if event.key in self.pressed: self.pressed.remove(event.key)
        if self._logging:
            log.debug("keyup %s", event.key)

    # TODO: probably also need a way to handle canvas losing focus and missing key up events, for example if alt
    # tabbing away, it registers a key down event, but the not a key up event since it has already lost focus by
    # that point