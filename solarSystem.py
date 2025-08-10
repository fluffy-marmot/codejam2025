from window import Window
from spacemass import SpaceMass
import math

GRAVI_CONST = 0.67

class SolarSystem(Window):
    
    def __init__(self, screen_size = [512, 512]):
        super().__init__(screen_size)
        
        # Sun position (center of screen)
        self.sun_pos = [screen_size[0] // 2, screen_size[1] // 2]
        
        # Sun
        self.sun = SpaceMass("assets/sun sprites", 1000.0, 120.0, 0.0)
        
        # Inner planets
        self.mercury = SpaceMass("assets/mercury sprites", 3.3, 1.5, 2.5)
        self.venus = SpaceMass("assets/venus sprites", 48.7, 3.8, 2.0)
        self.earth = SpaceMass("assets/earth sprites", 59.7, 4.0, 1.8)
        self.mars = SpaceMass("assets/mars sprites", 6.4, 2.1, 1.5)
        
        # Outer planets
        self.jupiter = SpaceMass("assets/jupiter sprites", 1898.0, 44.0, 1.0)
        self.saturn = SpaceMass("assets/saturn sprites", 568.0, 36.0, 0.8)
        self.uranus = SpaceMass("assets/uranus sprites", 86.8, 16.0, 0.6)
        self.neptune = SpaceMass("assets/neptune sprites", 102.0, 15.0, 0.4)
        
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
        
    def render(self):
        """Render the entire solar system"""
        if self.screen is not None:
            self.screen.fill((10, 10, 30))
        # Render sun at center
        self.sun.render(self.screen, self.sun_pos)
        
        # Render all planets
        for i, planet in enumerate(self.planets):
            planet.render(self.screen, self.planet_positions[i])

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

def main():
    game = SolarSystem(screen_size=[800, 800])
    game.run()

if __name__ == "__main__":
    main()


