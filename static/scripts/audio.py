import random

from js import Audio  # type: ignore[attr-defined]


class AudioHandler:
    def __init__(self, static_url: str) -> None:
        self.static_url = static_url
        self.volume: int = 100

    def play_sound(self, audio_name: str, volume=1.0) -> None:
        """
        play a sound file
        audio_name: name of sound file, without any path included, as it appears in static/audio/
        volume: adjust this for loud sound files, 0.0 to 1.0, where 1.0 is full volume
        """
        sound = Audio.new(f"{self.static_url}audio/{audio_name}")
        sound.volume = volume
        sound.play()

    def play_bang(self) -> None:
        # these bangs are kind of loud, playing it at reduced volume
        self.play_sound(random.choice(["bang1.ogg", "bang2.ogg", "bang3.ogg"]), volume=0.75)
