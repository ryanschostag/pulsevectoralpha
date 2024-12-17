# constants.py

import pygame

global_depth_change = 0
DEPTH_COLLISION_TOLERANCE = 0.001
WIDTH, HEIGHT = 1920, 1080
FULLSCREEN = False
NUM_STARS = 127
PLAYER_SPEED = 10
DEPTH_RATE = .01
MIN_DEPTH = .01
MAX_DEPTH = 2.0
BULLET_MAX_DEPTH = 10.0
STAR_COLOR = (255, 255, 255)
TARGET_COLOR = (255, 0, 0)
# Speed modifiers for bullet types
NEUTRAL_BULLET_SPEED_MOD = 1  # 50% of the original distance for 2D bullets
INWARD_BULLET_SPEED_MOD = 1.0   # Full distance for inward-moving bullets
OUTWARD_BULLET_SPEED_MOD = 1.0  # Full distance for outward-moving bullets
PIXEL_SIZE = 10
# Define pixel colors for the spaceship
pixel_colors = {
    1: (57, 255, 20),   # NEON_GREEN
    2: (0, 255, 255),   # CYAN
    3: (255, 20, 147),  # NEON_PINK
}

def draw_spaceship(surface, matrix, position, scale=1.0, color=(255, 255, 255), rotation=0):
    """
    Draws a spaceship with one pixel colored cyan, rotated based on the direction.

    Args:
        surface: Pygame surface to draw on.
        matrix: 2D list representing the spaceship shape.
        position: Tuple (x, y) for the spaceship position.
        scale: Scaling factor for the spaceship size.
        color: Base color for the spaceship.
        rotation: Rotation angle in degrees.
    """
    # Create a new surface for rotation
    rows = len(matrix)
    cols = len(matrix[0]) if rows > 0 else 0
    ship_width = cols * PIXEL_SIZE * scale
    ship_height = rows * PIXEL_SIZE * scale
    ship_surface = pygame.Surface((ship_width, ship_height), pygame.SRCALPHA)

    # Draw the ship on the ship_surface
    for row_index, row in enumerate(matrix):
        for col_index, pixel in enumerate(row):
            if pixel in pixel_colors:
                color_pixel = pixel_colors[pixel]
                pygame.draw.rect(
                    ship_surface,
                    color_pixel,
                    (
                        col_index * PIXEL_SIZE * scale,
                        row_index * PIXEL_SIZE * scale,
                        PIXEL_SIZE * scale,
                        PIXEL_SIZE * scale,
                    ),
                )

    # **Rotate the ship_surface by adding 180 degrees to the rotation**
    rotated_ship = pygame.transform.rotate(ship_surface, -rotation + 180)  # Added 180 degrees

    # Get the new rect and set its center to the desired position
    rotated_rect = rotated_ship.get_rect(center=position)

    # Blit the rotated ship onto the main surface
    surface.blit(rotated_ship, rotated_rect.topleft)
    
# Updated RAW_SPACESHIP_SHAPES to include multiple colors:
RAW_SPACESHIP_SHAPES = {
    "up": """
    020
    121
    010
    030
    """,
    "down": """
    030
    010
    121
    020
    """,
    "left": """
    0000
    0110
    1120
    0130
    """,
    "right": """
    0000
    0210
    0012
    0310
    """,
    "up-right": """
    010
    120
    012
    001
    """,
    "up-left": """
    010
    012
    120
    100
    """,
    "down-right": """
    001
    012
    120
    010
    """,
    "down-left": """
    100
    120
    012
    010
    """,

    "up_inward": """
    010
    101
    020
    030
    """,
    "down_inward": """
    030
    020
    101
    010
    """,
    "left_inward": """
    0000
    1020
    0100
    1030
    """,
    "right_inward": """
    0000
    1020
    0010
    1030
    """,
    "up-right_inward": """
    010
    101
    102
    001
    """,
    "up-left_inward": """
    010
    101
    201
    100
    """,
    "down-right_inward": """
    001
    201
    101
    010
    """,
    "down-left_inward": """
    100
    101
    201
    010
    """,

    "up_outward": """
    010
    020
    010
    030
    """,
    "down_outward": """
    030
    010
    020
    010
    """,
    "left_outward": """
    0000
    0101
    0200
    0101
    """,
    "right_outward": """
    0000
    0102
    0010
    0103
    """,
    "up-right_outward": """
    010
    010
    020
    001
    """,
    "up-left_outward": """
    010
    020
    010
    100
    """,
    "down-right_outward": """
    001
    010
    020
    010
    """,
    "down-left_outward": """
    100
    010
    020
    010
    """,
}

# Convert raw string shapes to matrices using comprehensions
SPACESHIP_SHAPES = {
    direction: [
        [int(char) for char in row.strip()]
        for row in shape.strip().split("\n")
    ]
    for direction, shape in RAW_SPACESHIP_SHAPES.items()
}
BASE_DIRECTION_MAP = {
    (0, -1): "up",
    (0, 1): "down",
    (-1, 0): "left",
    (1, 0): "right",
    (1, -1): "up-right",
    (-1, -1): "up-left",
    (1, 1): "down-right",
    (-1, 1): "down-left"
}

DIRECTION_VECTORS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
    "up-right": (1, -1),
    "up-left": (-1, -1),
    "down-right": (1, 1),
    "down-left": (-1, 1),
}

def wrap_depth(depth):
    """
    Wrap the depth value so that going beyond MAX_DEPTH restarts at MIN_DEPTH (and vice versa).
    """
    return MIN_DEPTH + (depth - MIN_DEPTH) % ((MAX_DEPTH*100) - MIN_DEPTH)
