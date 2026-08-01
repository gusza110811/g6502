# TOML-6502 Virtual Machine
The TOML-6502 virtual machine is a software emulator that simulates the behavior of a 65c02 microprocessor and its associated hardware components. It allows users to run programs written for the 65c02 architecture on modern computers.

## Command Line Interface

    toml-6502 [-h] [-m] [-M] [options] <config_file>

flags:
- `-h`, `--help`: Show help message and exit.
- `-m`, `--dump`: Dump the memory to terminal on halt
- `-M`, `--monitor`: Start the emulator in monitor mode (interactive mode).

options is a list of key-value pairs in the form of `NAME=VALUE`, where `NAME` is the name of the constant and `VALUE` is its value. Matching `NAME` in the configuration file will be overridden by the command line options.

## Runtime Commands
The TOML-6502 virtual machine supports a set of runtime commands that can be used to control the execution of the emulator. These commands can be entered in the terminal while the emulator is running. The following is a list of available commands:
- `^A N`: Trigger a Non-Maskable Interrupt (NMI).
- `^A I`: Trigger an Interrupt Request (IRQ).
- `^A R`: Reset the emulator.
- `^A X`: Exit the emulator.
- `^A S`: Send bytes to the emulator. The user will be prompted to enter a string of hexadecimal bytes, which will be sent to the emulator's input buffer.

## CTRL-C Behavior
The behavior of the emulator when Ctrl-C is pressed can be configured in the configuration file. The available options are:
- `reset`: Reset the emulator.
- `halt`: Halt the emulator.
- `pass`: Pass the Ctrl-C signal to the emulator's input buffer. (Default)
