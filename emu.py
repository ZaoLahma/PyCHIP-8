#!/usr/bin/env python3

from rom import Rom
from cpu import Cpu
from gpu import Gpu
from debugger import Debugger

GRAPHICS_SCALE = 20

class Emu(object):
    def __init__(self, debug):
        self.rom = Rom()
        self.gpu = Gpu(GRAPHICS_SCALE)
        self.cpu = Cpu(self.gpu)
        self.gpu.setCpu(self.cpu)
        self.debugger = None
        self.debugger = Debugger(self.cpu)        
        if True == debug:
            self.debugger.activate()

    def run(self, binPath):
        self.rom.load(binPath)
        self.cpu.execProg(self.rom.romData, self.debugger)
        self.gpu.pyGameMainLoop()
