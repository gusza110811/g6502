import threading
from time import sleep
import sys, os
import select
import toml65.termmagic as termmagic

class Device:

    def __init__(self, parameters:dict, irq_callback=None):
        self.irq_callback = irq_callback

        self.running = True

        self.threads:list[threading.Thread] = []

    def start(self):
        self.running = True
        for job in self.jobs_target:
            thread = threading.Thread(target=job,daemon=True)
            self.threads.append(thread)
            thread.start()

    jobs_target = []

    def kill(self):
        self.running = False

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

class Nvram(Device):
    def __init__(self, parameters, irq_callback=None):
        super().__init__(parameters, irq_callback)
        savefilename = parameters.get("file","nvram.img")
        size = parameters.get("size",None)
        if size is None:
            raise ValueError("NVRam size not defined")
        if os.path.exists(savefilename):
            self.savefile = open(savefilename,"rb+")
        else:
            self.savefile = open(savefilename,"wb+")
        sizef = self.savefile.seek(0,2)
        if sizef < size:
            self.savefile.write(bytes(size-sizef))

    def read(self, addr):
        self.savefile.seek(addr)
        return self.savefile.read(1)[0]

    def write(self, addr, value):
        self.savefile.seek(addr)
        self.savefile.write(bytes([value]))
        self.savefile.flush()

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

        omap_opt = [
            ("odelbksp",b"\x7f",b"\b",True),
            ("ocrcrlf",b"\r",b"\r\n",False),
            ("olfcrlf",b"\n",b"\r\n",False),
        ]
        imap_opt = [
            ("idelbksp",b"\x7f",b"\b",True),
            ("ilfcr",b"\n",b"\r",True),
        ]

        ctrlc_type = [
            "reset",
            "halt",
            "pass"
        ]

        ctrlc = parameters.get("ctrl-c","pass").lower()

        if ctrlc not in ctrlc_type:
            raise ValueError(f"Invalid CTRL-C bahavior: {ctrlc}")

        self.ctrlc = ctrlc_type.index(ctrlc)

        self.omap = {}

        for opt in omap_opt:
            if parameters.get(opt[0],opt[3]):
                self.omap[opt[1]] = opt[2]

        self.imap = {}
        
        for opt in imap_opt:
            if parameters.get(opt[0],opt[3]):
                self.imap[opt[1]] = opt[2]

        super().__init__(parameters, irq_callback)

    def output(self):
        mapping = self.omap
        stdout_fd = sys.stdout.fileno()
        while self.running:
            while self.tx_buffer:
                byte = bytes([self.tx_buffer.pop(0)])
                if byte in mapping:
                    byte = mapping[byte]
                os.write(stdout_fd, byte)
            sleep(0.001)

    def menu(self):
        stdin = sys.stdin
        prompt = "[N]MI [I]RQ [R]eset e[X]it [S]end []continue"
        print("\033[?1049h\r"+prompt, end="", flush=True)

        command = stdin.read(1).lower()
        if command == "i":
            self.irq_callback(0)
        elif command == "n":
            self.irq_callback(1)
        elif command == "r":
            self.irq_callback(2)
        elif command == "x":
            self.irq_callback(-1)

        print("\b"*len(prompt)+" "*(len(prompt))+"\b"*len(prompt), end="", flush=True)

        if command == "s":
            print(": ", end="", flush=True)
            termmagic.reset()
            bytes_str = stdin.readline().strip()
            termmagic.disable_buffering()
            termmagic.disable_lfcrlf()
            try:
                bytes_list = bytes.fromhex(bytes_str)
                self.rx_buffer.extend(bytes_list)
            except ValueError:
                print("Invalid")

        print("\033[?1049l", end="", flush=True)
    
    def input(self):
        mapping = self.imap
        stdin = sys.stdin
        stdin_fd = sys.stdin.fileno()
        ctrlc = self.ctrlc
        while self.running:
            selected = select.select([stdin_fd],[],[],0.01)[0]
            if not len(selected):continue
            char = os.read(stdin_fd, 1)
            if char == b"\x03":
                if ctrlc == 0:
                    self.irq_callback(2)
                    continue
                elif ctrlc == 1:
                    self.irq_callback(-1)
                    continue
            if char == b"\x01":
                self.irq_callback(-2)
                self.menu()
                self.irq_callback(-3)
                continue
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
    "nvram":Nvram,
    "rom":Rom,
    "demoled":DemoLED,
    "demobutton":DemoButton,
    "acia":ACIA,
}
