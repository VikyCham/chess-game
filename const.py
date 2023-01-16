import pygame
# Screen dimensions
WIDTH = 512
HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = HEIGHT

# Board dimensions
DIMENSIONS = 8
SQSIZE = WIDTH // DIMENSIONS

MAX_FPS = 15
IMAGES = {}

ALPHACOLS = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}

'''
Initilize a global dictionary of images.
'''

def loadImages():
    pieces = ["wp", "wR", "wN", "wB", "wQ", "wK", "bp", "bR", "bN", "bB", "bQ", "bK"]

    for piece in pieces:
        IMAGES[piece] = pygame.image.load('assets/images/' + piece + ".png")