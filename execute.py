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
                    return read(read(fetch()))
                case "stack":
                    val = read(0x0100 + registers[SP])
                    registers[SP] += 1
                    registers[SP] &= 0xFF  # Ensure SP wraps around at 0xFF
                    return val

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
                    write(read(fetch()), value)
                case "stack":
                    registers[SP] -= 1
                    registers[SP] &= 0xFF
                    write(0x0100 + registers[SP], value)
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
                    index = (fetch() | (fetch() << 8)) + registers[X]
                    registers[PC] = read(index) | (read(index+1) << 8)
        
        def compare_and_set_flags(value1, value2):
            result = value1 - value2
            registers[P] &= 0b1111_1100  # Clear Carry and Zero flags
            if result >= 0:
                registers[P] |= 0b0000_0001  # Set Carry flag
            if result == 0:
                registers[P] |= 0b0000_0010  # Set Zero flag
            if result & 0x80:
                registers[P] |= 0b1000_0000  # Set Negative flag

        match mnemonic:
            case "BRK":
                self.emulator.running = False # debugging purposes, stop execution on BRK

            case "ADC":
                registers[A] += read_value(addressing) + (registers[P]&1)
                correct_register(A)
            case "SBC":
                registers[A] = registers[A] + (~read_value(addressing)) + (1 - (registers[P]&1))
                correct_register(A)
            
            case "CMP":
                compare_and_set_flags(registers[A], read_value(addressing))
            case "CPX":
                compare_and_set_flags(registers[X], read_value(addressing))
            case "CPY":
                compare_and_set_flags(registers[Y], read_value(addressing))
            case "BIT":
                value = read_value(addressing)
                registers[P] &= 0b0011_1111  # Clear N and V
                registers[P] |= value & 0b1100_0000  # Set N and V from value
                if (registers[A] & value) == 0:
                    registers[P] |= 0b0000_0010  # Set Zero flag

            case "INC":
                write_value(addressing,read_value(addressing)+1)
            case "INA":
                registers[A] += 1
                correct_register(A)
            case "INX":
                registers[X] += 1
                correct_register(X)
            case "INY":
                registers[Y] += 1
                correct_register(Y)
            case "DEC":
                write_value(addressing,read_value(addressing)-1)
            case "DEA":
                registers[A] -= 1
                correct_register(A)
            case "DEX":
                registers[X] -= 1
                correct_register(X)
            case "DEY":
                registers[Y] -= 1
                correct_register(Y)

            case "AND":
                registers[A] &= read_value(addressing)
                correct_register(A)
            case "ORA":
                registers[A] |= read_value(addressing)
                correct_register(A)
            case "EOR":
                registers[A] ^= read_value(addressing)
                correct_register(A)
            
            case "ASL":
                write_value(addressing,read_value(addressing)<<1)
                correct_register(A)
            case "LSR":
                write_value(addressing,read_value(addressing)>>1)
                correct_register(A)
            case "ROL":
                original = read_value(addressing)
                registers[PC] -= 1
                write_value(addressing,(original<<1) | (registers[P]&1))
                if original & 0x80:
                    registers[P] |= 0b0000_0001  # Set Carry flag
                else:
                    registers[P] &= 0b1111_1110  # Clear Carry flag
            case "ROR":
                original = read_value(addressing)
                registers[PC] -= 1
                write_value(addressing,(original>>1) | ((registers[P]&1)<<7))
                if original & 1:
                    registers[P] |= 0b0000_0001  # Set Carry flag
                else:
                    registers[P] &= 0b1111_1110  # Clear Carry flag

            case "BCC":
                if not registers[P]&0x1:
                    jump(addressing)
                else:
                    fetch()
            case "BCS":
                if registers[P]&0x1:
                    jump(addressing)
                else:
                    fetch()
            case "BNE":
                if not registers[P]&0x2:
                    jump(addressing)
                else:
                    fetch()
            case "BEQ":
                if registers[P]&0x2:
                    jump(addressing)
                else:
                    fetch()
            case "BPL":
                if not registers[P]&0x8:
                    jump(addressing)
                else:
                    fetch()
            case "BMI":
                if registers[P]&0x8:
                    jump(addressing)
                else:
                    fetch()
            case "BVC":
                if not registers[P]&0x4:
                    jump(addressing)
                else:
                    fetch()
            case "BVS":
                if registers[P]&0x4:
                    jump(addressing)
                else:
                    fetch()
            case "JMP":
                jump(addressing)
            case "JSR":
                return_address = registers[PC]+2
                write_value("stack", (return_address >> 8) & 0xFF)
                write_value("stack", return_address & 0xFF)
                jump(addressing)
            case "RTS":
                low = read_value("stack")
                high = read_value("stack")
                registers[PC] = (high << 8) | low
            case "RTI":
                registers[P] = read_value("stack")
                low = read_value("stack")
                high = read_value("stack")
                registers[PC] = (high << 8) | low

            case "CLC":
                registers[P] &= 0b1111_1110
            case "CLD":
                registers[P] &= 0b1111_0111
            case "CLI":
                registers[P] &= 0b1111_1011
            case "CLV":
                registers[P] &= 0b1011_1111
            case "SEC":
                registers[P] |= 0b0000_0001
            case "SED":
                registers[P] |= 0b0000_1000
            case "SEI":
                registers[P] |= 0b0000_0100
            case "NOP":
                pass

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
            
            case "TAX":
                registers[X] = registers[A]
            case "TAY":
                registers[Y] = registers[A]
            case "TXA":
                registers[A] = registers[X]
            case "TYA":
                registers[A] = registers[Y]
            
            case "PHA":
                write_value("stack",registers[A])
            case "PHP":
                write_value("stack",registers[P])
            case "PLA":
                registers[A] = read_value("stack")
            case "PLP":
                registers[P] = read_value("stack")
            
            case _:
                raise ValueError(f"not yet implemented: {instruction:2X}")
