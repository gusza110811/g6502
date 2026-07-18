import memory
import execute
import math
import time

A, X, Y, SP, PC, P = range(6)

class Emulator:
    def __init__(self):
        self.running = True
        self.memory = memory.Memory()
        self.execute = execute.Execute(self)
        self.registers = [0] * 8  # A, X, Y, SP, PC, P, -, -
        self.delay = 0.1
    
    def fetch(self):
        pc = self.registers[PC]
        opcode = self.memory.read(pc)
        self.registers[PC] += 1
        return opcode
    
    def correct_register(self,reg):
        if reg == PC:
            self.registers[reg] = self.registers[reg] & 0xFFFF
        else:
            self.registers[P] = 0
            if self.registers[reg] & 0x100:
                self.registers[P] |= 0x01  # Set Carry flag
            if self.registers[reg] < 0:
                self.registers[P] |= 0x40  # Set Overflow flag

            self.registers[reg] = self.registers[reg] & 0xFF

            if self.registers[reg] == 0:
                self.registers[P] |= 0x02  # Set Zero flag
            if self.registers[reg] & 0x80:
                self.registers[P] |= 0x80  # Set Negative flag

    def main(self):
        reset_vec = self.memory.read(0xFFFC) | (self.memory.read(0xFFFD) << 8)
        self.registers[PC] = reset_vec

        while self.running:
            inst = self.fetch()

            self.execute.execute(inst)

            #print(f"PC: {self.registers[PC]:04X}, A: {self.registers[A]:02X}, X: {self.registers[X]:02X}, Y: {self.registers[Y]:02X}, SP: {self.registers[SP]:02X}, P: {self.registers[P]:08b}")

            time.sleep(self.delay)  # Add a small delay to slow down execution for debugging purposes

    def dump_registers(self):
        print("Registers:")
        reg_names = ['A ', 'X ', 'Y ', 'SP', 'PC', 'P ']
        for i, name in enumerate(reg_names):
            print(f"{name}: {self.registers[i]:02X}")
    
    def dump_memory(self, start=0x0000, end=0xFFFF):
        print(f"Memory dump from {start:04X} to {end:04X}:")
        mem = [self.memory.read(addr) for addr in range(start, end + 1)]
        previous = None
        repeated = False

        def get_string(bytes:bytearray):
            out = []
            for byte in bytes:
                if 31 < byte < 127:
                    out.append(chr(byte))
                else:
                    out.append(".")

            return "".join(out)

        for idx in range(int(math.ceil(len(mem)/16))):
            line = bytes(mem[idx*16:idx*16+16])
            if line == previous:
                repeated = True
                continue
            if repeated:
                print("...")
                repeated = False
            print(f"{idx:03X}0",end="")
            print(" "+line.hex(" "),end="")
            print(" | ",end="")
            print(get_string(line))
            previous = line

if __name__ == "__main__":
    emu = Emulator()
    try:
        emu.main()
    finally:
        emu.dump_registers()
        emu.dump_memory(0x0000, 0xFFFF)
