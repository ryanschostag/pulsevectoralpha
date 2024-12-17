# enemy.py

import pygame
import random
import math
from pygame.math import Vector2
from constants import *
from spaceship import draw_spaceship
from bullet import Bullet

DEPTH_FIRE_THRESHOLD = 0.25
FIRE_DISTANCE_THRESHOLD = 222

def interpolate_path(current_pos, target_pos, t):
    """
    Returns an interpolated position along the path.
    Args:
        current_pos (Vector2): Current position of the enemy.
        target_pos (Vector2): Target star's position.
        t (float): Interpolation factor between 0 and 1.
    Returns:
        Vector2: Interpolated position.
    """
    return current_pos.lerp(target_pos, t)

def draw_health_bar(surface, position, health, max_health, scale_factor=1.0):
    """
    Draws a health bar at the given position, scaling it according to the enemy's size.

    Args:
        surface (pygame.Surface): The surface to draw on.
        position (Vector2): The position to draw the health bar.
        health (int): Current health of the enemy.
        max_health (int): Maximum health of the enemy.
        scale_factor (float): The scale factor to adjust the size of the health bar.
    """
    health_ratio = health / max_health
    bar_width = 40 * scale_factor  # Width of the health bar, scales with enemy size
    bar_height = 6 * scale_factor  # Height of the health bar, scales with enemy size
    
    # Position the health bar above the enemy's position
    bar_x = position.x - bar_width // 2
    bar_y = position.y - 20 * scale_factor  # 20 pixels above the enemy (adjust as necessary)
    
    # Draw the border of the health bar
    border_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(surface, (255, 0, 0), border_rect)  # Red border
    
    # Draw the current health as a green bar
    health_rect = pygame.Rect(bar_x, bar_y, bar_width * health_ratio, bar_height)
    pygame.draw.rect(surface, (0, 255, 0), health_rect)  # Green fill

MAX_DEPTH_SCALE = 2

