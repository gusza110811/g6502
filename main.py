import memory
import execute
import math
import time
from instructions import instructions
import tomllib

A, X, Y, SP, PC, P = range(6)

class Emulator:
    def __init__(self, bus_definition:dict):
        self.running = True
        self.memory = memory.Bus(self.interrupt, bus_definition)
        self.execute = execute.Execute(self)
        self.registers = [0] * 8  # A, X, Y, SP, PC, P, -, -
        self.delay = 0.1

        self.doTrace = True
        self.trace = []

        self.reset_vec = self.memory.read(0xFFFC) | (self.memory.read(0xFFFD) << 8)
        self.interrupt_vec = self.memory.read(0xFFFE) | (self.memory.read(0xFFFF) << 8)

        self.interrupt_request = False
    
    def fetch(self):
        pc = self.registers[PC]
        opcode = self.memory.read(pc)
        self.registers[PC] += 1
        return opcode

    def push(self, value):
        self.registers[SP] -= 1
        self.registers[SP] &= 0xFF
        self.memory.write(0x0100 + self.registers[SP], value)
    def pop(self):
        value = self.memory.read(0x0100 + self.registers[SP])
        self.registers[SP] += 1
        self.registers[SP] &= 0xFF
        return value

    def interrupt(self):
        self.interrupt_request = True
    
    def correct_register(self,reg):
        if reg == PC:
            self.registers[reg] = self.registers[reg] & 0xFFFF
        else:
            self.registers[P] = 0
            if self.registers[reg] & 0x100:
                self.registers[P] |= 0x01
            if self.registers[reg] < 0:
                self.registers[P] |= 0x40

            self.registers[reg] = self.registers[reg] & 0xFF

            if self.registers[reg] == 0:
                self.registers[P] |= 0x02
            if self.registers[reg] & 0x80:
                self.registers[P] |= 0x80

    def main(self):
        self.registers[PC] = self.reset_vec

        while self.running:
            inst = self.fetch()

            if self.doTrace:
                self.trace.append((self.registers[PC]-1, inst, self.registers.copy()))

            self.execute.execute(inst)

            if self.interrupt_request:
                if self.registers[P] & 0x04:
                    self.push(self.registers[PC] >> 8)
                    self.push(self.registers[PC])
                    self.push(self.registers[P])
                    self.registers[PC] = self.interrupt_vec
                    self.interrupt_request = False

            time.sleep(self.delay)

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
    default_busdef = tomllib.load(open("default_bus.toml","rb"))

    emu = Emulator(default_busdef)
    try:
        emu.main()
    finally:
        emu.dump_registers()
        emu.dump_memory(0x0000, 0xFFFF)

        with open(".trace", "w") as f:
            for addr, inst, regs in emu.trace:
                inst_decode = instructions.get(inst, ('???',"???"))
                f.write(f"{addr:04X}: {inst_decode[0].rjust(4)}-{inst_decode[1].ljust(10)}\
({inst:2X})\t\tA: {regs[A]:02X}, X: {regs[X]:02X}, Y: {regs[Y]:02X}, SP: {regs[SP]:02X}, P: {regs[P]:08b}\n")
