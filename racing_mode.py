import pygame
import random
import math
from pygame.math import Vector2
from constants import WIDTH, HEIGHT, MIN_DEPTH, MAX_DEPTH

CAPTURE_RADIUS = 200           # Radius within which a ship can capture the checkpoint
CAPTURE_TIME_REQUIRED = 0.5   # 0.5 seconds needed to capture
WIN_SCORE = 3                 # First to 3 captures wins

class RacingMode:
    def __init__(self, player, enemies, screen):
        """
        Initializes the King of the Hill racing mode with one shared checkpoint.
        
        Args:
            player (Player): The player object.
            enemies (list): List of enemy ship objects.
            screen (pygame.Surface): The game screen surface for drawing.
        """
        self.player = player
        self.enemies = enemies
        self.screen = screen

        # Score tracking for player and all enemies
        self.scores = {"player": 0}
        for i, enemy in enumerate(enemies):
            self.scores[f"enemy_{i}"] = 0

        # Single checkpoint with (x, y, depth) plus capture logic
        self.checkpoint_pos = Vector2(0, 0)
        self.checkpoint_depth = 1
        self.respawn_checkpoint()

        # Track who is capturing the checkpoint
        self.current_controller = None
        self.capture_timer = 0.0
        self.race_active = False
        self.race_finished = False

    def respawn_checkpoint(self):
        """Randomly place the shared checkpoint at a new 3D location (world space)."""
        x = random.uniform(0, WIDTH)
        y = random.uniform(0, HEIGHT)
        depth = random.uniform(MIN_DEPTH, MAX_DEPTH)
        self.checkpoint_pos = Vector2(x, y)
        self.checkpoint_depth = depth
        self.current_controller = None
        self.capture_timer = 0.0

    def start_race(self):
        """Start the King of the Hill race."""
        self.race_active = True
        self.race_finished = False
        for key in self.scores:
            self.scores[key] = 0
        self.respawn_checkpoint()
        print("King of the Hill Race Started! First to 3 captures wins.")

    def update(self, dt, player_velocity, depth_change):
        """Update checkpoint position, depth, and capture logic."""
        if not self.race_active or self.race_finished:
            return

        # === Update Checkpoint Based on Player Movement ===
        parallax_factor = 1.0 / max(self.checkpoint_depth, MIN_DEPTH)
        movement = player_velocity * parallax_factor * dt
        self.checkpoint_pos -= movement

        # Apply depth changes if player zooms
        self.checkpoint_depth += depth_change
        if self.checkpoint_depth < MIN_DEPTH:
            self.checkpoint_depth = MAX_DEPTH - (MIN_DEPTH - self.checkpoint_depth)
        elif self.checkpoint_depth > MAX_DEPTH:
            self.checkpoint_depth = MIN_DEPTH + (self.checkpoint_depth - MAX_DEPTH)

        # === Check if player or enemies are capturing ===
        candidate_controller = self._check_ships_in_radius()
        if candidate_controller is None:
            self.current_controller = None
            self.capture_timer = 0.0
        else:
            if self.current_controller == candidate_controller:
                self.capture_timer += dt
                if self.capture_timer >= CAPTURE_TIME_REQUIRED:
                    self.scores[candidate_controller] += 1
                    print(f"{candidate_controller} captured the checkpoint! Score: {self.scores[candidate_controller]}")
                    self.respawn_checkpoint()
            else:
                self.current_controller = candidate_controller
                self.capture_timer = dt

    def _check_ships_in_radius(self):
        """Check which ship is in the checkpoint radius (player or AI)."""
        player_dist = (self.player.position - self.checkpoint_pos).length()
        depth_diff_player = abs(self.player.depth - self.checkpoint_depth)
        if player_dist <= CAPTURE_RADIUS and depth_diff_player < 0.2:
            return "player"

        for i, enemy in enumerate(self.enemies):
            dist = (enemy.position - self.checkpoint_pos).length()
            depth_diff_enemy = abs(enemy.depth - self.checkpoint_depth)
            if dist <= CAPTURE_RADIUS and depth_diff_enemy < 0.2:
                return f"enemy_{i}"
        
        return None

    def draw(self):
        """Draw the checkpoint, score, progress bar, and depth for debugging."""
        if not self.race_active:
            return

        # === Calculate Checkpoint Position and Size Based on Depth ===
        parallax_factor = 1.0 / max(self.checkpoint_depth, MIN_DEPTH)
        on_screen_x = self.checkpoint_pos.x * parallax_factor
        on_screen_y = self.checkpoint_pos.y * parallax_factor
        checkpoint_radius = max(10, CAPTURE_RADIUS * parallax_factor)

        # === Draw the Checkpoint Circle ===
        pygame.draw.circle(self.screen, (255, 255, 0), (int(on_screen_x), int(on_screen_y)), int(checkpoint_radius), 2)

        # === Draw Capture Progress Arc (if capturing) ===
        if self.current_controller is not None:
            progress_ratio = min(self.capture_timer / CAPTURE_TIME_REQUIRED, 1.0)
            start_angle = -math.pi / 2
            end_angle = start_angle + 2 * math.pi * progress_ratio
            arc_rect = [
                on_screen_x - checkpoint_radius,
                on_screen_y - checkpoint_radius,
                checkpoint_radius * 2,
                checkpoint_radius * 2
            ]
            pygame.draw.arc(self.screen, (0, 255, 0), arc_rect, start_angle, end_angle, 4)

        # === Draw Checkpoint Depth for Debugging ===
        font = pygame.font.SysFont(None, 24)  # Smaller font for debug info
        depth_text = f"z = {self.checkpoint_depth:.2f}"  # Show 2 decimal places of depth
        depth_text_surface = font.render(depth_text, True, (255, 255, 255))  # White text
        text_x = on_screen_x - depth_text_surface.get_width() // 2  # Center it
        text_y = on_screen_y + checkpoint_radius + 5  # Position it below the checkpoint
        self.screen.blit(depth_text_surface, (text_x, text_y))  # Render the text on the screen

        # === Draw the Scoreboard ===
        font = pygame.font.SysFont(None, 36)
        y_offset = 10
        for racer_id, score in self.scores.items():
            text_str = f"{racer_id}: {score}"
            text_surf = font.render(text_str, True, (255, 255, 255))
            self.screen.blit(text_surf, (10, y_offset))
            y_offset += 30
