#!/usr/bin/env python3

RAM_SIZE              = 4096
U8_MAX                = 0xFF
U16_MAX               = 0xFFFF
NUM_REGISTERS         = 0x10
NUM_INSTRUCTIONS      = 0x10

NUM_0x8_INSTRUCTIONS  = 0x9

PRG_START_ADDR        = 0x200

OPCODE_MASK           = 0xF0
ARG_HIGH_MASK         = 0x0F
ARG_LOW_MASK          = 0xF0
OPCODE_LOW_MASK       = 0x0F

class instruction(object):
    def __init__(self, func, numSubInstructions = 0, illInstr = None):
        self.handle = func
        self.subInstructions = []
        for i in range(numSubInstructions):
            self.subInstructions.append(instruction(illInstr))

class instructionSet(object):
    def __init__(self):
        self.instructions = [None] * NUM_INSTRUCTIONS
        for i in range(NUM_INSTRUCTIONS):
            self.instructions[i] = instruction(self.illegalInstr)

        self.instructions[0x6] = instruction(self.execLdReg)
        self.instructions[0x8] = instruction(self.exec8XY, NUM_0x8_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0x8].subInstructions[0x0] = instruction(self.execAssignXY)
        self.instructions[0xA] = instruction(self.execSetI)

    def illegalInstr(self, cpu):
        print("Illegal instruction at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

    def execLdReg(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        print("reg: " + hex(reg))
        cpu.V[reg] = cpu.ram[cpu.pc + 1]
        cpu.pc += 2

    def exec8XY(self, cpu):
        subInstruction = (cpu.ram[cpu.pc + 1] & OPCODE_LOW_MASK)
        if subInstruction != 0xE:
            self.instructions[0x8].subInstructions[subInstruction].handle(cpu)
        else:
            self.illegalInstr(cpu)
        cpu.pc += 2

    def execAssignXY(self, cpu):
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        cpu.V[regX] = cpu.V[regY]
        print("Assigned reg " + hex(regX) + " to reg " + hex(regY))

    def execSetI(self, cpu):
        val = ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]
        cpu.I = val
        cpu.pc += 2

    def execGoto(self, cpu):
        addr = ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]
        cpu.pc = addr

class cpu(object):
    def __init__(self):
        self.ram = [U8_MAX] * RAM_SIZE
        self.V = [U16_MAX] * NUM_REGISTERS
        self.I = U16_MAX
        self.pc = PRG_START_ADDR
        self.sp = 0
        self.running = False
        self.instructionSet = instructionSet()

    def run(self, bin):
        byteAddr = 0
        for byte in bin:
            self.ram[PRG_START_ADDR + byteAddr] = byte
            byteAddr += 1

        self.running = True
        while self.running:
            op = (self.ram[self.pc] & OPCODE_MASK) >> 4
            print("op: " + hex(op) + " (" + str(op) + ")")
            self.instructionSet.instructions[op].handle(self)
