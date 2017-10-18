#!/usr/bin/env python3

import pygame
from rom import Rom
from cpu import Cpu
from gpu import Gpu
from debugger import Debugger

class Emu(object):
    def __init__(self, debug, graphicsScale):
        self.rom = Rom()
        self.gpu = Gpu(graphicsScale)
        self.cpu = Cpu(self.gpu)
        self.gpu.setCpu(self.cpu)
        self.debugger = None
        self.debugger = Debugger(self.cpu)
        if True == debug:
            self.debugger.activate()

    def run(self, binPath):
        self.rom.load(binPath)
        self.cpu.execProg(self.rom.romData, self.debugger)
        self.pyGameMainLoop()

    def pyGameMainLoop(self):
        while 1:
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                keysPressed = pygame.key.get_pressed()
                self.cpu.keyboard.keyPressedIndication(keysPressed)
                if keysPressed[pygame.K_q]:
                    self.cpu.stop()
            if event.type == pygame.QUIT:
                self.cpu.stop()

            if False == self.cpu.running:
                raise SystemExit
