    .org $8000

reset:
    lda #$ff
    sta $6002

    lda #$0
    sta $6000

    sei

loop:
    jmp loop

int:
    adc #1
    sta $6000

    rti

vector:
    .org $fffc
    .word reset
    .word int
