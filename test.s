    .org $8000

reset:
    lda #$F0

loop:
    sta $200,x
    inx
    bne loop

    brk

vectors:
    .org $fffc
    .word reset
    .word $0000