class TypeDEnemy:
    """
    An enemy type that moves through 3D space, transitioning between stars based on strategic decisions.
    Implements smooth depth management and dynamic orbital behaviors.
    """
    
    # Refined depth management constants
    DEPTH_BUFFER = 0.0  # Buffer zone at boundaries
    
    # Calculated depth boundaries
    MIN_DEPTH_BOUNDARY = MIN_DEPTH + DEPTH_BUFFER
    MAX_DEPTH_BOUNDARY = MAX_DEPTH - DEPTH_BUFFER
    MIN_DEPTH_BUFFER = MIN_DEPTH
    MAX_DEPTH_BUFFER = MAX_DEPTH
    # Constants for orbital behavior
    ORBIT_TRANSITION_CHANCE = 0.5  # 2% chance per update to check for new star
    MIN_ORBIT_TIME = 2.0  # Minimum time to stay in orbit (seconds)
    MAX_ORBIT_DISTANCE = 255  # Maximum distance to consider new star
    
    def __init__(self, stars, enemies):
        """Initialize the enemy with improved orbital transition management."""
        self.position = Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.direction = Vector2(1, 0).rotate(random.uniform(0, 360))
        self.speed = 20
        self.depth = random.uniform(self.MIN_DEPTH_BUFFER, self.MAX_DEPTH_BUFFER)
        self.target_depth = self.depth
        self.velocity = self.direction * self.speed
        self.stars = stars
        self.orbit_star = None
        self.target_star = None  # **The new target star to move towards**
        self.size = 5
        self.fire_rate = 2.0  # Fire a bullet every 2 seconds
        self.last_shot_time = 0
        self.current_radius = 5
        # Movement personalization parameters
        self.movement_traits = {
            'phase_offset': random.uniform(0, 2 * math.pi),  # Unique starting phase
            'lateral_frequency': random.uniform(0.8, 1.4),   # Individual lateral oscillation rate
            'vertical_frequency': random.uniform(0.7, 1.2),  # Individual vertical oscillation rate
            'wander_frequency': random.uniform(0.9, 1.3),    # Personal wander rate
            'turn_bias': random.uniform(0.8, 1.2),          # Individual turning preference
        }
        
        self.orbit_radius = 45
        self.orbit_angle = 0
        self.state = 'normal'
        self.base_direction = "up"
        self.ship_color = (random.randint(55, 255), random.randint(55, 255), random.randint(55, 255))
        self.turn_rate = 45  # **Degrees per second**
        self.relative_velocity = Vector2(0, 0)  # Tracks relative velocity with respect to player
        self.enemies = enemies 
        self.enemy_lock_probability = 0.5  # 20% chance to check for better enemy target
        self.switching_cooldown = 2.0  # Cooldown (in seconds) before switching targets
        self.switching_timer = 0
        self.target_enemy = None
        self.orbit_target = None
        self.alive = True
        self.type = "enemy"
        self.health = 25
        self.max_health = 25

    def find_next_target(self):
        """
        Predicts and selects the next target for smoother transitions.
        Prioritizes locking onto stars or enemy ships.
        """
        if not self.stars and not self.enemies:
            self.target_enemy = None
            self.target_star = None
            self.state = 'normal'  # Explicitly return to normal state if no targets found
            return None

        forward_direction = self.direction.normalize()
        candidates = []

        # **Check for potential stars to lock onto**
        for star in self.stars:
            if star == self.orbit_target:  # Ignore current target
                continue
            dx = min(abs(star.position.x - self.position.x), WIDTH - abs(star.position.x - self.position.x))
            dy = min(abs(star.position.y - self.position.y), HEIGHT - abs(star.position.y - self.position.y))
            distance = math.sqrt(dx**2 + dy**2)
            star_dir = Vector2(dx, dy).normalize()
            alignment_score = forward_direction.dot(star_dir)
            candidates.append(("star", alignment_score, distance, star))

        # **Check for potential enemy ships to lock onto**
        for enemy in self.enemies:
            if enemy == self or enemy == self.target_enemy:  # Ignore self and current target
                continue
            dx = min(abs(enemy.position.x - self.position.x), WIDTH - abs(enemy.position.x - self.position.x))
            dy = min(abs(enemy.position.y - self.position.y), HEIGHT - abs(enemy.position.y - self.position.y))
            distance = math.sqrt(dx**2 + dy**2)
            enemy_dir = Vector2(dx, dy).normalize()
            alignment_score = forward_direction.dot(enemy_dir)
            candidates.append(("enemy", alignment_score, distance, enemy))

        # **Prioritize the best target (star or enemy)**
        if candidates:
            candidates.sort(key=lambda x: (-x[1], x[2]))  # Sort by (-alignment_score, distance)
            best_type, best_alignment, best_distance, best_target = candidates[0]

            if best_type == "star":
                self.target_star = best_target
                self.target_enemy = None
                self.orbit_target = best_target
                self.target_depth = best_target.depth

            elif best_type == "enemy":
                self.target_enemy = best_target
                self.target_star = None
                self.orbit_target = best_target
                self.target_depth = best_target.depth

            self.state = 'transitioning'  # Ensure state is set to transitioning
            return best_target

        # **If no targets are found, clear current targets and return to normal state**
        self.target_enemy = None
        self.target_star = None
        self.orbit_target = None
        self.state = 'normal'  # Explicitly set state to normal
        return None

    def stop_orbiting(self):
        """
        Cleanly transitions out of orbital state when depth wrapping occurs.
        Ensures proper state management during depth transitions.
        """
        self.state = 'normal'
        self.orbit_star = None
        self.target_star = None
        self.orbit_target = None  # Ensure orbit_target is reset
        self.find_next_target()  # Find a new target to avoid drifting
    
    def update(self, dt, player_depth, player_velocity, player_depth_change, global_depth_change=0, checkpoint_pos=None, checkpoint_depth=None):
        """
        Updates enemy state with enhanced star and enemy ship transition logic.
        """
        if checkpoint_pos is not None:
            # If at checkpoint, handle like orbit logic
            self.orbit_target = None
            self.target_star = None
            self.target_enemy = None
        
        # Store old depth for wrap detection
        old_depth = self.depth
        
        # Update relative motion based on player velocity
        self.update_relative_motion(player_velocity, dt)
        self.update_direction(dt)

        # Reduce switching cooldown timer
        if self.switching_timer > 0:
            self.switching_timer -= dt
        
        # **State Management Logic**
        if self.state == 'normal':
            # Check for new targets if no current targets
            if not self.target_enemy and not self.target_star:
                self.find_next_target()
            self.normal_movement(dt, player_velocity)
            
        elif self.state == 'orbiting' and self.orbit_target:
            better_star = self.find_better_star()
            if better_star:
                self.transition_to_next_star(better_star)
            if self.state == 'orbiting':
                self.orbit_movement(dt)
                
        elif self.state == 'transitioning':
            if self.target_enemy:
                self.approach_orbit(self.target_enemy, dt)
                distance = (self.position - self.target_enemy.position).length()
                if distance < self.orbit_radius:
                    self.start_orbiting(self.target_enemy)
            elif self.target_star:
                self.approach_orbit(self.target_star, dt)
                distance = (self.position - self.target_star.position).length()
                if distance < self.orbit_radius:
                    self.start_orbiting(self.target_star)

        self.depth += global_depth_change + player_depth_change
        self.handle_depth_wrapping(old_depth)
        self.update_base_direction()
        self.smooth_turning(dt)

    def handle_depth_wrapping(self, old_depth=None):
        wrapped = False
        if self.depth < MIN_DEPTH or self.depth > MAX_DEPTH:
            self.depth = (self.depth - MIN_DEPTH) % (MAX_DEPTH - MIN_DEPTH) + MIN_DEPTH
            self.stop_orbiting()  # Reset target after depth wrap
        
        if self.position.x < 0 or self.position.x > WIDTH:
            self.position.x = self.position.x % WIDTH
        if self.position.y < 0 or self.position.y > HEIGHT:
            self.position.y = self.position.y % HEIGHT
            
        if wrapped:
            self.stop_orbiting()
 
    def _get_onscreen_radius(self):
        """
        Returns the radius used for collision detection against bullets.
        """
        # Similar logic: a base radius that shrinks/grows with depth
        return max(5, int(10 / self.depth))
    
    def fire_bullets(self, player_position, player_depth, player_velocity, dt):
        """
        Fires a bullet if player is close enough in 2D distance and depth.
        """
        # --- 1. Check for depth proximity ---
        if abs(self.depth - player_depth) > DEPTH_FIRE_THRESHOLD:
            return None  # Too far in depth to fire

        # --- 2. Check for 2D distance proximity ---
        distance_2d = (self.position - player_position).length()
        if distance_2d > FIRE_DISTANCE_THRESHOLD:
            return None  # Player is too far away in 2D space to fire
        
        # --- 3. Rate-limiting for fire rate ---
        current_time = pygame.time.get_ticks() / 1000.0  # Convert ms to seconds
        if (current_time - self.last_shot_time) > self.fire_rate:
            
            # Decide whether bullet should move inward or outward in depth
            #   If the enemy is deeper (enemy.depth > player_depth), bullet moves 'inward'
            #   If the enemy is shallower (enemy.depth < player_depth), bullet moves 'outward'
            #   If they're nearly the same, just treat it as 'custom' with no depth change
            depth_diff = self.depth - player_depth
            if depth_diff > 0.50:  # a small threshold
                bullet_direction = "outward"
            elif depth_diff < -0.50:
                bullet_direction = "inward"
            else:
                bullet_direction = "middle"  # No depth transition

            # --- 4. Fire bullet towards player position ---
            # Get the player's true world position from the player object
            player_world_position = player_position  # Assume player is passed as an argument to this function
            direction_vector = (player_world_position - self.position).normalize()

            # Add random spread to the bullet's direction
            spread_angle = random.uniform(-0.1, 0.1)  # Random spread between -0.1 and 0.1 radians
            cos_angle = math.cos(spread_angle)
            sin_angle = math.sin(spread_angle)
            
            spread_direction_vector = pygame.math.Vector2(
                direction_vector.x * cos_angle - direction_vector.y * sin_angle,
                direction_vector.x * sin_angle + direction_vector.y * cos_angle
            ).normalize()

            bullet = Bullet(
                position=self.position,
                direction=bullet_direction,
                initial_depth=self.depth,
                spaceship_width=10,
                spaceship_height=10,
                player_velocity=player_velocity,
                player_depth=player_depth,
                is_enemy_bullet=True
            )

            # Set bullet velocity (combines enemy-to-player vector and player's current velocity)
            bullet.velocity = spread_direction_vector * 100 + player_velocity
            bullet.depth = self.depth  # Start at enemy's depth
            self.last_shot_time = current_time  # Update shot timer
            return bullet

        return None  # No bullet fired

    def transition_to_next_star(self, next_target):
        """
        Start moving towards the new target with depth transition.
        
        Args:
            next_target: The target to transition to (can be Star or TypeDEnemy)
        """
        if next_target and next_target != self.orbit_target:
            self.state = 'transitioning'
            
            # Check if target is a star or enemy
            if isinstance(next_target, TypeDEnemy):
                self.target_enemy = next_target
                self.target_star = None
            else:
                self.target_star = next_target
                self.target_enemy = None
                
    def find_better_enemy(self):
        candidates = []

        for i, enemy in enumerate(self.enemies):
            if not hasattr(enemy, 'position') or not hasattr(enemy, 'depth'):
                continue

            if enemy == self:  # Don't lock onto itself
                continue

            dx = min(abs(enemy.position.x - self.position.x), WIDTH - abs(enemy.position.x - self.position.x))
            dy = min(abs(enemy.position.y - self.position.y), HEIGHT - abs(enemy.position.y - self.position.y))
            distance = math.sqrt(dx**2 + dy**2)
            alignment_score = self.direction.normalize().dot((enemy.position - self.position).normalize())

            candidates.append((alignment_score, distance, enemy))

        if candidates:
            candidates.sort(key=lambda x: (-x[0], x[1]))  # Prioritize alignment, then distance
            best_enemy = candidates[0][2]
            return best_enemy

        return None

    def orbit_movement(self, dt):
        """
        Orbit around the orbit target in both 2D space and depth.
        """
        if not self.orbit_target:
            return

        # Calculate the orbit position relative to the orbit target
        orbit_center = self.orbit_target.position

        # Increment orbit angle over time
        self.orbit_angle += 90 * dt  # Rotate 90 degrees per second
        if self.orbit_angle >= 360:
            self.orbit_angle -= 360

        # Calculate new position around the orbit center
        radians = math.radians(self.orbit_angle)
        orbit_offset = Vector2(
            math.cos(radians) * self.orbit_radius,
            math.sin(radians) * self.orbit_radius
        )
        
        # Update position
        self.position = orbit_center + orbit_offset

        # Match depth with orbit target with consistent speed
        target_depth = self.orbit_target.depth
        depth_diff = target_depth - self.depth + global_depth_change  # Include global depth change
        max_depth_change = 0.5 * dt  # Consistent depth change speed
        if abs(depth_diff) > 0.01:  # Only change depth if difference is significant
            depth_change = max(-max_depth_change, min(max_depth_change, depth_diff))
            self.depth += depth_change

    def start_orbiting(self, target):
        """Start orbiting around the target object with proper depth transition."""

        self.orbit_target = target
        self.state = 'orbiting'
        self.orbit_angle = 0
        
        # Set target depth from the target (star or enemy)
        if hasattr(target, 'depth'):
            self.target_depth = target.depth
        
        # Calculate initial orbit radius
        displacement = self.position - target.position
        self.orbit_radius = max(displacement.length(), 32)
        self.orbit_angle = math.degrees(math.atan2(displacement.y, displacement.x))

    def approach_orbit(self, target, dt):
        """Approach target with consistent depth transitions."""
        if not target:
            return

        # Calculate distance to target
        to_target = target.position - self.position
        distance = to_target.length()
        
        if distance < 1:
            return

        # Update direction and movement
        direction_to_target = to_target / distance
        self.direction = self.direction.lerp(direction_to_target, 0.05 * dt)
        
        # Movement speed adjustments
        approach_speed = self.speed
        if distance < self.orbit_radius * 2:
            speed_factor = max(0.2, distance / (self.orbit_radius * 2))
            approach_speed *= speed_factor
        
        # Apply movement
        movement = self.direction * approach_speed * dt
        max_movement = self.speed * dt * 2
        if movement.length() > max_movement:
            movement.scale_to_length(max_movement)
        self.position += movement

        # Handle depth transition during approach
        if hasattr(target, 'depth'):
            depth_diff = target.depth - self.depth
            max_depth_change = 0.5 * dt  # Consistent depth change speed
            if abs(depth_diff) > 0.01:  # Only change depth if difference is significant
                depth_change = max(-max_depth_change, min(max_depth_change, depth_diff))
                self.depth += depth_change

        # Check if we've reached orbit distance
        if distance < self.orbit_radius:
            self.start_orbiting(target)
            
    def find_better_star(self):
        """
        Finds a more suitable star for orbiting, respecting depth boundaries.
        Prioritizes stars within valid depth range.
        
        Returns:
            Star or None: Better star to orbit, or None if current is optimal
        """
        current_depth = self.orbit_star.depth if self.orbit_star else self.depth
        
        suitable_stars = [
            star for star in self.stars
            if (star != self.orbit_star and
                self.MIN_DEPTH_BOUNDARY <= star.depth <= self.MAX_DEPTH_BOUNDARY and
                (star.position - self.position).length() < self.MAX_ORBIT_DISTANCE)
        ]
        
        return min(suitable_stars, key=lambda s: (s.position - self.position).length()) if suitable_stars else None

    def draw(self, surface):
        scale_factor = max(0.5, min(1.5, 1 / self.depth))
        ship_shape = SPACESHIP_SHAPES.get(self.base_direction, SPACESHIP_SHAPES["up"])
        shade_color = tuple(
            int(c * (1 - ((self.depth - MIN_DEPTH) / (MAX_DEPTH - MIN_DEPTH)) * 0.6))
            for c in self.ship_color
        )
        draw_spaceship(surface, ship_shape, self.position, scale_factor, shade_color)

        # Draw health bar if needed
        if self in self.enemies or self in self.tagged_enemies:
            draw_health_bar(surface, self.position, self.health, self.max_health, scale_factor)
        
        '''
        font_size = int(21)# * scale_factor)
        font = pygame.font.SysFont(None, font_size)
        
        depth_text = f"{self.depth:.2f}"   # Show two decimal places
        depth_surf = font.render(depth_text, True, (255, 255, 255))
        
        # Position the text just below the enemy, similar to how the health bar is offset
        text_x = self.position.x - depth_surf.get_width() // 2
        text_y = self.position.y + 15 * scale_factor  # push it a bit below (depends on your art)
        
        surface.blit(depth_surf, (text_x, text_y))'''
        
        
    def smooth_turning(self, dt):
        """
        Gradually rotates the ship to face its intended direction based on current state.
        
        Implements state-aware turning behavior:
        - Orbiting: Turns to face tangential to orbit path
        - Normal: Maintains current direction vector
        - Transitioning: Smoothly interpolates between states
        
        Args:
            dt (float): Delta time for frame-rate independent turning
        """
        if not self.orbit_star:
            # In normal state, maintain current direction
            return
            
        # Calculate desired facing direction when orbiting
        target_vector = (self.orbit_star.position - self.position).normalize()
        target_angle = target_vector.angle_to(Vector2(1, 0))
        
        # Smooth rotation towards target
        angle_difference = (target_angle - self.direction.angle_to(Vector2(1, 0)) + 180) % 360 - 180
        turn_step = min(abs(angle_difference), 180 * dt) * (-1 if angle_difference < 0 else 1)
        self.direction = self.direction.rotate(turn_step)

    def handle_depth_wrapping(self, old_depth=None):
        """
        Wrap the ship's 2D position (x, y) and depth (z-axis) according to inverse logic.
        1. When the ship crosses a screen edge, it appears on the opposite edge, but at the **inverse position**.
        2. When the ship crosses the min or max depth, its depth wraps between MIN_DEPTH and MAX_DEPTH.
        3. When depth is wrapped, the (X, Y) position also inverts.
        """
        wrapped = False  # Track if any wrapping occurred

        # --- 1. X-axis position wrapping (inverse position) ---
        if self.position.x < 0:
            self.position.x += WIDTH  # Wrap to the right
            self.position.y = HEIGHT - self.position.y  # Invert Y
            self.depth = MAX_DEPTH - self.depth  # Invert depth
            wrapped = True
        elif self.position.x > WIDTH:
            self.position.x -= WIDTH  # Wrap to the left
            self.position.y = HEIGHT - self.position.y  # Invert Y
            self.depth = MAX_DEPTH - self.depth  # Invert depth
            wrapped = True

        # --- 2. Y-axis position wrapping (inverse position) ---
        if self.position.y < 0:
            self.position.y += HEIGHT  # Wrap to the bottom
            self.position.x = WIDTH - self.position.x  # Invert X
            self.depth = MAX_DEPTH - self.depth  # Invert depth
            wrapped = True
        elif self.position.y > HEIGHT:
            self.position.y -= HEIGHT  # Wrap to the top
            self.position.x = WIDTH - self.position.x  # Invert X
            self.depth = MAX_DEPTH - self.depth  # Invert depth
            wrapped = True

        # --- 3. Depth wrapping (inverse depth) ---
        if self.depth < MIN_DEPTH:
            self.depth = MAX_DEPTH - (MIN_DEPTH - self.depth)  # Wrap from min depth to max depth
            self.position.x = WIDTH - self.position.x  # Invert X
            self.position.y = HEIGHT - self.position.y  # Invert Y
            wrapped = True
        elif self.depth > MAX_DEPTH:
            self.depth = MIN_DEPTH + (self.depth - MAX_DEPTH)  # Wrap from max depth to min depth
            self.position.x = WIDTH - self.position.x  # Invert X
            self.position.y = HEIGHT - self.position.y  # Invert Y
            wrapped = True

        if wrapped:
            self.stop_orbiting()

    def update_direction(self, dt):
        """
        Updates direction with individualized movement patterns.
        Each enemy maintains unique turning characteristics while preserving
        purposeful movement behavior.
        """
        if not self.orbit_target:
            # No orbit target available, so skip orbiting logic.
            return
        
        if self.velocity.length() == 0:
            return

        # Individual time-based variations
        personal_time = (pygame.time.get_ticks() * 0.01 + self.movement_traits['phase_offset'])
        
        # Personalized turn rate calculation
        base_turn_rate = self.turn_rate * self.movement_traits['turn_bias']
        variation_factor = math.sin(personal_time * self.movement_traits['wander_frequency']) * 0.5 + 0.5
        current_turn_rate = base_turn_rate * (0.8 + variation_factor * 0.4)
        
        if self.state == 'orbiting':
            # Orbital movement with individual characteristics
            orbit_tangent = (self.orbit_target.position - self.position).normalize().rotate(90)
            target_direction = orbit_tangent
        else:
            # Individualized wandering behavior
            wander_strength = 0.3
            wander_offset = Vector2(
                math.sin(personal_time * self.movement_traits['lateral_frequency']),
                math.cos(personal_time * self.movement_traits['vertical_frequency'])
            ) * wander_strength
            
            target_direction = (self.velocity.normalize() + wander_offset).normalize()

        # Calculate turning angles
        current_angle = math.atan2(self.direction.y, self.direction.x)
        target_angle = math.atan2(target_direction.y, target_direction.x)
        angle_diff = (target_angle - current_angle + math.pi) % (2 * math.pi) - math.pi
        
        # Apply personalized turning
        max_turn = math.radians(current_turn_rate) * dt
        turn_amount = max(-max_turn, min(max_turn, angle_diff))
        
        new_angle = current_angle + turn_amount
        self.direction = Vector2(math.cos(new_angle), math.sin(new_angle))
        
        if self.state != 'orbiting':
            self.velocity = self.direction * self.speed

    def normal_movement(self, dt, player_velocity):
        """
        Implements individualized normal movement patterns.
        Each enemy follows its own unique trajectory while maintaining
        smooth and natural motion.
        """
        # Personal time-based modulation
        personal_time = pygame.time.get_ticks() * 0.01 + self.movement_traits['phase_offset']
        
        # Individual trajectory adjustments
        lateral_offset = math.sin(personal_time * self.movement_traits['lateral_frequency']) * 0.3
        vertical_offset = math.cos(personal_time * self.movement_traits['vertical_frequency']) * 0.3
        
        trajectory_adjustment = Vector2(lateral_offset, vertical_offset)
        adjusted_velocity = self.velocity + trajectory_adjustment * self.speed
        
        # Movement with parallax
        parallax_factor = 2.0 / max(self.depth, MIN_DEPTH)
        movement = (adjusted_velocity * parallax_factor * dt)
        
        # Movement limiting
        max_movement = self.speed * 2 * dt
        if movement.length() > max_movement:
            movement.scale_to_length(max_movement)
        
        self.position += movement
        self.position -= player_velocity * parallax_factor * dt

    def update_relative_motion(self, player_velocity, dt):
        """
        Updates relative motion and applies parallax effect to the enemy's position.
        """
        self.relative_velocity = self.velocity - player_velocity
        parallax_factor = 2.0 / max(self.depth, MIN_DEPTH)
        relative_movement = self.relative_velocity * parallax_factor * dt
        self.position += relative_movement

    def update_base_direction(self):
        """
        Updates the ship's sprite to face its movement direction.
        """
        angle = self.direction.angle_to(Vector2(1, 0))
        self.base_direction = self.get_base_direction(angle)

    def get_base_direction(self, angle):
        """
        Converts a movement angle to a sprite direction.
        """
        directions = ["right", "down-right", "down", "down-left", "left", "up-left", "up", "up-right"]
        adjusted_angle = angle % 360
        direction_index = int((adjusted_angle + 22.5) / 45) % 8
        return directions[direction_index]
