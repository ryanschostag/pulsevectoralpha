import pygame

PIXEL_COLORS = {
    1: (180, 180, 190), 
    2: (150, 150, 165),
    3: (120, 120, 140),  
    4: (140, 140, 160),  
    5: (80, 127, 222), 
    6: (127, 222, 255),
    7: (0, 0, 255)  
}

RAW_SPACESHIP_SHAPES = {
    # Standard Directions
    "up": """
0002000
0022200
0223220
0225220
0022200
0002000
""",
    "down": """
0002000
0022200
0225220
0223220
0022200
0002000
""",
    "left": """
0000200
0002220
0022522
0223220
0002220
0000200
""",
    "right": """
0020000
0222000
2252200
0223220
0222000
0020000
""",
    "up-right": """
000220
002222
022522
022522
002220
000220
""",
    "up-left": """
022000
222220
225520
225520
222220
022000
""",
    "down-right": """
000220
002222
022522
022522
002220
000220
""",
    "down-left": """
220000
222220
225520
225520
222220
022000
""",

    # Outward Variants (Slightly Angled Outward)
    "up_outward": """
0003300
0033330
0335330
3355330
0033330
0003300
""",
    "down_outward": """
0003300
0033330
0335330
3355330
0033330
0003300
""",
    "left_outward": """
0000030
0003330
0033533
0333330
0003330
0000030
""",
    "right_outward": """
0030000
0333000
3353300
0333330
0333000
0030000
""",
    "up-right_outward": """
000330
003333
033533
033533
003333
000330
""",
    "up-left_outward": """
033000
333330
335530
335530
333330
033000
""",
    "down-right_outward": """
000330
003333
033533
033533
003333
000330
""",
    "down-left_outward": """
330000
333330
335530
335530
333330
033000
""",

    # Inward Variants (Slightly Angled Inward)
    "up_inward": """
0004400
0044440
0445540
4444440
0044440
0004400
""",
    "down_inward": """
0004400
0044440
0445540
4444440
0044440
0004400
""",
    "left_inward": """
0000040
0004440
0044644
0444440
0004440
0000040
""",
    "right_inward": """
0040000
0444000
4464400
0444440
0444000
0040000
""",
    "up-right_inward": """
000440
004444
044644
044444
004444
000440
""",
    "up-left_inward": """
044000
444440
446640
444440
444440
044000
""",
    "down-right_inward": """
000440
004444
044644
044444
004444
000440
""",
    "down-left_inward": """
440000
444440
446640
444440
444440
044000
""",
}

PIXEL_SIZE = 5

# spaceship.py
def draw_spaceship(surface, matrix, position, scale_factor=1, color_override=None):
    x, y = position
    pixel_size = int(PIXEL_SIZE * scale_factor)  # Scale the pixel size
    for row_index, row in enumerate(matrix):
        for col_index, pixel in enumerate(row):
            if pixel in PIXEL_COLORS:
                # Use override color if provided, otherwise default to PIXEL_COLORS
                color = color_override if color_override else PIXEL_COLORS.get(pixel, (255, 255, 255))
                if not isinstance(color, tuple) or len(color) < 3 or not all(0 <= c <= 255 for c in color):
                    color = (255, 255, 255)  # Default to white if color is invalid
                pygame.draw.rect(
                    surface,
                    color,
                    (
                        x + col_index * pixel_size,
                        y + row_index * pixel_size,
                        pixel_size,
                        pixel_size,
                    ),
                )

SPACESHIP_SHAPES = {
    direction: [
        [int(char) for char in row.strip()]
        for row in shape.strip().split("\n")
    ]
    for direction, shape in RAW_SPACESHIP_SHAPES.items()
}
