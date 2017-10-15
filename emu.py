#!/usr/bin/env python3

from rom import rom
from cpu import cpu

class emu(object):
    def __init__(self):
        self.rom = rom()
        self.cpu = cpu()

    def run(self, binPath):
        self.rom.load(binPath)
        self.cpu.run(self.rom.romData)
