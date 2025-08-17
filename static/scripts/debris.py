import math
from random import randint

from common import Position
from window import window
from scene_classes import SceneObject


class Debris(SceneObject):
    def __init__(self, position: Position, color: str, radius: float, duration: int, rotation: float) -> None:
        super().__init__()
        super().set_position(position)

        self.color = color
        self.radius = radius
        # number of frames until this debris should decay
        self.initial_duration = self.duration = duration
        self.rotation = rotation
        self.momentum = Position(0, 0)

    def update(self) -> None:
        # decay duration by 1 frame
        self.duration -= 1

        # adjust position based on momentum and break Newton's laws a little
        self.x += self.momentum.x * 0.4
        self.y += self.momentum.y * 0.4
        self.momentum.x *= 0.97
        self.momentum.y *= 0.97

    def render(self, ctx, timestamp) -> None:
        ctx.save()

        ctx.translate(*self.get_position())
        ctx.rotate(self.rotation)

        ctx.beginPath()
        # Outer arc
        ctx.arc(0, 0, self.radius, 0, 2 * math.pi, False)
        # Inner cut arc (opposite winding, offset)
        ctx.arc(
            self.radius * 0.3 * self.duration / self.initial_duration,
            0,
            self.radius * (1.2 - 0.8 * self.duration / self.initial_duration),
            0,
            2 * math.pi,
            True,
        )

        ctx.closePath()
        ctx.fillStyle = self.color
        ctx.globalAlpha = min(self.duration / 255, 1.0)  # normalize to 0..1
        ctx.fill()

        ctx.restore()
        # DEBUGGING THE CIRCLES DEFINING CRESCENT ABOVE ^
        if window.DEBUG_DRAW_HITBOXES:
            ctx.save()
            ctx.translate(*self.get_position())
            ctx.rotate(self.rotation)
            ctx.strokeStyle = "#FF0000"
            ctx.beginPath()
            ctx.arc(0, 0, self.radius, 0, 2 * math.pi, False)
            ctx.stroke()
            ctx.closePath()

            ctx.strokeStyle = "#00FF00"
            ctx.beginPath()
            ctx.arc(
                self.radius * 0.3 * self.duration / self.initial_duration,
                0,
                self.radius * (1.2 - 0.8 * self.duration / self.initial_duration),
                0,
                2 * math.pi,
                True,
            )
            ctx.stroke()
            ctx.closePath()
            ctx.restore()

        super().render(ctx, timestamp)


class DebrisSystem(SceneObject):
    def __init__(self) -> None:
        super().__init__()

        self.debris_list: list[Debris] = []  # will be filled with debris object instances

    def update(self) -> None:
        # tick each debris' timer and discard any debris whose timer has run out
        for debris in self.debris_list:
            debris.update()
        self.debris_list = list(filter(lambda deb: deb.duration > 0, self.debris_list))

    def generate_debris(self, player_pos: Position, asteroid_pos: Position, max_size=3) -> None:
        distance = player_pos.distance(asteroid_pos)
        new_debris = []
        for _ in range(randint(3, 5)):
            position = player_pos.midpoint(asteroid_pos) + Position(randint(-20, 20), randint(-20, 20))
            shade = randint(128, 255)
            color = f"#{shade:x}{shade:x}{shade:x}"
            radius = randint(15, 25) * min(50 / distance, max_size)
            duration = randint(100, 200)
            rotation = 0

            new_debris.append(Debris(position, color, radius, duration, rotation))

        new_debris_center = Position(
            sum(debris.x for debris in new_debris) / len(new_debris),
            sum(debris.y for debris in new_debris) / len(new_debris),
        )

        for debris in new_debris:
            debris.momentum = Position((debris.x - new_debris_center.x) / 5.0, (debris.y - new_debris_center.y) / 5.0)
            debris.rotation = math.atan2(-debris.y + new_debris_center.y, -debris.x + new_debris_center.x)

        self.debris_list.extend(new_debris)

    def render(self, ctx, timestamp) -> None:
        """Render every debris"""
        for debris in self.debris_list:
            debris.render(ctx, timestamp)

        super().render(ctx, timestamp)

    def reset(self):
        self.debris_list = []
