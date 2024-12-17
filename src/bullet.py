import pygame
from pygame.math import Vector2
import math
from constants import *
from player import *

# A new constant for how close in depth the bullet needs to be to its target
BULLET_DEPTH_HIT_TOLERANCE = .25  # Tweak as needed

class Bullet:
    def __init__(
        self,
        position,
        direction,
        initial_depth,
        spaceship_width,
        spaceship_height,
        player_velocity=Vector2(0, 0),
        player_depth=1.0,
        is_enemy_bullet=False
    ):
        self.position = Vector2(position)
        self.direction = direction
        self.initial_depth = initial_depth
        self.depth = initial_depth
        self.player_depth = player_depth  # Track player depth (for enemy bullets, this is the "target depth")
        self.is_enemy_bullet = is_enemy_bullet  # Flag: enemy bullet vs. player bullet

        # Base direction vector
        base_direction = direction.split("_")[0]
        self.direction_vector = Vector2(DIRECTION_VECTORS.get(base_direction, (0, -1)))
        if self.direction_vector.length() == 0:
            self.direction_vector = Vector2(0, -1)

        # Base bullet speed
        self.base_speed = 88
        self.velocity = self.direction_vector * self.base_speed + player_velocity

        # If bullet is "inward" or "outward", set up depth movement
        if "inward" in direction:
            self.target_depth = MIN_DEPTH
            self.depth_change = 0.25
            self.velocity *= 0.25
        elif "outward" in direction:
            self.target_depth = BULLET_MAX_DEPTH
            self.depth_change = -0.25
            self.velocity *= 0.25
        else:
            self.target_depth = initial_depth
            self.depth_change = 0.0

        ship_size = min(spaceship_width, spaceship_height)
        # bullet.py
        if self.initial_depth != 0:
            self.base_size = max(0, int(ship_size / (2 * self.initial_depth)))
        else:
            self.base_size = 1  # Default size if depth is zero

        self.creation_time = pygame.time.get_ticks()
        self.alive = True
        self.total_depth_change = 2.0
        self.color = (255, 0, 0)  # Default to red
        if not self.is_enemy_bullet:
            self.color = (0, 255, 255)  # Cyan for player bullets
        self.size = self.base_size
        self.lifespan = 3333
        
    def get_collision_radius(self):
        # Return bullet's on-screen radius
        return self.size
    
    def update(self, delta_time):
        """
        Update the bullet's position and properties.

        Args:
            delta_time (float): The time elapsed since the last update.
        """
        # Update depth
        self.depth += self.depth_change * delta_time
        self.depth = max(MIN_DEPTH, min(MAX_DEPTH, self.depth))

        # Calculate proportion of depth change
        if "inward" in self.direction:
            proportion = (self.initial_depth - self.depth) / self.total_depth_change
        elif "outward" in self.direction:
            proportion = (self.depth - self.initial_depth) / self.total_depth_change
        else:
            proportion = 0.0

        proportion = max(0.0, min(1.0, proportion))

        # Adjust speed and size based on proportion
        if "inward" in self.direction:
            speed_scale = 1.0 + proportion
            size_scale = 1.0 + proportion
        elif "outward" in self.direction:
            speed_scale = 1.0 - proportion
            size_scale = 1.0 - proportion
        else:
            speed_scale = 1.0
            size_scale = 1.0

        # Update position
        parallax_factor = 1.0 / self.depth
        self.position += self.velocity * parallax_factor * delta_time * speed_scale

        # Update size
        if self.is_enemy_bullet:
            base_size = 5
        else:
            base_size = 5
        self.size = max(1, int(base_size * size_scale / self.depth))

        # **Updated Color Logic**
        if not self.is_enemy_bullet:  # Player bullets stay cyan
            self.color = (255, 0, 255)
        else:
            # Enemy bullet color changes with depth
            close_color = (255, 0, 0)
            far_color = (150, 0, 0)
            t = (self.depth - MIN_DEPTH) / (MAX_DEPTH - MIN_DEPTH)
            t = max(0, min(1, t))
            r = int(close_color[0] + t * (far_color[0] - close_color[0]))
            g = int(close_color[1] + t * (far_color[1] - close_color[1]))
            b = int(close_color[2] + t * (far_color[2] - close_color[2]))
            self.color = (r, g, b)

        # Remove bullet if off-screen, if it exceeds depth boundaries, or if it exceeds its lifespan
        current_time = pygame.time.get_ticks()
        if (self.position.x < 0 or self.position.x > WIDTH or
                self.position.y < 0 or self.position.y > HEIGHT or
                self.depth < MIN_DEPTH or self.depth > BULLET_MAX_DEPTH or
                current_time - self.creation_time > self.lifespan):
            self.alive = False

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), self.size)
        
        '''
        debug_font = pygame.font.SysFont(None, 16)
        depth_text = f"{self.depth:.2f}"
        depth_surf = debug_font.render(depth_text, True, (255, 255, 255))
        
        # Draw the depth text just below the bullet
        text_x = self.position.x - depth_surf.get_width() // 2
        text_y = self.position.y + self.size + 2  # offset below the bullet’s radius
        
        surface.blit(depth_surf, (text_x, text_y))'''
        
        
    def _get_onscreen_radius(self):
        """
        Returns the onscreen radius of the bullet for collision detection.
        """
        return self.size

    def check_collision(self, target):
        """
        Check collision with a target based on 2D overlap and depth tolerance.

        Args:
            target (Player or Enemy): The target to check collision against.

        Returns:
            bool: True if collision occurs, False otherwise.
        """
        # Depth tolerance check
        if hasattr(target, 'depth'):
            if abs(self.depth - target.depth) > BULLET_DEPTH_HIT_TOLERANCE:
                return False

        # Ensure target has necessary attributes
        if not hasattr(target, 'position') or not hasattr(target, '_get_onscreen_radius'):
            return False
        
        bullet_radius = self._get_onscreen_radius()
        target_radius = target._get_onscreen_radius()

        # Simple circle-to-circle collision in 2D
        if target.__class__.__name__ == 'Player':  # NEW
            player_center_position = Vector2(WIDTH // 2, HEIGHT // 2)
            distance = (self.position - player_center_position).length()
        else:
            distance = (self.position - target.position).length()
        if distance < (bullet_radius + target_radius):
            return True

        return False
