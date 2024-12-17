import pygame
from constants import *

def get_direction(keys_pressed, BASE_DIRECTION_MAP):
    dx = keys_pressed[pygame.K_d] - keys_pressed[pygame.K_a]
    dy = keys_pressed[pygame.K_s] - keys_pressed[pygame.K_w]
    return BASE_DIRECTION_MAP.get((dx, dy)) if (dx, dy) != (0, 0) else None

def draw_box(surface, position, size, color, thickness=2):
    half_size = size // 2
    quarter_size = size // 4
    x, y = position.x, position.y
    lines = [
        ((x - half_size, y - half_size), (x - half_size + quarter_size, y - half_size)),
        ((x - half_size, y - half_size), (x - half_size, y - half_size + quarter_size)),
        ((x + half_size, y - half_size), (x + half_size - quarter_size, y - half_size)),
        ((x + half_size, y - half_size), (x + half_size, y - half_size + quarter_size)),
        ((x - half_size, y + half_size), (x - half_size + quarter_size, y + half_size)),
        ((x - half_size, y + half_size), (x - half_size, y + half_size - quarter_size)),
        ((x + half_size, y + half_size), (x + half_size - quarter_size, y + half_size)),
        ((x + half_size, y + half_size), (x + half_size, y + half_size - quarter_size)),
    ]
    for start_pos, end_pos in lines:
        pygame.draw.line(surface, color, start_pos, end_pos, thickness)
