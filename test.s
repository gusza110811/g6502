    .org $8000

reset:
    lda #$ff
    sta $6002

    lda #$50
    sta $6000

loop:
    ror A
    sta $6000

    jmp loop

    .org $fffc
    .word reset
    .word $0000
