from instructions import Instruction

A, X, Y, SP, PC, P = range(6)

class Execute:
    def __init__(self, emulator):
        self.emulator = emulator

    def execute(self, instruction):
        registers = self.emulator.registers
        fetch = self.emulator.fetch
        read = self.emulator.memory.read
        write = self.emulator.memory.write

        if instruction == Instruction.BRK:
            self.emulator.running = False
        elif instruction == Instruction.LDA_IMM:
            registers[A] = fetch()
        elif instruction == Instruction.STA_ZP:
            addr = fetch()
            write(addr, registers[A])
        else:
            raise NotImplementedError(f"Instruction {instruction} not implemented.")
