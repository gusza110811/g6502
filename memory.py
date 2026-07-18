from devices import *

class map_entry:
    def __init__(self, match:int, match_mask:int, address_mask:int, handler:Device):
        self.match = match
        self.match_mask = match_mask
        self.address_mask = address_mask
        self.handler = handler

DEFAULT_MAP = [
    map_entry(0x8000, 0x8000, 0x7FFF, Rom("a.out")),
    map_entry(0x6000, 0xE000, 0x000F, DemoLED()),
    map_entry(0x0000, 0xE000, 0x7FFF, Ram(0x4000)),
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
