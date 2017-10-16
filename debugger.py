#!/usr/bin/env python3

from cpu import NUM_REGISTERS
from cpu import U16_MAX

class debugger(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.activated = False
        self.pc = U16_MAX

    def activate(self):
        self.activated = True

    def trace(self):
        if True == self.activated:
            print("Registers: ")
            for i in range(NUM_REGISTERS):
                print("V[" + hex(i) + "] = " + hex(self.cpu.V[i]))
            print("I: " + hex(self.cpu.I))
            print("PC: " + hex(self.cpu.pc))
            print("SP: " + hex(self.cpu.sp))
        if self.pc == self.cpu.pc:
            print("Execution hanging at " + hex(self.cpu.pc))
            self.cpu.stop()
        self.pc = self.cpu.pc
