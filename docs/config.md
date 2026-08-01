# TOML-6502 configuration format

The configuration file for the TOML-6502 emulator is written in TOML (Tom's Obvious, Minimal Language) format. This file defines the hardware components and their properties for the emulator.

## General Configuration
- `clock`: The clock speed of the emulator in Hertz (Hz). This value determines how fast the emulator runs. Default is as fast as possible.
- `static`: Determine if the configuration is to be used in a specific environment (change directory to the configuration file's directory) or if it should be dynamic (stay in current directory). Default is `true`.

## Device Configuration

Each device in the emulator is configured with a set of parameters. The following is a list of available devices and their respective parameters:

### Base
- `type`: The type of the device (e.g., "RAM", "ROM", "ACIA", "DemoLED", "DemoButton").
- `match`: The match pattern for the mmio
- `match_mask`: The match mask for the mmio
- `address_mask`: The exposed address mask to the device

### RAM
- `size`: The size of the RAM in bytes.

### ROM
- `source`: The path to the ROM file.

### ACIA
- `ctrl-c`: The behavior of the emulator when Ctrl-C is pressed. Options are "reset", "halt", or "pass".
- `ocrcrlf`: Map TX `CR` to `CRLF`. Default is `false`.
- `olfcrlf`: Map TX `LF` to `CRLF`. Default is `false`.
- `odelbksp`: Map TX `DEL` to `BS`. Default is `true`.
- `idelbksp`: Map RX `DEL` to `BS`. Default is `true`.
- `ilfcr`: Map RX `LF` to `CR`. Default is `true`.

## [options] field
List of constants that can be used in the configuration file.

In the form of `NAME = VALUE`, where `NAME` is the name of the constant and `VALUE` is its value. The constants can be used in the configuration file to define device parameters. For every string value elsewhere in the configuration file that starts with a `$`, the value of the constant with the same name will be substituted. For example, if you have a constant `ROM_PATH = "/path/to/rom"`, you can use `$ROM_PATH` in the configuration file to refer to that path.
