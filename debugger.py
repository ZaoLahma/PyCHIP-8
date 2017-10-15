#!/usr/bin/env python3

from cpu import NUM_REGISTERS

class debugger(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.activated = False
        self.pc = 1
        self.prevPc = 0

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
            self.cpu.executing = False
        self.pc = self.cpu.pc
