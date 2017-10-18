#!/usr/bin/env python3

import threading
import time
import random
from gpu import SCREEN_X_SIZE
from gpu import SCREEN_Y_SIZE
from keyboard import Keyboard

U8_MAX                   = 0xFF
U16_MAX                  = 0xFFFF

RAM_SIZE                 = 4096
VRAM_SIZE                = SCREEN_X_SIZE * SCREEN_Y_SIZE
STACK_SIZE               = 16

NUM_REGISTERS            = 0x10

NUM_INSTRUCTIONS         = 0x10
NUM_0x8_INSTRUCTIONS     = 0x9
NUM_MISC_INSTRUCTIONS    = 0x9
MISC_BCD                 = 0x33
MISC_BCD_INDEX           = 0x0
MISC_SET_SPRT_ADDR       = 0x29
MISC_SET_SPRT_ADDR_INDEX = 0x1
MISC_REG_LOAD            = 0x65
MISC_REG_LOAD_INDEX      = 0x2
MISC_SET_DLY_TIMER       = 0x15
MISC_SET_DLY_TIMER_INDEX = 0x3
MISC_GET_DLY_TIMER       = 0x7
MISC_GET_DLY_TIMER_INDEX = 0x4
MISC_SET_SND_TIMER       = 0x18
MISC_SET_SND_TIMER_INDEX = 0x5

NUM_CRLRET_INSTRUCTINS   = 0x2
CLRRET_RET               = 0xEE
CLRRET_RET_INDEX         = 0x0

PRG_START_ADDR           = 0x200

OPCODE_MASK              = 0xF0
ARG_HIGH_MASK            = 0x0F
ARG_LOW_MASK             = 0xF0

SPRITE_WIDTH             = 0x8

NUM_INTERRUPTS           = 0x4
SIG_ILL_INSTR            = 0x0
SIG_DRAW_GRAPHICS        = 0x1
SIG_STACK_OVERFLOW       = 0x2
SIG_STACK_UNDERFLOW      = 0x3

