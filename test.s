    .org $8000

reset:
    lda #$50
    sta $04
    brk

vectors:
    .org $fffc
    .word reset
    .word $0000
