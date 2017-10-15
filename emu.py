#!/usr/bin/env python3

from rom import rom
from cpu import cpu
from debugger import debugger

class emu(object):
    def __init__(self):
        self.rom = rom()
        self.cpu = cpu()
        self.debugger = debugger(self.cpu)
        self.debugger.activate()

    def run(self, binPath):
        self.rom.load(binPath)
        self.cpu.run(self.rom.romData, self.debugger)
