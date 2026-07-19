import threading
from time import sleep

class Device:
    def __init__(self, parameters:dict, irq_callback=None):
        self.irq_callback = irq_callback

        self.running = True
        self.thread = threading.Thread(target=self.run,daemon=True)
        self.thread.start()

    def run(self):
        pass

    def read(self, addr):
        return 0

    def write(self, addr, value):
        pass

class Ram(Device):
    def __init__(self, parameters:dict, irq_callback=None):
        size = parameters.get("size",None)
        if size is None:
            raise ValueError("Ram size not defined")
        self.memory = [0] * size

    def read(self, addr):
        return self.memory[addr]

    def write(self, addr, value):
        self.memory[addr] = value

class Rom(Device):
    def __init__(self, parameters:dict, irq_callback=None):
        source = parameters.get("source","main.bin")
        if source is None:
            raise ValueError("Rom image source not defined")
        self.memory = open(source,'rb').read()
    
    def read(self, addr):
        return self.memory[addr]

    def write(self, addr, value):
        pass

class DemoLED(Device):
    def __init__(self, parameters:dict, irq_callback=None):
        self.state = 0
        super().__init__(parameters, irq_callback)

    def run(self):
        while self.running:
            sleep(0.1)
            print(f"LED state: {self.state:08b} \r", end="", flush=True)

    def read(self, addr):
        return 0

    def write(self, addr, value):
        self.state = value & 0xFF

class DemoButton(Device):
    def run(self):
        while self.running:
            input()
            if self.irq_callback:
                self.irq_callback()

    def read(self, addr):
        return 0

    def write(self, addr, value):
        pass

mapping = {
    "ram":Ram,
    "rom":Rom,
    "demoled":DemoLED,
    "demobutton":DemoButton,
}
