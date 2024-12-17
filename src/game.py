# game.py

import pygame
import random
from pygame.math import Vector2
import math
from constants import *
from star import *
from player import *
from bullet import *
from utils import *
from enemy import *
from spaceship import *
from racing_mode import *
import settings

FLAME_SCALE = settings.game.flame_scale
MAX_FLAME_LENGTH = settings.game.max_flame_length

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN if FULLSCREEN else 0)
        pygame.display.set_caption("Pulse Vector")
        self.clock = pygame.time.Clock()
        self.running = settings.game.default_running_state
        self.player = Player()
        self.stars = [
            Star(
                random.uniform(0, WIDTH),
                random.uniform(0, HEIGHT),
                random.uniform(MIN_DEPTH, MAX_DEPTH)
            ) for _ in range(NUM_STARS)
        ]
        self.target_star = None
        self.bullets = []
        self.enemy_total = settings.game.enemy_total
        self.enemies = []
        for _ in range(self.enemy_total):
            enemy = TypeDEnemy(self.stars, self.enemies)
            self.enemies.append(enemy)
        self.last_shot_time = 0
        self.fire_delay = settings.game.fire_delay

        pygame.event.set_allowed([
            pygame.QUIT,
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEWHEEL
        ])
        self.current_orbital_velocity = 0.0
        self.current_orbital_direction = Vector2(0, -1)
        self.depth_change = 0
        self.target_enemy = None
        self.target_enemy_index = -1  # Initialize with -1 indicating no target
        self.tagged_enemies = set()  # Keep track of tagged enemies
        self.tag_timer = 0  # Timer to track player proximity for tagging
        self.race = None 
        self.lock_timer = 0
        self.lock_on_duration = settings.game.lock_on_duration
        self.lock_indicator_color = settings.game.lock_indicator_color

    def cycle_target_enemy(self, forward=True):
        """Cycles the target_enemy_index to the next enemy."""
        if not self.enemies:
            return  # No enemies to cycle through

        if self.target_enemy not in self.enemies:
            # If no enemy is currently targeted, start from the first or last based on direction
            self.target_enemy_index = 0 if forward else len(self.enemies) - 1
        else:
            # Cycle forward or backward
            if forward:
                self.target_enemy_index = (self.target_enemy_index + 1) % len(self.enemies)
            else:
                self.target_enemy_index = (self.target_enemy_index - 1) % len(self.enemies)

        # Set the new target_enemy
        self.target_enemy = self.enemies[self.target_enemy_index]
        self.target_star = None  # Clear any star target
        print(f"Target enemy set to {self.target_enemy}. Auto-Follow remains {'ON' if self.player.auto_follow_active else 'OFF'}.")

    def draw_hud(self):
        """Draws the game's HUD including player health, enemy status, and auto-follow status."""
        font = pygame.font.SysFont(None, 36)  # Font for the HUD text

        # 1. **Player Health Bar (Top-Left)**
        player_health_ratio = self.player.health / self.player.max_health
        health_bar_width = 200
        health_bar_height = 20
        health_bar_x = 10
        health_bar_y = 10

        # Draw the border of the health bar
        pygame.draw.rect(self.screen, (255, 0, 0), 
                         (health_bar_x, health_bar_y, health_bar_width, health_bar_height))  # Red border

        # Draw the actual health amount inside the bar
        pygame.draw.rect(self.screen, (0, 255, 0), 
                         (health_bar_x, health_bar_y, int(health_bar_width * player_health_ratio), health_bar_height))  # Green fill

        # Display player's health as text
        player_health_text = f"Health: {self.player.health} / {self.player.max_health}"
        health_text_surface = font.render(player_health_text, True, (255, 255, 255))  # White text
        self.screen.blit(health_text_surface, (health_bar_x, health_bar_y + health_bar_height + 5))  # Slightly below health bar

        # 2. **Tagged Enemies Count (Top-Center)**
        tagged_count = len(self.tagged_enemies)
        total_enemies = len(self.enemies)
        tagged_text = f"Tagged Enemies: {tagged_count} / {total_enemies}"
        tagged_text_surface = font.render(tagged_text, True, (255, 255, 255))  # White text
        self.screen.blit(tagged_text_surface, (WIDTH // 2 - tagged_text_surface.get_width() // 2, 10))  # Centered at the top

        # 3. **Auto-Follow Status (Bottom-Left)**
        if self.player.auto_follow_active and isinstance(self.player.auto_follow_target, TypeDEnemy):
            follow_text = "Auto-pilot: ON"
            follow_color = (0, 255, 0)  # Green
        else:
            follow_text = "Auto-pilot: OFF"
            follow_color = (255, 0, 0)  # Red

        follow_surface = font.render(follow_text, True, follow_color)
        self.screen.blit(follow_surface, (10, HEIGHT - 50))  # Bottom-left corner

        # 4. **Lock-On Status (Bottom-Center)**
        if self.target_enemy is not None:
            lock_status_text = f"Target: {self.target_enemy.type}"
            lock_status_color = (0, 255, 0)  # Green if locked on
        else:
            lock_status_text = "No Target"
            lock_status_color = (255, 0, 0)  # Red if no lock-on target

        lock_status_surface = font.render(lock_status_text, True, lock_status_color)
        self.screen.blit(lock_status_surface, (WIDTH // 2 - lock_status_surface.get_width() // 2, HEIGHT - 50))  # Bottom-center

    def draw_scene(self):
        """
        Implements a precise depth-based rendering system that correctly interleaves
        world objects based on their distance from the viewer.
        """
        self.screen.fill((0, 0, 0))

        # Unified collection for all world objects
        world_objects = []
        player_depth = self.player.depth  # Get the player's current depth

        # Add all world objects with consistent depth values
        for star in self.stars:
            world_objects.append({
                'depth': star.depth,
                'object': star,
                'type': 'star',
                'is_target': star == self.target_star
            })

        for enemy in self.enemies:
            world_objects.append({
                'depth': enemy.depth - player_depth,
                'object': enemy,
                'type': 'enemy'
            })

        # Separate bullets into "far" and "shallow" based on player depth
        far_bullets = []
        shallow_bullets = []
        for bullet in self.bullets:
            if bullet.depth > player_depth:
                far_bullets.append({
                    'depth': bullet.depth,
                    'object': bullet,
                    'type': 'bullet'
                })
            else:
                shallow_bullets.append({
                    'depth': bullet.depth,
                    'object': bullet,
                    'type': 'bullet'
                })

     # Sort by depth (ascending) - this ensures furthest objects draw first
        world_objects.sort(key=lambda x: x['depth'])
        for obj_info in world_objects:
            obj = obj_info['object']
            obj_type = obj_info['type']
            if obj_type == 'star':
                obj.draw(self.screen)
            elif obj_type == 'enemy':
                obj.draw(self.screen)
                if obj == self.target_enemy:  # Highlight targeted enemy
                    # Calculate radius of the target circle
                    circle_radius = max(20, 50 / obj.depth)  # Dynamic size based on depth

                    # Calculate player position (center of screen)
                    player_pos = Vector2(WIDTH // 2, HEIGHT // 2)

                    # Calculate distance from player to the enemy
                    distance_to_target = (obj.position - player_pos).length()

                    if obj in self.tagged_enemies:
                        # If the enemy is already tagged, draw a full green circle
                        circle_color = (0, 255, 0)
                        pygame.draw.circle(self.screen, circle_color, (int(obj.position.x), int(obj.position.y)), int(circle_radius), 2)
                    else:
                        # Change color to green if the player is inside the circle, else red
                        circle_color = (0, 255, 0) if distance_to_target <= circle_radius else (255, 0, 0)
                        pygame.draw.circle(self.screen, circle_color, (int(obj.position.x), int(obj.position.y)), int(circle_radius), 2)

                        # Draw progress bar if within proximity
                        if distance_to_target <= circle_radius:
                            progress_ratio = self.tag_timer / 1000.0  # Assuming tag_timer is in milliseconds
                            progress_ratio = min(max(progress_ratio, 0.0), 1.0)  # Clamp between 0 and 1
                            start_angle = -math.pi / 2  # Start at the top
                            end_angle = start_angle + (2 * math.pi * progress_ratio)
                            pygame.draw.arc(
                                self.screen,
                                (0, 255, 0),  # Green color for progress
                                [
                                    int(obj.position.x - circle_radius),
                                    int(obj.position.y - circle_radius),
                                    int(circle_radius * 2),
                                    int(circle_radius * 2)
                                ],
                                start_angle,
                                end_angle,
                                4  # Thickness of the arc
                            )

        self.draw_hud()  # Draw the HUD

        far_bullets.sort(key=lambda x: x['depth'])  # Sort far bullets by depth
        shallow_bullets.sort(key=lambda x: x['depth'])  # Sort shallow bullets by depth

        # Draw far bullets first
        #player_hitbox_color = (0, 0, 255)  # Default to blue for player hitbox
        for obj_info in reversed(far_bullets):  # Reverse to draw background first
            obj = obj_info['object']
            obj.draw(self.screen)
            '''
            bullet_hitbox_radius = obj.get_collision_radius()
            bullet_hitbox_rect = pygame.Rect(
                bullet.position.x - bullet_hitbox_radius,
                bullet.position.y - bullet_hitbox_radius,
                bullet_hitbox_radius * 2,
                bullet_hitbox_radius * 2
            )
            
            # Draw bullet's hitbox (default yellow)
            bullet_hitbox_color = (255, 255, 0)

            # Calculate player's hitbox
            player_radius = 5
            player_hitbox_rect = pygame.Rect(
                (WIDTH // 2) - player_radius, 
                (HEIGHT // 2) - player_radius, 
                player_radius * 2, 
                player_radius * 2
            )
            
            # Check for intersection of bullet and player hitboxes
            if player_hitbox_rect.colliderect(bullet_hitbox_rect):
                # Check if the depths are within range
                depth_difference = abs(self.player.depth - obj.depth)
                if depth_difference < BULLET_DEPTH_HIT_TOLERANCE:  # Check if bullet is within hit depth
                    bullet_hitbox_color = (255, 255, 0)  # Change bullet hitbox color to yellow
                    player_hitbox_color = (255, 255, 0)  # Change player hitbox color to yellow
                    
            pygame.draw.rect(self.screen, bullet_hitbox_color, bullet_hitbox_rect, 2)  # Draw bullet hitbox
            '''
            pass

        # Draw all world objects (e.g., stars, enemies)
        for obj_info in reversed(world_objects):  # Reverse to draw background first
            obj = obj_info['object']
            obj_type = obj_info['type']

            if obj_type == 'star':
                obj.draw(self.screen)
                if obj_info['is_target']:
                    box_size = max(1, int(obj.size / obj.depth)) * 8
                    draw_box(self.screen, obj.position, box_size, TARGET_COLOR)
            elif obj_type == 'enemy':
                obj.draw(self.screen)

        # Draw player flame if in "outward" scroll mode (BEHIND the ship)
        if self.player.scroll_mode == 'outward':
            ship_center = Vector2(WIDTH // 2, HEIGHT // 2)
            boosted_velocity = self.player.update_boost(0)
            self.draw_flame(ship_center, self.player.direction, boosted_velocity)

        # Draw player ship (UI layer)
        spaceship_shape = SPACESHIP_SHAPES.get(self.player.direction, SPACESHIP_SHAPES["up"])
        spaceship_width = len(spaceship_shape[0]) * PIXEL_SIZE
        spaceship_height = len(spaceship_shape) * PIXEL_SIZE
        spaceship_position = ((WIDTH - spaceship_width) // 2, (HEIGHT - spaceship_height) // 2)

        draw_spaceship(self.screen, spaceship_shape, spaceship_position)
        '''debug stuff
        # Draw player hitbox
        player_radius = 14
        player_hitbox_rect = pygame.Rect(
            (WIDTH // 2) - player_radius, 
            (HEIGHT // 2) - player_radius, 
            player_radius * 2, 
            player_radius * 2
        )
        pygame.draw.rect(self.screen, player_hitbox_color, player_hitbox_rect, 2)  # Draw player hitbox
        '''
        # Draw player depth below player ship
        #font = pygame.font.SysFont(None, 24)
        #depth_text = f"Depth: {self.player.depth:.2f}, x:{self.player.position}"
        #depth_surface = font.render(depth_text, True, (255, 255, 255))
        #depth_x = WIDTH // 2 - depth_surface.get_width() // 2
        #depth_y = HEIGHT // 2 + player_radius + 10
        #self.screen.blit(depth_surface, (depth_x, depth_y))

        # Draw flame if not in "outward" scroll mode (AFTER ship)
        if self.player.scroll_mode != 'outward':
            ship_center = Vector2(WIDTH // 2, HEIGHT // 2)
            boosted_velocity = self.player.update_boost(0)
            self.draw_flame(ship_center, self.player.direction, boosted_velocity)

        # Draw shallow bullets after the player
        for obj_info in reversed(shallow_bullets):  # Reverse to draw background first
            obj = obj_info['object']
            obj.draw(self.screen)
            '''
            bullet_hitbox_radius = obj.get_collision_radius()
            bullet_hitbox_rect = pygame.Rect(
                bullet.position.x - bullet_hitbox_radius,
                bullet.position.y - bullet_hitbox_radius,
                bullet_hitbox_radius * 2,
                bullet_hitbox_radius * 2
            )

            # Draw bullet hitbox (yellow for visibility)
            bullet_hitbox_color = (255, 255, 0)
            pygame.draw.rect(self.screen, bullet_hitbox_color, bullet_hitbox_rect, 2)
        
            if player_hitbox_rect.colliderect(bullet_hitbox_rect):
                depth_difference = abs(self.player.depth - obj.depth)
                if depth_difference < BULLET_DEPTH_HIT_TOLERANCE:
                    bullet_hitbox_color = (255, 255, 0)
                    player_hitbox_color = (255, 255, 0)

            #pygame.draw.rect(self.screen, bullet_hitbox_color, bullet_hitbox_rect, 2)  # Draw bullet hitbox
            '''
            pass
        
    def handle_mouse_click(self, position):
        """
        Handles mouse clicks to select a target star.
        The click must be directly on the star (inside its visual radius).
        Clicking out of a star untargets only the star.
        
        Args:
            position (Vector2): The position of the mouse click.
            
        Returns:
            bool: True if a star was clicked, False otherwise.
        """
        # Find all stars where the click is inside the star's visual radius
        clicked_stars = [
            star for star in self.stars 
            if (star.position - position).length() <= max(1, int(star.size / star.depth))
        ]
        
        if clicked_stars:
            # Select the closest star that was actually clicked
            clicked_star = min(clicked_stars, key=lambda star: (star.position - position).length())
            self.target_star = clicked_star
            print(f"Star {clicked_star} selected. Enemy target is preserved.")
            return True

        # If no star is clicked, only untarget the star
        if self.target_star:
            print(f"Star {self.target_star} untargeted via click out.")
            self.player.handle_target_release(self.target_star, self.current_orbital_velocity)
            self.target_star = None

        # Do not untarget the enemy on click out
        return False

    def run(self):
        racing = False
        while self.running:
            delta_time = self.clock.tick(60) / 1000.0  # Get time since last frame
            player_position = Vector2(WIDTH // 2, HEIGHT // 2)  # Center of the screen (where player ship is)
            player_depth = self.player.depth  # Get player's depth
            self.delta_time = delta_time  # Store delta_time globally for use in lock-on logic

            # Handle events and input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:  # Cycle lock-on
                        if event.mod & pygame.KMOD_SHIFT:
                            self.cycle_target_enemy(forward=False)  # Cycle backward
                        else:
                            self.cycle_target_enemy(forward=True)  # Cycle forward
                    elif event.key == pygame.K_f:  # Lock-on / auto-follow toggle
                        if self.player.auto_follow_active:
                            self.player.disable_auto_follow()
                        else:
                            if self.target_enemy and self.target_enemy in self.tagged_enemies:
                                self.player.enable_auto_follow(self.target_enemy)
                            else:
                                print("Auto-Follow can only be enabled for tagged enemies.")
                    elif event.key == pygame.K_r:
                        # Start the King of the Hill race:
                        self.race = RacingMode(self.player, self.enemies, self.screen)
                        self.race.start_race()
                        racing = True
                        print("King of the Hill Mode activated!")
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        clicked_position = Vector2(event.pos)
                        self.handle_mouse_click(clicked_position)
                    elif event.button == 3:  # Right click (remove lock-on)
                        self.target_enemy = None
                        self.target_star = None
                        self.player.disable_auto_follow()
                        self.tag_timer = 0  # Reset tagging timer
                elif event.type == pygame.MOUSEWHEEL:
                    self.player.handle_wheel(event.y, delta_time)
                    
            # === Player Input ===
            depth_delta = self.center_zoom(delta_time)
            depth_change = depth_delta
            depth_change += self.player.handle_input(delta_time)
            self.handle_continuous_fire()
            self.player.update_scroll_mode()

            if racing and self.race:
                self.race.update(delta_time, self.player.velocity, depth_change)

            # === Check Lock-on and Bullet Hits ===
            self.check_proximity_to_target(delta_time)
            #self.check_enemy_wrap()

            # === Update All Game Objects ===
            # Update player position, depth, and movement
            boosted_velocity = self.player.update_boost(delta_time)
            
            # Update all stars
            for star in self.stars:
                star.update(boosted_velocity, depth_change, delta_time, star is self.target_star)
            
            # Update all bullets (player and enemy bullets)
            for bullet in self.bullets:
                bullet.update(delta_time)

            # Update All Enemies
            new_bullets = [] 
            if racing and self.race:
                checkpoint_pos = self.race.checkpoint_pos
                checkpoint_depth = self.race.checkpoint_depth
            else:
                checkpoint_pos = None
                checkpoint_depth = None

            for enemy in self.enemies:
                enemy.update(
                    delta_time,
                    self.player.depth,
                    self.player.velocity,
                    depth_change,
                    global_depth_change=0,
                    checkpoint_pos=checkpoint_pos,
                    checkpoint_depth=checkpoint_depth
                )
                bullet = enemy.fire_bullets(Vector2(WIDTH // 2, HEIGHT // 2), player_depth, self.player.velocity, delta_time)
                if bullet:
                    new_bullets.append(bullet)
            self.bullets.extend(new_bullets)  # Add newly fired bullets to bullet list
            self.update_collisions()
            # === Render the Scene ===
            self.draw_scene()
            if racing and self.race:
                self.race.draw()
            pygame.display.flip()
            
    def check_enemy_wrap(self):
        """Check if the locked enemy wraps and lose lock if they do."""
        if self.locked_enemy:
            if self.locked_enemy.position.x < 0 or self.locked_enemy.position.x > WIDTH:
                print("Enemy wrapped! Lock lost.")
                self.locked_enemy = None
            if self.locked_enemy.position.y < 0 or self.locked_enemy.position.y > HEIGHT:
                print("Enemy wrapped! Lock lost.")
                self.locked_enemy = None
                
    def check_proximity_to_target(self, delta_time):
        """Check if player is within proximity to tag the target."""
        target = self.target_star or self.target_enemy
        if target:
            player_pos = Vector2(WIDTH // 2, HEIGHT // 2)
            distance_to_target = (target.position - player_pos).length()
            if target.type == 'star' or target.type == 'enemy':
                circle_radius = max(20, 50 / target.depth)
            else:
                circle_radius = 20  # Default radius

            if distance_to_target <= circle_radius:
                self.tag_timer += delta_time * 1000  # Convert delta_time to milliseconds
                if self.tag_timer >= 1000:  # 1 second to tag
                    if target.type == 'enemy' and target not in self.tagged_enemies:
                        self.tagged_enemies.add(target)  # Add enemy to tagged set
                        print(f"Enemy {target} tagged!")  # Print only the first time
                    # Do not set auto-follow here
                    self.tag_timer = 0  # Reset timer after tagging
            else:
                self.tag_timer = 0
                
    def update_collisions(self):
        """
        Checks every bullet for collisions with player or enemies and applies damage.
        Removes bullets and/or kills enemies if health drops to zero.
        """
        bullets_to_remove = []
        enemies_to_remove = []

        for bullet in self.bullets:
            if not bullet.alive:
                # Already flagged for removal in bullet.update() if out-of-bounds or expired
                bullets_to_remove.append(bullet)
                continue

            # If it's an enemy bullet, check collision with player
            if bullet.is_enemy_bullet:
                if bullet.check_collision(self.player):
                    # Apply damage to the player
                    damage_amount = 1
                    self.player.health -= damage_amount

                    # Mark bullet for removal
                    bullet.alive = False
                    bullets_to_remove.append(bullet)

                    # If player's health is depleted
                    if self.player.health <= 0:
                        print("Player is destroyed!")
                        # Handle game-over logic here
                    continue  # No need to check other collisions for this bullet

            else:
                # It's a player bullet, check collision with enemies
                for enemy in self.enemies:
                    if not enemy.alive:
                        continue
                    if bullet.check_collision(enemy):
                        # Apply damage to the enemy
                        damage_amount = 1  # Example
                        enemy.health -= damage_amount

                        # Mark bullet for removal
                        bullet.alive = False
                        bullets_to_remove.append(bullet)

                        # If enemy's health is depleted
                        if enemy.health <= 0:
                            enemy.alive = False
                            enemies_to_remove.append(enemy)
                        break  # Stop checking more enemies once bullet hits something

        # Remove dead bullets
        self.bullets = [b for b in self.bullets if b.alive and b not in bullets_to_remove]

        # Remove dead enemies
        self.enemies = [e for e in self.enemies if e.alive and e not in enemies_to_remove]
    
    def handle_continuous_fire(self):
        """Fires a bullet every x milliseconds if the spacebar is held"""
        keys_pressed = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        if keys_pressed[pygame.K_SPACE]:
            if current_time - self.last_shot_time >= self.fire_delay:
                self.fire_bullet()
                self.last_shot_time = current_time

    def fire_bullet(self):
        direction = self.player.direction
        if self.player.scroll_mode == "outward":
            direction = f"{self.player.direction}_outward"
        bullet_position = Vector2(WIDTH // 2, HEIGHT // 2)
        spaceship_shape = SPACESHIP_SHAPES.get(self.player.direction, SPACESHIP_SHAPES["up"])
        spaceship_width = len(spaceship_shape[0]) * PIXEL_SIZE
        spaceship_height = len(spaceship_shape) * PIXEL_SIZE
        
        # Pass player's velocity to bullet
        bullet = Bullet(
            bullet_position, 
            direction, 
            self.player.depth, 
            spaceship_width, 
            spaceship_height, 
            self.player.velocity
        )
        self.bullets.append(bullet)
         
    def draw_flame(self, ship_center, direction, boosted_velocity):
        """
        Draws an animated flame behind the ship with dynamics based on speed and position.

        Args:
            ship_center (Vector2): The center position of the ship.
            direction (str): The current direction the ship is facing (e.g., "up", "left", "down", etc.).
            boosted_velocity (Vector2): The velocity vector of the player's boost.
        """
        speed = boosted_velocity.length()
        if speed < 0.1:  # If the player isn't moving, no need to draw the flame
            return

        # Get the base direction and its corresponding vector
        base_direction = direction.split('_')[0] if '_' in direction else direction
        dir_vector = Vector2(DIRECTION_VECTORS[base_direction]).normalize()

        # Calculate the base flame length
        flame_length = min(speed * FLAME_SCALE, MAX_FLAME_LENGTH)

        # Adjust flame length and offset for 'middle' scroll mode
        if self.player.scroll_mode == 'middle':
            flame_length *= 1.25  # Slightly longer flame in middle mode
            ship_offset = dir_vector * -19  # Offset flame slightly behind the ship
        else:
            ship_offset = dir_vector * -5  # Standard offset for other modes

        flame_direction = -dir_vector  # Flame points in the opposite direction of the ship's movement

        segments = 20  # Number of segments in the flame
        current_time = pygame.time.get_ticks()  # Get current time for wave effects

        for i in range(segments):
            t = i / segments  # This defines the distance along the flame (from 0 to 1)

            # Sinusoidal wave to give the flame a "flickering" effect
            wave_offset = math.sin(current_time * 0.005 + i) * 2  # Wavy flicker effect
            segment_pos = (
                ship_center
                + ship_offset  # Offset flame behind ship
                + flame_direction * (flame_length * t) 
                + Vector2(wave_offset, 0)
            )

            # Color gradient from cyan (0,255,255) to blue (0,0,255) as you move away from the ship
            r = 0
            g = int(255 - (255 * t))  # Green decreases as distance increases
            b = 255  # Blue remains constant
            color = (r, g, b)

            # Flame size gets smaller further from the ship (radius shrinks as t increases)
            radius = int(5 - 3 * t)

            # Draw the flame segment as a small circle
            pygame.draw.circle(self.screen, color, (int(segment_pos.x), int(segment_pos.y)), radius)

    def center_zoom(self, delta_time):
        """
        Adjusts the star field (and enemies, bullets, etc.) when a star or enemy is targeted,
        creating a smooth zooming and orbital effect.
        """
        target = self.target_star
        if self.player.auto_follow_active:
            target = self.target_enemy

        if target is None:
            return 0.0

        center = Vector2(WIDTH / 2, HEIGHT / 2)
        to_center = center - target.position
        distance = to_center.length()

        # Smoothly move the entire scene relative to the locked target
        move_speed = min(4.0, max(1.0, distance / WIDTH))  # Dynamic speed based on distance
        displacement = to_center * move_speed * delta_time

        # Apply the same camera displacement to all stars
        for star in self.stars:
            star.position += displacement

        for enemy in self.enemies:
            enemy.position += displacement

        for bullet in self.bullets:
            bullet.position += displacement

        # Adjust depth to smoothly move the target toward MIN_DEPTH
        target_depth = MIN_DEPTH + 0.1
        depth_diff = target_depth - target.depth
        zoom_speed = 1.0
        depth_delta = depth_diff * zoom_speed * delta_time

        return depth_delta

def draw_health_bar(surface, position, health, max_health, width=50, height=5):
    """Draws a health bar at the given position."""
    health_ratio = health / max_health
    border_rect = pygame.Rect(position.x - width // 2, position.y - 20, width, height)
    health_rect = pygame.Rect(position.x - width // 2, position.y - 20, int(width * health_ratio), height)
    pygame.draw.rect(surface, (255, 0, 0), border_rect)  # Border
    pygame.draw.rect(surface, (0, 255, 0), health_rect)  # Health fill

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
