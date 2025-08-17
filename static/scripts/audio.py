import random
from typing import Union
from functools import partial

from js import Audio  # type: ignore[attr-defined]


class AudioHandler:
    def __init__(self, static_url: str) -> None:
        self.static_url = static_url
        self.volume: int = 1.0

        self.text_sound = self.load_audio("text.ogg")
        self.scan_sound = self.load_audio("scan.ogg")
        self.music_main = self.load_audio("music_main.ogg")
        self.death_sound = self.load_audio("death.ogg")

        self.active_music = None

    def set_volume(self, volume: float) -> None:
        """ set volume to somewhere between 0.0 and 1.0 if a valid value is given """
        if 0.0 <= volume <= 1.0:
            self.volume = volume

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
        sound.volume = volume * self.volume
        sound.play()

    def play_bang(self) -> None:
        # these bangs are kind of loud, playing it at reduced volume
        self.play_sound(random.choice(["bang1.ogg", "bang2.ogg", "bang3.ogg"]), volume=0.4)

    def play_unique_sound(self, audio: Audio, pause_it=False, volume=1.0) -> None:
        if not pause_it and audio.paused:
            self.play_sound(audio, volume=volume)
        elif pause_it:
            audio.pause()
            audio.currentTime = 0

    def play_text(self, pause_it=False, volume=1.0) -> None:
        self.play_unique_sound(self.text_sound, pause_it, volume=0.8)

    def play_scan(self, pause_it=False, volume=1.0) -> None:
        self.play_unique_sound(self.scan_sound, pause_it, volume=0.4)

    def play_music_main(self, pause_it=False, volume=1.0) -> None:
        # if another music file is playing, don't play this one
        if self.active_music and not self.active_music.paused: 
            return
        self.active_music = self.music_main
        self.play_unique_sound(self.music_main, pause_it, volume=0.65)

    def play_death(self, volume=1.0) -> None:
        self.play_sound(self.death_sound, volume=0.6)
