#!/usr/bin/env python3

import threading

U8_MAX                = 0xFF
U16_MAX               = 0xFFFF

RAM_SIZE              = 4096
VRAM_SIZE             = 64 * 32

NUM_REGISTERS         = 0x10

NUM_INSTRUCTIONS      = 0x10
NUM_0x8_INSTRUCTIONS  = 0x9

PRG_START_ADDR        = 0x200

OPCODE_MASK           = 0xF0
ARG_HIGH_MASK         = 0x0F
ARG_LOW_MASK          = 0xF0

SPRITE_WIDTH          = 0x8

NUM_INTERRUPTS        = 0x2
SIG_ILL_INSTR         = 0x0
SIG_DRAW_GRAPHICS     = 0x1

class Instruction(object):
    def __init__(self, func, numSubInstructions = 0, illInstr = None):
        self.handle = func
        self.subInstructions = []
        for i in range(numSubInstructions):
            self.subInstructions.append(Instruction(illInstr))

class InstructionSet(object):
    def __init__(self):
        self.instructions = [None] * NUM_INSTRUCTIONS
        for i in range(NUM_INSTRUCTIONS):
            self.instructions[i] = Instruction(self.illegalInstr)

        self.instructions[0x1] = Instruction(self.execJump)
        self.instructions[0x6] = Instruction(self.execLdReg)
        self.instructions[0x8] = Instruction(self.exec8XY, NUM_0x8_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0x8].subInstructions[0x0] = Instruction(self.execAssignXY)
        self.instructions[0xA] = Instruction(self.execSetI)
        self.instructions[0xD] = Instruction(self.execRendering)

    def illegalInstr(self, cpu):
        cpu.interrupt = SIG_ILL_INSTR

    def execJump(self, cpu):
        addr = ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]
        cpu.pc = addr

    def execLdReg(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        print("reg: " + hex(reg))
        cpu.V[reg] = cpu.ram[cpu.pc + 1]
        cpu.pc += 2

    def exec8XY(self, cpu):
        subInstruction = (cpu.ram[cpu.pc + 1] & ARG_HIGH_MASK)
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

    def execSetVram(self, xStartPos, yStartPos, num_bytes, cpu):
        for yIndex in range(num_bytes):
            cpu.V[0xF] = 0
            pixByte = bin(cpu.ram[cpu.I + yIndex])
            pixByte = pixByte[2:].zfill(8)
            yCoord = yStartPos + yIndex
            yCoord = yCoord % 32

            for xIndex in range(8):

                xCoord = xStartPos + xIndex
                xCoord = xCoord % 64

                pixVal = int(pixByte[xIndex])
                # Set pixel to new pix val XOR old pix val
                oldPixVal = cpu.vram[xCoord * yCoord]
                if pixVal == 1 and oldPixVal == 1:
                    cpu.V[0xF] = cpu.V[0xF] | 1
                    pixVal = 0
                elif pixVal == 0 and oldPixVal == 1:
                    pixVal = 1

                cpu.vram[xCoord * yCoord] = pixVal
                cpu.gpu.drawPixel(xCoord, yCoord, pixVal)


    def execRendering(self, cpu):
        regXPos = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regYPos = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        xPos = cpu.V[regXPos]
        yPos = cpu.V[regYPos]
        pixSize = (cpu.ram[cpu.pc + 1] & ARG_HIGH_MASK)
        self.execSetVram(xPos, yPos, pixSize, cpu)
        cpu.interrupt = SIG_DRAW_GRAPHICS
        cpu.pc += 2

class Interrupt(object):
    def __init__(self, handle):
        self.handle = handle

class Interrupts(object):
    def __init__(self):
        self.interrupts = [None] * NUM_INTERRUPTS
        for i in range(NUM_INTERRUPTS):
            self.interrupts[i] = Interrupt(self.illegalInstr)

        self.interrupts[0x1] = Interrupt(self.drawGraphics)

    def illegalInstr(self, cpu):
        instr = (cpu.ram[cpu.pc] << 8) | cpu.ram[cpu.pc + 1]
        print("Illegal instruction " + hex(instr) +  " at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

    def drawGraphics(self, cpu):
        cpu.gpu.render()


class cpu(threading.Thread):
    def __init__(self, gpu):
        threading.Thread.__init__(self)
        self.gpu = gpu
        self.ram = [U8_MAX] * RAM_SIZE
        self.vram = [0x0] * VRAM_SIZE
        self.V = [U16_MAX] * NUM_REGISTERS
        self.I = U16_MAX
        self.pc = PRG_START_ADDR
        self.sp = 0
        self.running = False
        self.instructionSet = InstructionSet()
        self.debugger = None
        self.interrupt = None
        self.interruptTable = Interrupts()

    def run(self):
        self.running = True
        while self.running:
            if None != self.debugger:
                self.debugger.trace()
            op = (self.ram[self.pc] & OPCODE_MASK) >> 4
            print("op: " + hex(op) + " (" + str(op) + ")")
            self.instructionSet.instructions[op].handle(self)

            if None != self.interrupt:
                self.interruptTable.interrupts[self.interrupt].handle(self)
                self.interrupt = None

    def stop(self):
        self.running = False

    def execProg(self, bin, debugger):
        self.debugger = debugger
        byteAddr = 0
        for byte in bin:
            self.ram[PRG_START_ADDR + byteAddr] = byte
            byteAddr += 1
        self.start()
