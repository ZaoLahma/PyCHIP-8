#!/usr/bin/env python3

from rom import rom
from cpu import cpu
from gpu import gpu
from debugger import debugger

GRAPHICS_SCALE = 20

class emu(object):
    def __init__(self, debug):
        self.rom = rom()
        self.gpu = gpu(GRAPHICS_SCALE)
        self.cpu = cpu(self.gpu)
        self.debugger = None
        if True == debug:
            self.debugger = debugger(self.cpu)
            self.debugger.activate()

    def run(self, binPath):
        self.rom.load(binPath)
        self.cpu.execProg(self.rom.romData, self.debugger)
        self.gpu.pyGameMainLoop()
