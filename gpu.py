#!/usr/bin/env python3

import pygame

SCREEN_X_SIZE = 64
SCREEN_Y_SIZE = 32

COLORS = (pygame.Color(0, 0, 0, 255),
          pygame.Color(255, 255, 255, 255))

class gpu(object):
    def __init__(self, scale):
        self.scale = scale
        pygame.display.init()
        self.display = pygame.display.set_mode((SCREEN_X_SIZE * scale, SCREEN_Y_SIZE * scale))

        pygame.display.set_caption("PyCHIP-8")

        self.surface = pygame.Surface((SCREEN_X_SIZE * scale,
                                       SCREEN_Y_SIZE * scale),
                                       pygame.HWSURFACE | pygame.DOUBLEBUF,
                                       8)
        self.surface.fill(pygame.Color(0, 0, 0, 255))
        self.display.blit(self.surface, (0, 0))
        pygame.display.flip()

    def drawPixel(self, xPos, yPos, color):
        x_base = xPos * self.scale
        y_base = yPos * self.scale
        #print("Drawing pixel at " + hex(xPos) + ", " + hex(yPos) + ". Color: " + str(COLORS[color]))
        pygame.draw.rect(self.surface,
                         COLORS[color],
                         (x_base, y_base, self.scale, self.scale))

    def render(self):
        self.display.blit(self.surface, (0, 0))
        pygame.display.flip()

    def pyGameMainLoop(self):
        while 1:
            event = pygame.event.wait ()
            if event.type == pygame.QUIT:
                raise SystemExit
