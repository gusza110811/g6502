class Device:
    def init__(self):
        pass
    def read(self, addr):
        pass
    def write(self, addr, value):
        pass

class Ram(Device):
    def __init__(self, size:int=2**16):
        self.memory = [0] * size

    def read(self, addr):
        return self.memory[addr]

    def write(self, addr, value):
        self.memory[addr] = value

class Rom(Device):
    def __init__(self, file:str):
        self.memory = open(file,'rb').read()
    
    def read(self, addr):
        return self.memory[addr]

    def write(self, addr, value):
        raise ValueError("ROM is read-only")

class map_entry:
    def __init__(self, match:int, match_mask:int, address_mask:int, handler:Device):
        self.match = match
        self.match_mask = match_mask
        self.address_mask = address_mask
        self.handler = handler

DEFAULT_MAP = [
    map_entry(0x0000, 0x8000, 0x7FFF, Ram(0x8000)),
    map_entry(0x8000, 0x8000, 0x7FFF, Rom("a.out"))
]


class Memory:
    def __init__(self, map:list[map_entry]=DEFAULT_MAP):
        self.map = map
    
    def read(self, address):
        for item in self.map:
            if (address & item.match_mask) == item.match:
                return item.handler.read(address & item.address_mask)
        return 0

    def write(self, address, value):
        for item in self.map:
            if (address & item.match_mask) == item.match:
                return item.handler.write(address & item.address_mask, value)
        return 0
