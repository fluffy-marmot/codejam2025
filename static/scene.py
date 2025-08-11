from collections import deque
from pathlib import Path
from js import Image #type: ignore
from js import window #type: ignore
from spacemass import SpaceMass

class Scene:
    
    def __init__(self) -> None:
        
        self.children:list[SpaceMass] = []
        self.player = None
        self.background = None
        
    def initialize(self):
        pass
    
    def update(self):
        pass
    
    def add (self, child:SpaceMass):
        if isinstance(child, SpaceMass):
            self.children.append(child)
        
    def remove (self, child:SpaceMass):
        if child in self.children and isinstance(child, SpaceMass):
            self.children.remove(child)
            
    def setBackground(self, path:str):
        if Path(path).exists():
            self.background = Image.new()
            self.background.src = path
            
    def setChildPos(self, child:SpaceMass, pos:list):
        if child in self.children and isinstance(child, SpaceMass):
            child.position = pos
            
    def render(self, ctx, current_time):
        self.update()
        if self.background:
            ctx.drawImage(self.background, 0, 0, ctx.canvas.width, ctx.canvas.height)
        
        for child in self.children:
            if child.position:
                child.render(ctx, current_time)
        
        