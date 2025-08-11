import math

from js import window  # type: ignore
from spacemass import SpaceMass

GRAVI_CONST = 0.67
planets = {planet["name"].lower(): planet for planet in window.planets}


class SolarSystem():
    
    def __init__(self, screen_size = [512, 512]):
       
        # Sun position (center of screen)
        self.sun_pos = [screen_size[0] // 2, screen_size[1] // 2]
        
        # Sun
        self.sun = SpaceMass(planets["sun"]["spritesheet"], 1000.0, 120.0, 0.0)
        
        # Inner planets
        self.mercury = SpaceMass(planets["mercury"]["spritesheet"], 3.3, 1.5, 2.5)
        self.venus = SpaceMass(planets["venus"]["spritesheet"], 48.7, 3.8, 2.0)
        self.earth = SpaceMass(planets["earth"]["spritesheet"], 59.7, 4.0, 1.8)
        self.mars = SpaceMass(planets["mars"]["spritesheet"], 6.4, 2.1, 1.5)
        
        # Outer planets
        self.jupiter = SpaceMass(planets["jupiter"]["spritesheet"], 1898.0, 44.0, 1.0)
        self.saturn = SpaceMass(planets["saturn"]["spritesheet"], 568.0, 36.0, 0.8)
        self.uranus = SpaceMass(planets["uranus"]["spritesheet"], 86.8, 16.0, 0.6)
        self.neptune = SpaceMass(planets["neptune"]["spritesheet"], 102.0, 15.0, 0.4)
        
        self.planets = [
            self.mercury, self.venus, self.earth, self.mars,
            self.jupiter, self.saturn, self.uranus, self.neptune
        ]
        
        # Initial positions (distance from sun in pixels)
        self.planet_distances = [60, 80, 100, 130, 200, 270, 320, 370]
        self.planet_angles: list[float] = [0, 45, 90, 135, 180, 225, 270, 315] 
        
        # Initialize planet positions
        self.planet_positions = []
        for i, planet in enumerate(self.planets):
            angle_rad = math.radians(self.planet_angles[i])
            x = self.sun_pos[0] + self.planet_distances[i] * math.cos(angle_rad)
            y = self.sun_pos[1] + self.planet_distances[i] * math.sin(angle_rad)
            self.planet_positions.append([x, y])

    def update(self):
        self.update_orbits(0.20)
        
    def update_orbits(self, dt:float):
        """Update planet positions using simple circular orbits"""
        for i, planet in enumerate(self.planets):

            angular_velocity = planet.initial_velocity * 0.01
            
            # Update angle
            self.planet_angles[i] += angular_velocity * dt * 60  # Scale for 60 FPS
            
            # Keep angle in range [0, 360)
            self.planet_angles[i] = self.planet_angles[i] % 360
            
            # Calculate new position using circular motion
            angle_rad = math.radians(self.planet_angles[i])
            x = self.sun_pos[0] + self.planet_distances[i] * math.cos(angle_rad)
            y = self.sun_pos[1] + self.planet_distances[i] * math.sin(angle_rad)
            
            # Update position
            self.planet_positions[i] = [x, y]
        
    def render(self, context, timestamp):
        """Render the entire solar system"""
        # Render sun at center
        self.sun.render(context, self.sun_pos, timestamp)
        
        # Render all planets
        for i, planet in enumerate(self.planets):
            planet.render(context, self.planet_positions[i], timestamp)

    # I Couldn't get this to work 〒__〒
    def calculateGForce(self, planet_index: int):
        """Calculate gravitational force between the sun and a planet"""
        # Get planet position
        planet_pos = self.planet_positions[planet_index]
        planet = self.planets[planet_index]
        
        # Calculate distance between sun and planet
        dx = planet_pos[0] - self.sun_pos[0]
        dy = planet_pos[1] - self.sun_pos[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Prevent division by zero
        if distance == 0:
            return 0
        
        # F = G * m1 * m2 / r^2
        force = GRAVI_CONST * self.sun.mass * planet.mass / (distance * distance)
        
        return force