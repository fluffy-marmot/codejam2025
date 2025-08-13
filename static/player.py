from .common import Position


class Player:
    def __init__(self, spritesheet) -> None:
        self.sprite = spritesheet
        self.position: Position = Position(0, 0)

    # im working on this
