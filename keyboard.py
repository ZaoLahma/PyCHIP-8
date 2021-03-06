#!/usr/bin/env python3

import pygame
import threading

KEYS = {
    0x0: pygame.K_KP0,
    0x1: pygame.K_KP1,
    0x2: pygame.K_KP2,
    0x3: pygame.K_KP3,
    0x4: pygame.K_KP4,
    0x5: pygame.K_KP5,
    0x6: pygame.K_KP6,
    0x7: pygame.K_KP7,
    0x8: pygame.K_KP8,
    0x9: pygame.K_KP9,
    0xA: pygame.K_a,
    0xB: pygame.K_b,
    0xC: pygame.K_c,
    0xD: pygame.K_d,
    0xE: pygame.K_e,
    0xF: pygame.K_f,
}

class Keyboard(object):
    def __init__(self):
        self.pressedKeys = None
        self.pressedKeysCond = threading.Condition()

    def keyPressed(self, keyToCheck):
        retVal = False
        pressedKeys = pygame.key.get_pressed()
        if pressedKeys[KEYS[keyToCheck]]:
            retVal = True
        return retVal

    def keyPressedIndication(self, pressedKeys):
        with self.pressedKeysCond:
            self.pressedKeys = pressedKeys
            self.pressedKeysCond.notifyAll()

    def waitKeyPressed(self):
        keyVal = None
        keyPressed = False
        while not keyPressed:
            with self.pressedKeysCond:
                self.pressedKeysCond.wait()
                for keyVal, lookupKey in KEYS.items():
                    if self.pressedKeys[lookupKey]:
                        keyPressed = True
                        break
        return keyVal
