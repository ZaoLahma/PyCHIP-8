#!/usr/bin/env python3

from cpu import NUM_REGISTERS
from cpu import U16_MAX
from cpu import PRG_START_ADDR

STEP = 0xFFFFFFFF

class debugger(object):
    def __init__(self, cpu):
        self.cpu = cpu
        self.activated = False
        self.pc = U16_MAX
        self.breakpoint = PRG_START_ADDR

    def activate(self):
        self.activated = True

    def trace(self):
        if True == self.activated:
            if None != self.breakpoint:
                if self.cpu.pc == self.breakpoint or STEP == self.breakpoint:
                    print("Execution halted at " + hex(self.cpu.pc))
                    print("Enter next breakpoint, \"step\" or \"run\" followed by enter to continue execution: ")
                    self.breakpoint = input()
                    if "step" == self.breakpoint or "s" == self.breakpoint:
                        self.breakpoint = STEP
                    elif "run" == self.breakpoint or "r" == self.breakpoint:
                        self.breakpoint = None
                    else:
                        try:
                            self.breakpoint = int(self.breakpoint, 16)
                            print("New breakpoint: " + hex(self.breakpoint))
                        except ValueError:
                            self.breakpoint = STEP
            print("Registers: ")
            for i in range(NUM_REGISTERS):
                print("V[" + hex(i) + "] = " + hex(self.cpu.V[i]))
            print("I: " + hex(self.cpu.I))
            print("PC: " + hex(self.cpu.pc))
            print("SP: " + hex(self.cpu.sp))
            instr = self.cpu.ram[self.cpu.pc] << 8 | self.cpu.ram[self.cpu.pc + 1]
            print("Next instruction: " + hex(instr))

            if self.pc == self.cpu.pc:
                print("Execution hanging at " + hex(self.cpu.pc))
                self.cpu.stop()
            self.pc = self.cpu.pc
