#!/usr/bin/env python3

import threading

U8_MAX                   = 0xFF
U16_MAX                  = 0xFFFF

RAM_SIZE                 = 4096
VRAM_SIZE                = 64 * 32
STACK_SIZE               = 16

NUM_REGISTERS            = 0x10

NUM_INSTRUCTIONS         = 0x10
NUM_0x8_INSTRUCTIONS     = 0x9
NUM_MISC_INSTRUCTIONS    = 0x9
MISC_BCD                 = 0x33
MISC_BCD_INDEX           = 0x0
MISC_SET_SPRT_ADDR       = 0x29
MISC_SET_SPRT_ADDR_INDEX = 0x1

PRG_START_ADDR           = 0x200

OPCODE_MASK              = 0xF0
ARG_HIGH_MASK            = 0x0F
ARG_LOW_MASK             = 0xF0

SPRITE_WIDTH             = 0x8

NUM_INTERRUPTS           = 0x3
SIG_ILL_INSTR            = 0x0
SIG_DRAW_GRAPHICS        = 0x1
SIG_STACK_OVERFLOW       = 0x2

FONT_ADDRESS             = 0x50
FONT_SPRITE_SIZE         = 0x5
FONT_SPRITES = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
]

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
        self.instructions[0x2] = Instruction(self.execCall)
        self.instructions[0x6] = Instruction(self.execLdReg)
        self.instructions[0x8] = Instruction(self.exec8XY, NUM_0x8_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0x8].subInstructions[0x0] = Instruction(self.execAssignXY)
        self.instructions[0xA] = Instruction(self.execSetI)
        self.instructions[0xD] = Instruction(self.execRendering)
        self.instructions[0xF] = Instruction(self.execMiscInstructions, NUM_MISC_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0xF].subInstructions[MISC_BCD_INDEX] = Instruction(self.execBCD)
        self.instructions[0xF].subInstructions[MISC_SET_SPRT_ADDR_INDEX] = Instruction(self.execSetSprtAddress)

    def getAddress(self, cpu):
        return ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]

    def illegalInstr(self, cpu):
        cpu.interrupt = SIG_ILL_INSTR

    def execJump(self, cpu):
        cpu.pc = self.getAddress(cpu)

    def execCall(self, cpu):
        if cpu.sp > 0:
            cpu.sp -= 1
            jumpAddress = self.getAddress(cpu)
            cpu.stack[cpu.sp] = jumpAddress
            cpu.pc = jumpAddress
        else:
            cpu.interrupt = SIG_STACK_OVERFLOW

    def execLdReg(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.V[reg] = cpu.ram[cpu.pc + 1]

    def exec8XY(self, cpu):
        subInstruction = (cpu.ram[cpu.pc + 1] & ARG_HIGH_MASK)
        if subInstruction != 0xE:
            self.instructions[0x8].subInstructions[subInstruction].handle(cpu)
        else:
            cpu.interrupt = SIG_ILL_INSTR

    def execAssignXY(self, cpu):
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        cpu.V[regX] = cpu.V[regY]
        print("Assigned reg " + hex(regX) + " to reg " + hex(regY))

    def execSetI(self, cpu):
        val = ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]
        cpu.I = val

    def execSetVram(self, xStartPos, yStartPos, spriteHeight, cpu):
        for yIndex in range(spriteHeight):
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
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        xPos = cpu.V[regX]
        yPos = cpu.V[regY]
        spriteSize = (cpu.ram[cpu.pc + 1] & ARG_HIGH_MASK)
        cpu.V[0xF] = 0
        self.execSetVram(xPos, yPos, spriteSize, cpu)
        cpu.interrupt = SIG_DRAW_GRAPHICS

    def execMiscInstructions(self, cpu):
        instruction = cpu.ram[cpu.pc + 1]
        print("instruction: " + hex(instruction))
        if MISC_BCD == instruction:
            self.instructions[0xF].subInstructions[MISC_BCD_INDEX].handle(cpu)
        elif MISC_SET_SPRT_ADDR == instruction:
            self.instructions[0xF].subInstructions[MISC_SET_SPRT_ADDR_INDEX].handle(cpu)
        else:
            cpu.interrupt = SIG_ILL_INSTR

    def execBCD(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.V[reg]
        cpu.ram[cpu.I] = val / 100
        cpu.ram[cpu.I + 1] = (val % 100) / 10
        cpu.ram[cpu.I + 2] = val % 10

    def execSetSprtAddress(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.V[reg]
        cpu.I = val * FONT_SPRITE_SIZE

class Interrupt(object):
    def __init__(self, handle):
        self.handle = handle

class Interrupts(object):
    def __init__(self):
        self.interrupts = [None] * NUM_INTERRUPTS
        for i in range(NUM_INTERRUPTS):
            self.interrupts[i] = Interrupt(self.illegalInstr)

        self.interrupts[0x1] = Interrupt(self.drawGraphics)
        self.interrupts[0x2] = Interrupt(self.stackOverflow)

    def illegalInstr(self, cpu):
        instr = (cpu.ram[cpu.pc] << 8) | cpu.ram[cpu.pc + 1]
        print("Illegal instruction " + hex(instr) +  " at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

    def drawGraphics(self, cpu):
        cpu.gpu.render()

    def stackOverflow(self, cpu):
        print("Stack overflow at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False


class cpu(threading.Thread):
    def __init__(self, gpu):
        threading.Thread.__init__(self)
        self.gpu = gpu
        self.ram = [U8_MAX] * RAM_SIZE
        self.vram = [0x0] * VRAM_SIZE
        self.stack = [U16_MAX] * STACK_SIZE
        self.sp = STACK_SIZE
        self.V = [U16_MAX] * NUM_REGISTERS
        self.I = U16_MAX
        self.pc = PRG_START_ADDR
        self.running = False
        self.instructionSet = InstructionSet()
        self.debugger = None
        self.interrupt = None
        self.interruptTable = Interrupts()

        fontOffset = 0
        for font in FONT_SPRITES:
            self.ram[FONT_ADDRESS + fontOffset] = font
            fontOffset += 1

    def run(self):
        self.running = True
        while self.running:
            if None != self.debugger:
                self.debugger.trace()
            op = (self.ram[self.pc] & OPCODE_MASK) >> 4
            self.instructionSet.instructions[op].handle(self)

            # Execution of an instruction might lead to an interrupt
            # which needs to be handled
            if None != self.interrupt:
                self.interruptTable.interrupts[self.interrupt].handle(self)
                self.interrupt = None
            self.pc += 2

    def stop(self):
        self.running = False

    def execProg(self, bin, debugger):
        self.debugger = debugger
        byteAddr = 0
        for byte in bin:
            self.ram[PRG_START_ADDR + byteAddr] = byte
            byteAddr += 1
        self.start()
