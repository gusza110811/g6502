import threading
from time import sleep
import sys, os
import select
import toml65.termmagic as termmagic

class DeviceError(Exception): pass

class Device:

    def __init__(self, parameters:dict, irq_callback=None, get_device:callable=None):
        self.irq_callback = irq_callback
        self.get_device = get_device

        self.running = True

        self.name = parameters.get("name",None)

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
    def __init__(self, parameters:dict, irq_callback=None, get_device:callable=None):
        super().__init__(parameters, irq_callback, get_device)
        size = parameters.get("size",None)
        if size is None:
            raise ValueError("Ram size not defined")

        self.nonvolatile = parameters.get("nv",False)
        if self.nonvolatile:
            savefilename = parameters.get("file","nvram.img")
            if os.path.exists(savefilename):
                self.savefile = open(savefilename,"rb+")
            else:
                self.savefile = open(savefilename,"wb+")
            sizef = self.savefile.seek(0,2)
            if sizef < size:
                self.savefile.write(bytes(size-sizef))

            self.get_size = self.nvget_size
        else:
            self.memory = [0] * size

        self.banked = parameters.get("banked",False)
        if self.banked:
            self.window_id_length = parameters.get("window_id_length",None) # number of bits from MSB to use for window ID
            if self.window_id_length is None:
                raise ValueError("Banked RAM window_id_length not defined")
            self.window_id_unused = parameters.get("window_id_unused",0) # number of bits from MSB to skip before window ID
            self.bank_id_length = parameters.get("bank_id_length",None) # number of bytes for bank ID of each window in control area
            if self.bank_id_length is None:
                raise ValueError("Banked RAM bank_id_length not defined")
            control_area_name = parameters.get("control_area",None)
            if control_area_name is None:
                raise ValueError("Banked RAM control_area not defined")
            self.control_area:Ram = get_device(control_area_name)
            self.control_area_offset = parameters.get("control_area_offset",0)

            window_count = 2**(self.window_id_length-self.window_id_unused)

            #print(f"Banked RAM: {window_count} windows, {self.bank_id_length} bytes per bank. page table: {self.control_area.name}", file=sys.stderr, flush=True)

            if not isinstance(self.control_area, Ram):
                raise ValueError("Banked RAM control area must be a RAM device")
            if window_count * self.bank_id_length > self.control_area.get_size() - self.control_area_offset:
                raise ValueError("Banked RAM control area too small for defined window and bank sizes")

    def banked_getrealaddr(self, addr):
        window_id = addr >> (16-self.window_id_length+self.window_id_unused)
        window_offset = addr & ((1 << (16-self.window_id_length+self.window_id_unused))-1)
        page = self.control_area.read(self.control_area_offset + window_id * self.bank_id_length, self.bank_id_length)
        realaddr = (page << (16-self.window_id_length+self.window_id_unused)) | window_offset
        #print(f"Banked RAM: {addr:04X} -> {realaddr:04X}. id: {window_id}, page: {page} [({self.control_area_offset + window_id * self.bank_id_length:04X})]", file=sys.stderr, flush=True)
        return realaddr

    def read(self, addr, count=1):
        if self.banked:
            addr = self.banked_getrealaddr(addr)
        #print(f"RAM read: {addr:04X} (size={self.get_size():X}) from {self.name}", file=sys.stderr, flush=True)

        if addr >= self.get_size():
            return 0x00

        if self.nonvolatile:
            self.savefile.seek(addr)
            return int.from_bytes(self.savefile.read(count), byteorder='little')
        else:
            return int.from_bytes(self.memory[addr:addr+count], byteorder='little')

    def write(self, addr, value):
        if self.banked:
            addr = self.banked_getrealaddr(addr)

        if self.nonvolatile:
            self.savefile.seek(addr)
            self.savefile.write(bytes([value]))
            self.savefile.flush()
        else:
            if addr < self.get_size():
                self.memory[addr] = value

    def get_size(self):
        return len(self.memory)

    def nvget_size(self):
        self.savefile.seek(0,2)
        return self.savefile.tell()

class Rom(Device):
    def __init__(self, parameters:dict, irq_callback=None, get_device:callable=None):
        super().__init__(parameters, irq_callback, get_device)
        source = parameters.get("source","main.bin")
        if source is None:
            raise ValueError("Rom image source not defined")
        self.memory = open(source,'rb').read()
    
    def read(self, addr):
        return self.memory[addr]

    def write(self, addr, value):
        pass

class DemoLED(Device):
    def __init__(self, parameters:dict, irq_callback=None, get_device:callable=None):
        self.state = 0
        self.jobs_target = [self.run]
        super().__init__(parameters, irq_callback, get_device)

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
    def __init__(self, parameters:dict, irq_callback=None, get_device:callable=None):
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

mapping:dict[str, type] = {
    "ram":Ram,
    "rom":Rom,
    "demoled":DemoLED,
    "demobutton":DemoButton,
    "acia":ACIA,
}
