#!/usr/bin/env python3

import pygame

SCREEN_X_SIZE = 200
SCREEN_Y_SIZE = 200

class gpu(object):
    def __init__(self):
        pygame.init()
        pygame.display.set_mode((SCREEN_X_SIZE, SCREEN_Y_SIZE))
        self.surface = pygame.Surface ((SCREEN_X_SIZE, SCREEN_Y_SIZE), pygame.HWSURFACE)
        pygame.display.flip()
