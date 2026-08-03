#!/usr/bin/env python3

# COPYING – Summary of Licensing Terms

# Copyright (c) 2026 Slava "Gusza" Nikolsky

# You are permitted to use this software for free, forever, for any lawful purpose.

# However, you are NOT permitted to:
# 1. Redistribute this software (or any modified versions) under a different name.
# 2. Redistribute this software (or any modified versions) for commercial purposes or for profit.

# The software is provided "AS IS", without any warranties or guarantees of any kind.

# For full legal terms, please refer to the LICENSE file.

import toml65.memory as memory
from py65.devices import mpu65c02 as core
from py65 import monitor as Monitor
import math
import time
import tomllib
import argparse
import os, sys
import toml65.termmagic as termmagic

A, X, Y, SP, PC, P = range(6)

class VM:
    UNPAUSE=-3
    PAUSE=-2
    HALT=-1
    IRQ=0
    NMI=1
    RESET=2
    
    def __init__(self, bus_definition:dict):
        self.running = True
        self.memory = memory.Bus(self.interrupt, bus_definition)
        acia_exists = False
        for device in self.memory.devices:
            if device.__class__.__name__ == "ACIA":
                acia_exists = True
                break
        if not acia_exists:
            raise ValueError("ACIA device must be defined for normal emulation")

        self.cpu = core.MPU(self.memory, pc=None)
        self.delay = 0.0

        clock = bus_definition.get("clock",None)

        if clock:
            if isinstance(clock,int):
                pass
            else:
                clock = clock.lower()
            if clock.endswith("k"):
                clock = int(clock[:1])*10**3
            elif clock.endswith("m"):
                clock = int(clock[:1])*10**6
            elif clock.endswith("g"):
                clock = int(clock[:1])*10**9
            else:
                clock = int(clock)

            self.delay = 1/clock

        self.interrupt_request = False
        self.reset_request = False
        self.pause_request = False
        self.paused = False

    def interrupt(self, type:int=0):
        match type:
            case self.IRQ:
                self.interrupt_request = True
            case self.RESET:
                self.reset_request = True
            case self.PAUSE:
                self.pause_request = True
                while not self.paused:
                    continue
            case self.UNPAUSE:
                self.pause_request = False
            case self.HALT:
                self.running = False

    def main(self):
        delay = self.delay
        cpu = self.cpu
        while self.running:
            cpu.step()
            if self.interrupt_request:
                cpu.irq()
                self.interrupt_request = False
            if self.reset_request:
                cpu.reset()
                self.reset_request = False

            if self.pause_request:
                self.paused = True
                while self.pause_request:
                    pass
                self.paused = False

            timer = time.perf_counter()
            while timer + delay > time.perf_counter():
                pass


    def dump_registers(self):
        print(repr(self.cpu))
    
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

def main():
    def replace(item:dict|list|str|int|bool,options:dict[str,str]):

        if isinstance(item,dict):
            for key,value in item.items():
                item[key] = replace(value,options)
            return item
        elif isinstance(item,list):
            for idx,value in enumerate(item):
                item[idx] = replace(value,options)
            return item
        elif isinstance(item, str):
            if not item.startswith("$"):
                result = item
            else:
                key = item[1:]
                result = options.get(key)
                if not result:
                    raise ValueError(f"key {key} undefined or empty")
            try:
                return int(item,0)
            except ValueError:
                return result
        else:
            return item


    argparser = argparse.ArgumentParser()

    argparser.add_argument("config", default="./config.toml", help="bus definition", nargs="?")
    argparser.add_argument("-m","--dump",action="store_true", help="dump memory at the end of execution")
    argparser.add_argument("-M","--monitor",action="store_true", help="run monitor instead of regular execution")
    argparser.add_argument("options",nargs="*",help="")

    args = argparser.parse_args()

    try:
        busdef = tomllib.load(open(args.config,"rb"))
    except FileNotFoundError:
        sys.exit(f"{args.config} doesnt exist")
    opts:list[str] = args.options
    options = busdef.get("options",{})
    for field in opts:
        sep = field.find("=")
        options[field[:sep]] = field[sep+1:]

    try:
        replace(busdef,options)
    except ValueError as v:
        sys.exit(v)

    monitor = args.monitor
    dump = args.dump

    if busdef.get("static",True):
        os.chdir(os.path.dirname(args.config))
    emu = VM(busdef)

    if monitor:
        monitor = Monitor.Monitor([],mpu_type=core.MPU,memory=emu.memory)
        monitor.prompt = ":"

        def precmd(line):
            termmagic.disable_buffering()
            #termmagic.disable_lfcrlf()
            emu.memory.startall()
            sys.stdin.flush()
            return line
        monitor.precmd = precmd
        def postcmd(stop, line):
            termmagic.reset()
            emu.memory.killall()
            return stop
        monitor.postcmd = postcmd

        emu.memory.killall()

        monitor.cmdloop()

    else:
        termmagic.disable_buffering()
        termmagic.disable_lfcrlf()
        print("^A X to exit\r\n\r\n")
        try:
            emu.memory.startall()
            emu.main()
        except KeyboardInterrupt:
            pass
        finally:
            termmagic.reset()
            emu.memory.killall()
    termmagic.reset()
    if dump:
        emu.dump_registers()
        emu.dump_memory(0x0000, 0xFFFF)

if __name__ == "__main__":
    main()
