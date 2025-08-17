import random
from typing import Union

from js import Audio  # type: ignore[attr-defined]


class AudioHandler:
    def __init__(self, static_url: str) -> None:
        self.static_url = static_url
        self.volume: int = 100

        self.text_sound = self.load_audio("text.ogg")

    def load_audio(self, audio_name: str) -> Audio:
        return Audio.new(f"{self.static_url}audio/{audio_name}")

    def play_sound(self, audio_name: Union[str, "Audio"], volume=1.0) -> None:
        """
        play a sound file
        audio_name: name of sound file, without any path included, as it appears in static/audio/
        volume: adjust this for loud sound files, 0.0 to 1.0, where 1.0 is full volume
        """
        # sometimes we want to load new instances of Audio objcts, other times we want a persistent one
        if isinstance(audio_name, str):
            sound = self.load_audio(audio_name)
        else:
            sound = audio_name
        sound.volume = volume
        sound.play()

    def play_bang(self) -> None:
        # these bangs are kind of loud, playing it at reduced volume
        self.play_sound(random.choice(["bang1.ogg", "bang2.ogg", "bang3.ogg"]), volume=0.4)

    def play_text(self, pause_it=False) -> None:
        if not pause_it and self.text_sound.paused:
            self.play_sound(self.text_sound, volume=1.0)
        elif pause_it:
            self.text_sound.pause()
            self.text_sound.currentTime = 0

        