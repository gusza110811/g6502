import threading
from time import sleep
import sys

class Device:

    def __init__(self, parameters:dict, irq_callback=None):
        self.irq_callback = irq_callback

        self.running = True

        self.threads = []
        for job in self.jobs_target:
            thread = threading.Thread(target=job,daemon=True)
            self.threads.append(thread)
            thread.start()

    jobs_target = []

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
        if addr < len(self.memory):
            return self.memory[addr]
        else:
            return 0x00

    def write(self, addr, value):
        if addr < len(self.memory):
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
        self.jobs_target = [self.run]
        super().__init__(parameters, irq_callback)

    def run(self):
        prev = 0
        while self.running:
            sleep(0.1)
            if self.state != prev:
                print(f"LED state: {self.state:08b} \r", end="", flush=True)
                prev = self.state

    def read(self, addr):
        return 0

    def write(self, addr, value):
        self.state = value & 0xFF

class DemoButton(Device):
    def __init__(self, parameters, irq_callback=None):
        self.jobs_target = [self.run]
        super().__init__(parameters, irq_callback)
    def run(self):
        while self.running:
            input()
            if self.irq_callback:
                self.irq_callback()

    def read(self, addr):
        return 0

    def write(self, addr, value):
        pass

class ACIA(Device):
    def __init__(self, parameters:dict, irq_callback=None):
        self.tx_buffer = []
        self.rx_buffer = []
        self.jobs_target = [self.input, self.output]
        super().__init__(parameters, irq_callback)

    def output(self):
        mapping = {
            b"\x7F": b"\b",
            b"\r": b"\r\n",
        }
        while self.running:
            if self.tx_buffer:
                byte = bytes([self.tx_buffer.pop(0)])
                if byte in mapping:
                    byte = mapping[byte]
                print(byte.decode(), end="", flush=True)
    
    def input(self):
        mapping = {
            b"\x7F": b"\b",
            b"\n": b"\r",
        }
        stdin = sys.stdin
        while self.running:
            char = stdin.read(1).encode()
            if char in mapping:
                char = mapping[char]
            for c in char:
                self.rx_buffer.append(c)

    def read(self, addr):
        if addr == 0:
            if self.rx_buffer:
                return self.rx_buffer.pop(0)
            else:
                return 0
        elif addr == 1:
            return (8 if self.rx_buffer else 0) | (16 if len(self.tx_buffer) < 16 else 0)
        return 0x00

    def write(self, addr, value):
        if addr == 0:
            self.tx_buffer.append(value)
        elif addr == 1:
            pass
        elif addr == 2:
            pass

mapping = {
    "ram":Ram,
    "rom":Rom,
    "demoled":DemoLED,
    "demobutton":DemoButton,
    "acia":ACIA,
}