DELAY_CYCLE_PERIOD       = 60 # Hz
MS_IN_SEC                = 1000 # ms
RUN_FREQ_IN_HZ           = 500 #Hz

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

        self.instructions[0x0] = Instruction(self.execClrRet, NUM_CRLRET_INSTRUCTINS, self.illegalInstr)
        self.instructions[0x0].subInstructions[CLRRET_RET_INDEX] = Instruction(self.execRet)
        self.instructions[0x1] = Instruction(self.execJump)
        self.instructions[0x2] = Instruction(self.execCall)
        self.instructions[0x3] = Instruction(self.execSkpInstrIfEqVX)
        self.instructions[0x4] = Instruction(self.execSkpInstrIfNotEqVX)
        self.instructions[0x6] = Instruction(self.execLdReg)
        self.instructions[0x7] = Instruction(self.execAddX)
        self.instructions[0x8] = Instruction(self.exec8XY, NUM_0x8_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0x8].subInstructions[0x0] = Instruction(self.execAssignXY)
        self.instructions[0x8].subInstructions[0x2] = Instruction(self.execAndXY)
        self.instructions[0x8].subInstructions[0x4] = Instruction(self.execAddXY)
        self.instructions[0x8].subInstructions[0x5] = Instruction(self.execSubXY)
        self.instructions[0xA] = Instruction(self.execSetI)
        self.instructions[0xC] = Instruction(self.execRandVX)
        self.instructions[0xD] = Instruction(self.execRendering)
        self.instructions[0xE] = Instruction(self.execKbRoutine)
        self.instructions[0xF] = Instruction(self.execMiscInstructions, NUM_MISC_INSTRUCTIONS, self.illegalInstr)
        self.instructions[0xF].subInstructions[MISC_BCD_INDEX] = Instruction(self.execBCD)
        self.instructions[0xF].subInstructions[MISC_SET_SPRT_ADDR_INDEX] = Instruction(self.execSetSprtAddress)
        self.instructions[0xF].subInstructions[MISC_REG_LOAD_INDEX] = Instruction(self.execRegLoad)
        self.instructions[0xF].subInstructions[MISC_SET_DLY_TIMER_INDEX] = Instruction(self.execSetDlyTmr)
        self.instructions[0xF].subInstructions[MISC_GET_DLY_TIMER_INDEX] = Instruction(self.execGetDlyTmr)
        self.instructions[0xF].subInstructions[MISC_SET_SND_TIMER_INDEX] = Instruction(self.execSetSndTmr)

    def getAddress(self, cpu):
        return ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]

    def illegalInstr(self, cpu):
        cpu.interrupt = SIG_ILL_INSTR

    def execClrRet(self, cpu):
        subInstruction = cpu.ram[cpu.pc + 1]
        if CLRRET_RET == subInstruction:
            self.instructions[0x0].subInstructions[CLRRET_RET_INDEX].handle(cpu)
        else:
            cpu.interrupt = SIG_ILL_INSTR

    def execRet(self, cpu):
        retAddr = cpu.stack[cpu.sp]
        if cpu.sp > 0:
            cpu.sp -= 1
            cpu.pc = retAddr
        else:
            cpu.interrupt = SIG_STACK_UNDERFLOW

    def execJump(self, cpu):
        cpu.pc = self.getAddress(cpu) - 2

    def execCall(self, cpu):
        if cpu.sp < STACK_SIZE:
            cpu.sp += 1
            jumpAddress = self.getAddress(cpu)
            cpu.stack[cpu.sp] = cpu.pc
            cpu.pc = jumpAddress - 2
        else:
            cpu.interrupt = SIG_STACK_OVERFLOW

    def execSkpInstrIfEqVX(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.ram[cpu.pc + 1]
        if val == cpu.V[reg]:
            cpu.pc += 2

    def execSkpInstrIfNotEqVX(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.ram[cpu.pc + 1]
        if val != cpu.V[reg]:
            cpu.pc += 2

    def execLdReg(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.V[reg] = cpu.ram[cpu.pc + 1]

    def execAddX(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.V[reg] += cpu.ram[cpu.pc + 1]

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

    def execAndXY(self, cpu):
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        cpu.V[regX] = cpu.V[regX] & cpu.V[regY]

    def execAddXY(self, cpu):
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        val = cpu.V[regX] + cpu.V[regY]
        if val > 255:
            val -= 256
            cpu.V[0xF] = 1
        else:
            cpu.V[0xF] = 0
        cpu.V[regX] = val

    def execSubXY(self, cpu):
        regX = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        regY = (cpu.ram[cpu.pc + 1] & ARG_LOW_MASK) >> 4
        val = cpu.V[regX] - cpu.V[regY]
        if cpu.V[regX] < cpu.V[regY]:
            val += 256
            cpu.V[0xF] = 0
        else:
            cpu.V[0xF] = 1
        cpu.V[regX] = val

    def execSetI(self, cpu):
        val = ((cpu.ram[cpu.pc] & ARG_HIGH_MASK) << 8) | cpu.ram[cpu.pc + 1]
        cpu.I = val

    def execRandVX(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.ram[cpu.pc + 1]
        cpu.V[reg] = (val & random.randint(0, 255))

    def execSetVram(self, xStartPos, yStartPos, spriteHeight, cpu):
        for yIndex in range(spriteHeight):
            pixByte = bin(cpu.ram[cpu.I + yIndex])
            pixByte = pixByte[2:].zfill(8)
            yCoord = yStartPos + yIndex
            yCoord = yCoord % SCREEN_Y_SIZE

            for xIndex in range(8):
                xCoord = xStartPos + xIndex
                xCoord = xCoord % SCREEN_X_SIZE

                pixVal = int(pixByte[xIndex])
                # Set pixel to new pix val XOR old pix val
                vramAddr = yCoord * SCREEN_X_SIZE + xCoord
                oldPixVal = cpu.vram[vramAddr]
                if pixVal == 1 and oldPixVal == 1:
                    cpu.V[0xF] = cpu.V[0xF] | 1
                    pixVal = 0
                elif pixVal == 0 and oldPixVal == 1:
                    pixVal = 1

                cpu.vram[vramAddr] = pixVal
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

    def execKbRoutine(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        subRoutine = cpu.ram[cpu.pc + 1]

        if 0x9E == subRoutine:
             if True == cpu.keyboard.keyPressed(cpu.V[reg]):
                 cpu.pc += 2
        elif 0xA1 == subRoutine:
             if False == cpu.keyboard.keyPressed(cpu.V[reg]):
                 cpu.pc += 2
        else:
            cpu.interrupt = SIG_ILL_INSTR


    def execMiscInstructions(self, cpu):
        instruction = cpu.ram[cpu.pc + 1]
        if MISC_BCD == instruction:
            self.instructions[0xF].subInstructions[MISC_BCD_INDEX].handle(cpu)
        elif MISC_SET_SPRT_ADDR == instruction:
            self.instructions[0xF].subInstructions[MISC_SET_SPRT_ADDR_INDEX].handle(cpu)
        elif MISC_REG_LOAD == instruction:
            self.instructions[0xF].subInstructions[MISC_REG_LOAD_INDEX].handle(cpu)
        elif MISC_SET_DLY_TIMER == instruction:
            self.instructions[0xF].subInstructions[MISC_SET_DLY_TIMER_INDEX].handle(cpu)
        elif MISC_GET_DLY_TIMER == instruction:
            self.instructions[0xF].subInstructions[MISC_GET_DLY_TIMER_INDEX].handle(cpu)
        elif MISC_SET_SND_TIMER == instruction:
            self.instructions[0xF].subInstructions[MISC_SET_SND_TIMER_INDEX].handle(cpu)
        else:
            cpu.interrupt = SIG_ILL_INSTR

    def execBCD(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.V[reg]
        cpu.ram[cpu.I] = int(val / 100)
        cpu.ram[cpu.I + 1] = int((val % 100) / 10)
        cpu.ram[cpu.I + 2] = int(val % 10)

    def execSetSprtAddress(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        val = cpu.V[reg]
        cpu.I = FONT_ADDRESS + val * FONT_SPRITE_SIZE

    def execRegLoad(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        for i in range(reg + 1):
            cpu.V[i] = cpu.ram[cpu.I]
            cpu.I += 1

    def execSetDlyTmr(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.D = cpu.V[reg]

    def execGetDlyTmr(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.V[reg] = cpu.D

    def execSetSndTmr(self, cpu):
        reg = cpu.ram[cpu.pc] & ARG_HIGH_MASK
        cpu.S = cpu.V[reg]

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
        self.interrupts[0x2] = Interrupt(self.stackUnderflow)

    def illegalInstr(self, cpu):
        instr = (cpu.ram[cpu.pc] << 8) | cpu.ram[cpu.pc + 1]
        print("Illegal instruction " + hex(instr) +  " at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

    def drawGraphics(self, cpu):
        cpu.gpu.render()

    def stackOverflow(self, cpu):
        print("Stack overflow at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False

    def stackUnderflow(self, cpu):
        print("Stack underflow at " + hex(cpu.pc - PRG_START_ADDR))
        cpu.running = False


class Cpu(threading.Thread):
    def __init__(self, gpu):
        threading.Thread.__init__(self)
        self.gpu = gpu
        self.ram = [U8_MAX] * RAM_SIZE
        self.vram = [0x0] * VRAM_SIZE

        self.V = [U16_MAX] * NUM_REGISTERS
        self.I = U16_MAX
        self.D = 0x0
        self.S = 0x0

        self.stack = [U16_MAX] * STACK_SIZE
        self.sp = 0x0

        self.pc = PRG_START_ADDR

        self.running = False
        self.instructionSet = InstructionSet()
        self.debugger = None
        self.interrupt = None
        self.interruptTable = Interrupts()

        self.delayCycle = 0

        self.keyboard = Keyboard()

        fontOffset = 0
        for font in FONT_SPRITES:
            self.ram[FONT_ADDRESS + fontOffset] = font
            fontOffset += 1

    def run(self):
        self.running = True
        while self.running:
            if None != self.debugger:
                self.debugger.trace()
            timeBefore = time.time() * 1000
            op = (self.ram[self.pc] & OPCODE_MASK) >> 4
            self.instructionSet.instructions[op].handle(self)

            # Execution of an instruction might lead to an interrupt
            # which needs to be handled
            if None != self.interrupt:
                self.interruptTable.interrupts[self.interrupt].handle(self)
                self.interrupt = None
            self.pc += 2

            timeAfter = time.time() * 1000
            elapsedTime = timeAfter - timeBefore
            if elapsedTime < (MS_IN_SEC / RUN_FREQ_IN_HZ):
                toSleep = ((MS_IN_SEC / RUN_FREQ_IN_HZ)) - elapsedTime
                toSleep = toSleep / MS_IN_SEC
                time.sleep(toSleep)

            self.delayCycle = (self.delayCycle + 1) % int((MS_IN_SEC / DELAY_CYCLE_PERIOD) / (MS_IN_SEC / RUN_FREQ_IN_HZ) + 1)
            if 0 == self.delayCycle:
                if self.D > 0x0:
                    self.D -= 0x1
                if self.S > 0x0:
                    self.S -= 0x1



    def stop(self):
        self.running = False

    def execProg(self, bin, debugger):
        self.debugger = debugger
        byteAddr = 0
        for byte in bin:
            self.ram[PRG_START_ADDR + byteAddr] = byte
            byteAddr += 1
        self.start()
