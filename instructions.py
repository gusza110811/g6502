class Instruction:
    BRK = 0x00

    LDA_IMM = 0xA9
    LDA_ZP = 0xA5
    LDA_ZPX = 0xB5
    LDA_ABS = 0xAD
    LDA_ABSX = 0xBD
    LDA_ABSY = 0xB9
    LDA_INDX = 0xA1
    LDA_INDY = 0xB1

    STA_ZP = 0x85
    STA_ZPX = 0x95
    STA_ABS = 0x8D
    STA_ABSX = 0x9D
    STA_ABSY = 0x99
    STA_INDX = 0x81
    STA_INDY = 0x91
