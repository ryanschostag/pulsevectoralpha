# star.py

import random
import pygame
from pygame.math import Vector2
import math
from constants import *

class Star:
    def __init__(self, x, y, depth):
        """Initialize a star with enhanced visual properties.
        
        Args:
            x (float): Initial x-coordinate
            y (float): Initial y-coordinate
            depth (float): Initial depth in 3D space
        """
        self.position = Vector2(x, y)
        self.velocity = Vector2(random.uniform(-50, 50), random.uniform(-50, 50))
        self.depth = depth
        self.base_size = random.uniform(1.5, 4.0)  # Base size for visual rendering
        self.size = self.base_size  # Compatibility attribute for click detection
        self.flicker_intensity = random.uniform(0.7, 1.0)
        self.flicker_speed = random.uniform(0.1, 0.5)
        self.relative_velocity = Vector2(0, 0)
        self.trail_positions = []
        self.max_trail_length = 0
        self.color = self._generate_star_color()
        self.type = "star"
        
    def _generate_star_color(self):
        """Generate a slightly varied star color based on temperature simulation.
        
        Returns:
            tuple: RGB color values
        """
        temperature = random.uniform(0, 1)
        if temperature < 0.3:  # Cooler stars (yellowish)
            return (255, 255, random.randint(200, 255))
        elif temperature < 0.7:  # Medium stars (white with slight variation)
            base = random.randint(240, 255)
            return (base, base, base)
        else:  # Hotter stars (bluish)
            return (random.randint(200, 255), random.randint(200, 255), 255)

    def update(self, player_velocity, depth_change, delta_time, is_target=False, global_depth_change=0):
        """
        Update star position, depth, and visual effects. Handles wrapping for both normal movement and when orbiting a locked star.

        Args:
            player_velocity (Vector2): Current player velocity.
            depth_change (float): Change in depth.
            delta_time (float): Time elapsed since last frame.
            is_target (bool): Whether this star is currently targeted.
            global_depth_change (float): Global depth change affecting all stars.
        """
        # Store previous position for trail effect
        self.trail_positions.insert(0, self.position.copy())
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop()

        # Update depth and apply global depth change
        self.depth += depth_change + global_depth_change

        # Enhanced parallax effect for movement
        parallax_factor = math.pow(1.0 / max(self.depth, MIN_DEPTH), 1.2)
        movement = player_velocity * parallax_factor * delta_time
        self.position -= movement

        # Handle orbital relative movement if locked
        if is_target:
            self.position.x = (self.position.x - player_velocity.x * delta_time) % WIDTH
            self.position.y = (self.position.y - player_velocity.y * delta_time) % HEIGHT

        # Apply wrapping with optional components
        self._handle_wrapping(
            invert_x=True,
            invert_y=True,
            invert_depth=False
        )

    def _handle_wrapping(self, invert_x=True, invert_y=True, invert_depth=True):
        """
        Handles position and depth wrapping for stars. Ensures stars are properly wrapped and inverted
        based on optional toggles.

        Args:
            invert_x (bool): Whether to invert the Y position when wrapping on the X-axis.
            invert_y (bool): Whether to invert the X position when wrapping on the Y-axis.
            invert_depth (bool): Whether to wrap the depth during wrapping.
        """
        # --- X-axis wrapping and optional inversion ---
        if self.position.x < 0:
            self.position.x += WIDTH  # Wrap to the right
            if invert_x:
                self.position.y = HEIGHT - self.position.y  # Invert Y
        elif self.position.x > WIDTH:
            self.position.x -= WIDTH  # Wrap to the left
            if invert_x:
                self.position.y = HEIGHT - self.position.y  # Invert Y

        # --- Y-axis wrapping and optional inversion ---
        if self.position.y < 0:
            self.position.y += HEIGHT  # Wrap to the bottom
            if invert_y:
                self.position.x = WIDTH - self.position.x  # Invert X
        elif self.position.y > HEIGHT:
            self.position.y -= HEIGHT  # Wrap to the top
            if invert_y:
                self.position.x = WIDTH - self.position.x  # Invert X

        # --- Depth wrapping ---
        if self.depth < MIN_DEPTH:
            self.depth = MAX_DEPTH - (MIN_DEPTH - self.depth)  # Wrap from min depth to max depth
        elif self.depth > MAX_DEPTH:
            self.depth = MIN_DEPTH + (self.depth - MAX_DEPTH)  # Wrap from max depth to min depth

    def get_click_radius(self):
        """Calculate the clickable radius of the star based on its depth.
        
        Returns:
            float: The radius of the clickable area
        """
        return max(1, self.size / math.pow(self.depth, 0.7))

    def is_clicked(self, click_position):
        """Check if the star was clicked.
        
        Args:
            click_position (Vector2): The position of the mouse click
            
        Returns:
            bool: True if the star was clicked, False otherwise
        """
        click_radius = self.get_click_radius()
        return (self.position - click_position).length() <= click_radius * 1.5  # 1.5x radius for easier clicking

    def draw(self, surface):
        """Draw the star with enhanced visual effects.
        
        Args:
            surface (pygame.Surface): Target surface for rendering
        """
        base_radius = self.get_click_radius()
        
        # Apply flicker effect
        flicker = self.flicker_intensity + math.sin(pygame.time.get_ticks() * 0.001 * self.flicker_speed) * 0.3
        radius = base_radius * flicker
        
        # Draw motion trail
        for i, pos in enumerate(self.trail_positions):
            trail_alpha = int(255 * (1 - i / len(self.trail_positions)) * 0.3)
            trail_color = (*self.color[:3], trail_alpha)
            trail_surface = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, trail_color, 
                             (int(radius), int(radius)), max(1, radius * 0.8))
            surface.blit(trail_surface, 
                        (int(pos.x - radius), int(pos.y - radius)))

        # Draw main star with glow effect
        glow_radius = radius * 2
        glow_surface = pygame.Surface((int(glow_radius * 2), int(glow_radius * 2)), pygame.SRCALPHA)
        
        # Inner glow
        for i in range(3):
            current_radius = glow_radius * (1 - i * 0.2)
            alpha = int(100 * (1 - i * 0.3))//2
            glow_color = (*self.color[:3], alpha)
            pygame.draw.circle(glow_surface, glow_color,
                             (int(glow_radius), int(glow_radius)), 
                             max(1, int(current_radius)))

        # Core star
        pygame.draw.circle(glow_surface, self.color,
                         (int(glow_radius), int(glow_radius)), 
                         max(1, int(radius)))
        
        # Blend onto main surface
        surface.blit(glow_surface, 
                    (int(self.position.x - glow_radius),
                     int(self.position.y - glow_radius)))
