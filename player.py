# player.py

import pygame
from pygame.math import Vector2
from constants import *
from utils import *
import math
from spaceship import *
from bullet import *

MAX_PLAYER_SPEED = 21
PLAYER_ACCELERATION = 88

class Player:
    def __init__(self):
        # Initialize position at the center of the screen
        self.position = Vector2(WIDTH // 2, HEIGHT // 2)
        self.velocity = Vector2()
        self.depth = 1.0
        self.last_direction = "up"

        # Scroll-related attributes
        self.scroll_states = ["inward", "middle", "outward"]
        self.scroll_mode = "middle"
        self.depth_buffer = DEPTH_RATE * 2
        self.target_depth = 1.0
        self.depth_transition_speed = 0.01  # Units per second
        self.depth_scroll_increment = 0.01
        self.min_scroll_depth = MIN_DEPTH + self.depth_buffer
        self.max_scroll_depth = MAX_DEPTH - self.depth_buffer

        # Direction and movement
        self.direction = "up"

        # Boost-related attributes
        self.boost_velocity = Vector2(0, 0)
        self.boost_decay_rate = 0.995
        self.boost_duration = 0.0
        self.max_boost_duration = 2.0

        # Manual control tracking
        self.manual_control_active = False
        self.manual_control_timeout = 0.5
        self.manual_control_timer = 0.0
        self.target_direction = "up"

        # Auto-follow attributes
        self.auto_follow_active = False
        self.auto_follow_target = None
        self.auto_follow_speed = 21.0  # Adjust as necessary for game balance

        # Maximum speed limit
        self.max_speed = MAX_PLAYER_SPEED  # Define this constant in your constants.py

        self.stars = []
        self.enemies = []
        self.bullets = []
        self.current_radius = 10
        self.health = 100
        self.max_health = 100
        
    def _get_onscreen_radius(self):
        """
        Returns the radius used for collision detection against bullets.
        """
        # You could make this dynamic based on depth or sprite size.
        # For simplicity, let's assume it's a constant or something proportional to `current_radius`.
        # If you want it to shrink/grow with depth, scale it: int(self.current_radius / self.depth) etc.
        try:
            radius = max(0, int(self.current_radius / self.depth))
            return radius
        except:
            return 1
    
    def enable_auto_follow(self, target):
        """
        Enables auto-follow mode for a specific target.

        Args:
            target (TypeDEnemy): The enemy to auto-follow.
        """
        if target:
            self.auto_follow_active = True
            self.auto_follow_target = target
            print(f"Auto-Follow enabled for {target}.")
    
    def disable_auto_follow(self):
        """
        Disables auto-follow mode.
        """
        self.auto_follow_active = False
        self.auto_follow_target = None
        print("Auto-Follow disabled.")

    def handle_input(self, delta_time):
        """
        Handles player input for movement, direction, and auto-follow.

        Args:
            delta_time (float): Time elapsed since the last frame.

        Returns:
            float: Depth change applied during this frame.
        """
        keys_pressed = pygame.key.get_pressed()
        depth_change = 0.0

        # Check for manual movement input
        current_manual_input = any([
            keys_pressed[pygame.K_w],
            keys_pressed[pygame.K_a],
            keys_pressed[pygame.K_s],
            keys_pressed[pygame.K_d]
        ])
        #if not any([keys_pressed[pygame.K_w], keys_pressed[pygame.K_a], keys_pressed[pygame.K_s], keys_pressed[pygame.K_d]]):
        #    self.velocity = Vector2(0, 0)
        if current_manual_input:
            self.manual_control_active = True
            self.manual_control_timer = self.manual_control_timeout
        elif self.manual_control_timer > 0:
            self.manual_control_timer -= delta_time
            if self.manual_control_timer <= 0:
                self.manual_control_active = False

        # Determine current direction based on input
        current_direction = get_direction(keys_pressed, BASE_DIRECTION_MAP)

        # Update last_direction if there's manual input
        if current_direction:
            self.last_direction = current_direction

        # Initialize acceleration
        acceleration = Vector2(0, 0)

        # Calculate movement based on manual input
        acceleration = Vector2(
            (keys_pressed[pygame.K_d] - keys_pressed[pygame.K_a]),
            (keys_pressed[pygame.K_s] - keys_pressed[pygame.K_w])
        ) * PLAYER_ACCELERATION  # Use an acceleration constant
        
        # Apply acceleration to velocity
        self.velocity += acceleration * delta_time

        # Apply boost velocity if active
        if self.boost_duration > 0:
            self.velocity += self.boost_velocity * delta_time
            self.update_boost(delta_time)

        # Clamp the velocity to the maximum speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalize() * self.max_speed

        self._update_position()

        # Direction priority system with proper outward state handling
        if self.manual_control_active and not self.auto_follow_active:
            # Use manual input direction, preserving scroll state
            base_direction = current_direction if current_direction else self.last_direction
        elif self.auto_follow_active and self.auto_follow_target:
            # Calculate direction towards the auto-follow target
            direction_vector = (self.auto_follow_target.position - self.position).normalize()
            angle = math.degrees(math.atan2(-direction_vector.y, direction_vector.x)) % 360
            base_direction = self.calculate_direction_from_angle(angle)
            self.last_direction = base_direction
        else:
            base_direction = self.last_direction

        # Determine current direction based on input
        current_direction = get_direction(pygame.key.get_pressed(), BASE_DIRECTION_MAP)

        # Update last_direction if there's manual input
        if current_direction:
            self.last_direction = current_direction

        # Apply scroll mode to the ship's direction
        if self.scroll_mode != "middle":
            full_direction = f"{self.last_direction}_{self.scroll_mode}"
            if full_direction in SPACESHIP_SHAPES:
                self.direction = full_direction
            else:
                self.direction = self.last_direction
        else:
            self.direction = self.last_direction

        return depth_change

    def update_scroll_mode(self):
        """Update scroll mode (inward, middle, outward) based on player's depth relative to the target."""
        if self.auto_follow_active and self.auto_follow_target:
            target_depth = self.auto_follow_target.depth
            depth_difference = self.depth - target_depth

            # Customizable offsets for determining scroll mode
            inward_offset = .5
            middle_offset = .5
            outward_offset = .5 

            if depth_difference < -outward_offset:  # Player is shallower than target
                self.scroll_mode = "outward"
            elif -middle_offset <= depth_difference <= middle_offset:  # Player is within middle range
                self.scroll_mode = "inward"
            elif depth_difference > inward_offset:  # Player is deeper than target
                self.scroll_mode = "middle"
            
            # Update the player's direction to reflect the new scroll mode
            base_direction = self.direction.split("_")[0]  # Extract current base direction
            if self.scroll_mode != "middle":
                self.direction = f"{base_direction}_{self.scroll_mode}"
            else:
                self.direction = base_direction

    def calculate_direction_from_angle(self, angle):
        """
        Converts an angle in degrees to the closest direction string.

        Args:
            angle (float): Angle in degrees.

        Returns:
            str: Direction string (e.g., "up", "down_left").
        """
        direction_ranges = {
            "right": (-22.5, 22.5),
            "up_right": (22.5, 67.5),
            "up": (67.5, 112.5),
            "up_left": (112.5, 157.5),
            "left": (157.5, 202.5),
            "down_left": (-157.5, -112.5),
            "down": (-112.5, -67.5),
            "down_right": (-67.5, -22.5)
        }

        for direction, (start, end) in direction_ranges.items():
            # Normalize angle to be within -180 to 180
            normalized_angle = (angle + 180) % 360 - 180
            if start <= normalized_angle < end:
                return direction
        return self.last_direction  # Default to last known direction

    def handle_target_release(self, target, orbital_velocity):
        """
        Handles the slingshot boost when releasing a target star or enemy.
        Now properly considers the ship's actual facing direction.

        Args:
            target: The target being released (Star or Enemy)
            orbital_velocity: Current orbital velocity around the target
        """
        if target is None:
            return

        # Get the raw direction without scroll modifiers
        base_direction = self.direction.split('_')[0] if '_' in self.direction else self.direction

        # Get the direction vector based on the ship's current facing
        boost_direction = Vector2(DIRECTION_VECTORS[base_direction])
        boost_direction = boost_direction.normalize()

        # Calculate boost magnitude based on orbital velocity
        MAX_BOOST_SPEED = 1e3
        relative_speed = target.relative_velocity.length() if hasattr(target, 'relative_velocity') else 0
        boost_magnitude = min(relative_speed * 2.0, MAX_BOOST_SPEED)
        
        # Apply the boost in the ship's facing direction
        self.boost_velocity = boost_direction * boost_magnitude
        self.boost_duration = self.max_boost_duration

    def handle_wheel(self, y, delta_time):
        """
        Handles mouse wheel input for smooth depth transitions.

        Args:
            y (int): Scroll direction (-1 for scroll down, 1 for scroll up).
            delta_time (float): Time elapsed since last frame.

        Returns:
            float: Actual depth change applied this frame.
        """
        if y != 0:
            # Update scroll mode based on scroll input
            current_index = self.scroll_states.index(self.scroll_mode)
            if y > 0:  # Scroll up
                new_index = max(0, current_index - 1)
            else:      # Scroll down
                new_index = min(len(self.scroll_states) - 1, current_index + 1)
            self.scroll_mode = self.scroll_states[new_index]

            # Update the player's direction to reflect the new scroll mode
            base_direction = self.direction.split("_")[0]  # Extract current base direction
            if self.scroll_mode != "middle":
                self.direction = f"{base_direction}_{self.scroll_mode}"
            else:
                self.direction = base_direction        # Smooth depth transition towards target_depth
        if self.depth != self.target_depth:
            # Determine direction and maximum change for this frame
            direction = 1 if self.target_depth > self.depth else -1
            max_change = self.depth_transition_speed * delta_time

            # Calculate actual change while respecting max speed
            desired_change = self.target_depth - self.depth
            actual_change = max(-max_change, min(max_change, desired_change))

            # Apply change and ensure we stay within bounds
            old_depth = self.depth
            self.depth += actual_change
            self.depth = min(self.max_scroll_depth, max(self.min_scroll_depth, self.depth))

            # If we have a target, adjust depth relative to it
            if self.auto_follow_active and self.auto_follow_target:
                star_min_depth = self.auto_follow_target.depth - self.depth_buffer
                star_max_depth = self.auto_follow_target.depth + self.depth_buffer
                self.depth = min(star_max_depth, max(star_min_depth, self.depth))

            return self.depth - old_depth

        return 0.0

    def _update_position(self):
        """
        Updates player position with toroidal wrapping.
        Prevents the player from exceeding screen boundaries.
        """
        self.position += self.velocity

        # Toroidal wrapping for X-axis
        if self.position.x < 0:
            self.position.x += WIDTH
            self.position.y = HEIGHT - self.position.y
        elif self.position.x > WIDTH:
            self.position.x -= WIDTH
            self.position.y = HEIGHT - self.position.y

        # Toroidal wrapping for Y-axis
        if self.position.y < 0:
            self.position.y += HEIGHT
            self.position.x = WIDTH - self.position.x
        elif self.position.y > HEIGHT:
            self.position.y -= HEIGHT
            self.position.x = WIDTH - self.position.x

        # Prevent floating-point inaccuracies from causing position issues
        self.position.x = self.position.x % WIDTH
        self.position.y = self.position.y % HEIGHT

    def update_boost(self, delta_time):
        """
        Updates the boost velocity over time, applying decay.

        Args:
            delta_time (float): Time elapsed since the last frame.

        Returns:
            Vector2: Updated velocity including boost.
        """
        if self.boost_duration > 0:
            self.boost_duration -= delta_time
            # Apply decay to the boost velocity
            self.boost_velocity *= self.boost_decay_rate ** delta_time
            if self.boost_duration <= 0:
                self.boost_velocity = Vector2(0, 0)
        return self.velocity + self.boost_velocity
