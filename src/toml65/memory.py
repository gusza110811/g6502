import toml65.devices as devices

class map_entry:
    def __init__(self, match:int, match_mask:int, address_mask:int, offset:int, handler:devices.Device):
        self.match = match
        self.match_mask = match_mask
        self.address_mask = address_mask
        self.offset = offset
        self.handler = handler

class Bus:
    def __init__(self, irq_callback=None, map_dict:dict=None):
        self.map = []
        self.irq_callback = irq_callback
        self.devices = []
        self.names = {}
        if map_dict:
            self.gen_map(map_dict)
    
    def killall(self):
        for dev in self.devices:
            dev.kill()
    def startall(self):
        for dev in self.devices:
            dev.start()
    
    def gen_map(self, map_dict:str):
        regions = map_dict.get("region", [])
        for region in regions:
            type = region.get("type", None)
            name = region.get("name", None)
            match = region.get("match", 0)
            match_mask = region.get("match_mask", 0x0000)
            address_mask = region.get("address_mask", 0xFFFF)
            offset = region.get("offset", 0)

            if type is None:
                raise ValueError("\"type\" field is required")

            handler = devices.mapping.get(type, None)
            if handler is None:
                print(f"Unknown device: {type}")
                continue
            handler = handler(region, self.irq_callback, self.get_device)
            entry = map_entry(match, match_mask, address_mask, offset, handler)
            self.devices.append(handler)
            self.names[name] = handler
            self.map.append(entry)
    
    def read(self, address):
        for item in self.map:
            if (address & item.match_mask) == item.match:
                return item.handler.read(address & item.address_mask)
        return 0

    def write(self, address, value):
        for item in self.map:
            if (address & item.match_mask) == item.match:
                return item.handler.write(address & item.address_mask, value & 0xFF)
        return 0

    def get_device(self, name):
        return self.names.get(None)
    
    def __getitem__(self, address):
        return self.read(address)
    
    def __setitem__(self, address, value):
        return self.write(address, value)
