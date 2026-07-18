from instructions import instructions

A, X, Y, SP, PC, P = range(6)

class Execute:
    def __init__(self, emulator):
        self.emulator = emulator
        self.instructions = instructions

    def execute(self, instruction):
        registers = self.emulator.registers
        fetch = self.emulator.fetch
        read = self.emulator.memory.read
        write = self.emulator.memory.write
        correct_register = self.emulator.correct_register

        mnemonic, addressing = self.instructions.get(instruction,("JAM","IMM"))

        def read_value(addressing):
            match addressing:
                case "accumulator":
                    return registers[A]
                case "absolute":
                    return read(fetch() | (fetch() << 8))
                case "absolute_X":
                    return read((fetch() | (fetch() << 8)) + registers[X])
                case "absolute_Y":
                    return read((fetch() | (fetch() << 8)) + registers[Y])
                case "immediate":
                    return fetch()
                case "implied":
                    return 0
                case "indirect_X":
                    index = fetch() + registers[X]
                    address = read(index) | (read(index+1) << 8)
                    return read(address)
                case "indirect_Y":
                    index = fetch()
                    address = read(index) | (read(index+1) << 8) + registers[Y]
                    return read(address)
                case "zeropage":
                    return read(fetch())
                case "zeropage_X":
                    return read(fetch() + registers[X])
                case "zeropage_Y":
                    return read(fetch() + registers[Y])
                case "zp_indirect":
                    return read(read(fetch))

        def write_value(addressing, value):
            match addressing:
                case "accumulator":
                    registers[A] = value
                case "absolute":
                    write(fetch() | (fetch() << 8), value)
                case "absolute_X":
                    write((fetch() | (fetch() << 8)) + registers[X], value)
                case "absolute_Y":
                    write((fetch() | (fetch() << 8)) + registers[Y], value)
                case "implied":
                    return
                case "indirect_X":
                    index = fetch() + registers[X]
                    address = read(index) | (read(index+1) << 8)
                    write(address, value)
                case "indirect_Y":
                    index = fetch()
                    address = read(index) | (read(index+1) << 8) + registers[Y]
                    write(address, value)
                case "zeropage":
                    write(fetch(), value)
                case "zeropage_X":
                    write(fetch() + registers[X], value)
                case "zeropage_Y":
                    write(fetch() + registers[Y], value)
                case "zp_indirect":
                    write(read(fetch), value)
        def jump(addressing):
            match addressing:
                case "absolute":
                    registers[PC] = fetch() | (fetch() << 8)
                case "indirect":
                    index = fetch() | (fetch() << 8)
                    registers[PC] = read(index) | (read(index+1) << 8)
                case "relative":
                    target = fetch()
                    registers[PC] += (target & 0x7F) - (target & 0x80)
                case "abs_indirect_X":
                    index = (fetch() | (fetch() << 8)) + registers(X)
                    registers[PC] = read(index) | (read(index+1) << 8)
        match mnemonic:
            case "BRK":
                self.emulator.running = False

            case "BNE":
                if not registers[P]&0x2:
                    jump(addressing)
                else:
                    fetch()

            case "INX":
                registers[X] += 1
                correct_register(X)
            case "INY":
                registers[Y] += 1
                correct_register(Y)

            case "LDA":
                registers[A] = read_value(addressing)
            case "LDX":
                registers[X] = read_value(addressing)
            case "LDY":
                registers[Y] = read_value(addressing)
            
            case "STA":
                write_value(addressing,registers[A])
            case "STX":
                write_value(addressing,registers[X])
            case "STY":
                write_value(addressing,registers[Y])
            
            case _:
                raise ValueError(f"not yet implemented: {instruction:2X}")
