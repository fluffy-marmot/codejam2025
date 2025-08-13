from js import document, window # type: ignore
from pyodide.ffi import create_proxy # type: ignore
import math
from solar_system import SolarSystem

import random

canvas = document.getElementById("gameCanvas")
ctx = canvas.getContext("2d")
container = document.getElementById("canvasContainer")
width, height = container.clientWidth, container.clientHeight


class Asteroid:
    def __init__(self, max_size, x, y, travel_time):
        self.max_size = max_size
        self.size = 0
        self.x = x
        self.y = y
        self.travel_time = travel_time
        self.animation_timer = 0
        self.color = "rgb(255, 255, 255)"
        self.hazard = False #when its big enough (close enough, then the player could die)
    def render(self, ctx, current_time):
        if current_time - self.animation_timer >= self.travel_time:
            self.animation_timer = current_time

            if self.size + 1 < self.max_size:
                self.size += 1
            #TODO: Its red for a very short time, not enough for player warning
            if self.size >= self.max_size / 2:
                print("its hazard now")
                self.hazard = True
                self.color = "rgb(255, 0, 0)"

        ctx.fillStyle = self.color
        ctx.beginPath()
        ctx.rect(self.x, self.y, self.size, self.size)
        ctx.fill()


class AsteriodAttack:
    def __init__(self, spawnrate):
       self.astriods = []
       self.timer = 0
       self.spawnrate = spawnrate
    
    def generate_astriods(self, current_time, size, player_x, player_y, speed):
        if current_time - self.timer >= self.spawnrate:
            self.timer = current_time
            astriod = Asteroid(size, player_x, player_y, speed)
            self.astriods.append(astriod)
    
    def render(self, ctx, current_time):
        for index, astriod in enumerate(self.astriods):
            astriod.render(ctx, current_time)
            if astriod.hazard:
                self.astriods.pop(index)
            

