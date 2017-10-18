#!/usr/bin/env python3

import pygame

SCREEN_X_SIZE = 64
SCREEN_Y_SIZE = 32

COLORS = (pygame.Color(192, 192, 192, 255),
          pygame.Color(100, 80, 255, 255))

class Gpu(object):
    def __init__(self, scale):
        self.cpu = None
        self.scale = scale
        if None == self.scale:
            self.scale = 1
        pygame.display.init()
        self.display = pygame.display.set_mode((SCREEN_X_SIZE * self.scale, SCREEN_Y_SIZE * self.scale))

        pygame.display.set_caption("PyCHIP-8")

        self.surface = pygame.Surface((SCREEN_X_SIZE * self.scale,
                                       SCREEN_Y_SIZE * self.scale),
                                       pygame.HWSURFACE | pygame.DOUBLEBUF,
                                       8)
        self.surface.fill(COLORS[0])
        self.display.blit(self.surface, (0, 0))
        pygame.display.flip()

    def drawPixel(self, xPos, yPos, color):
        xStart = xPos * self.scale
        yStart = yPos * self.scale
        pygame.draw.rect(self.surface,
                         COLORS[color],
                         (xStart, yStart, self.scale, self.scale))

    def render(self):
        self.display.blit(self.surface, (0, 0))
        pygame.display.flip()

    def setCpu(self, cpu):
        self.cpu = cpu
