from js import Audio, window   # type: ignore[attr-defined]
import random

class AudioHandler:

    def __init__(self, static_url: str) -> None:
        self.static_url = static_url
        self.volume: int = 100

    def play_sound(self, audio_name: str) -> None:
        sound = Audio.new(f"{self.static_url}audio/{audio_name}")
        sound.play()

    def play_bang(self) -> None:
        self.play_sound(random.choice(["bang1.ogg", "bang2.ogg", "bang3.ogg"]))