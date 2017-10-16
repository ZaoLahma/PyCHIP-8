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

        self.instructions[0x1] = instruction(self.execJump)
        self.instructions[0x6] = instruction(self.execLdReg)
        self.instructions[0x8] = instruction(self.exec8XY, NUM_0x8_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0x8].subInstructions[0x0] = instruction(self.execAssignXY)
        self.instructions[0xA] = instruction(self.execSetI)
        self.instructions[0xD] = instruction(self.execRendering)

    def illegalInstr(self, cpu):
        instr = (cpu.ram[cpu.pc] << 8) | cpu.ram[cpu.pc + 1]
        print("Illegal instruction " + hex(instr) +  " at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

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

    def execRendering(self, cpu):
        regXPos = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regYPos = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        print("Printing graphics from regs: " + hex(regXPos) + ", " + hex(regYPos))
        xPos = cpu.V[regXPos]
        yPos = cpu.V[regYPos]
        pixSize = (cpu.ram[cpu.pc + 1] & ARG_HIGH_MASK)
        pixData = [None] * pixSize
        for pixIndex in range(pixSize):
            pixData[pixIndex] = cpu.ram[cpu.I + pixIndex]
            print("pixel: " + hex(pixData[pixIndex]))
            pixIndex += 1

        print("Graphics starting at: " + hex(xPos) + ", " + hex(yPos) + ". Height: " + hex(pixSize))
        for y in range(pixSize):
            yCoord = y + yPos
            yCoord = yCoord % 32
            for x in range(SPRITE_WIDTH):
                xCoord = x + xPos
                xCoord = xCoord % 64
                cpu.vram[yCoord * xCoord] = pixData[y]
                print("Set pix " + hex(y + yPos) + ", " + hex(x + xPos) + " to " + hex(cpu.vram[(y + yPos) * (x + xPos)]))
        x = 0
        y = 0
        for byte in cpu.vram:
            if 0x0 != byte:
                cpu.gpu.drawPixel(x, y, 1)
            else:
                cpu.gpu.drawPixel(x, y, 0)
            x += 1
            if x == 64:
                x = 0
                y += 1
        cpu.gpu.render()
        #cpu.pc += 2

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
        self.instructionSet = instructionSet()
        self.debugger = None

    def run(self):
        self.running = True
        while self.running:
            if None != self.debugger:
                self.debugger.trace()
            op = (self.ram[self.pc] & OPCODE_MASK) >> 4
            print("op: " + hex(op) + " (" + str(op) + ")")
            self.instructionSet.instructions[op].handle(self)

    def stop(self):
        self.running = False

    def execProg(self, bin, debugger):
        self.debugger = debugger
        byteAddr = 0
        for byte in bin:
            self.ram[PRG_START_ADDR + byteAddr] = byte
            byteAddr += 1
        self.start()
