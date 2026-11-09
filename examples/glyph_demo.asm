; Minimal G801 IOCS check before trying the game. No direct hardware IO.
; G100 draws three software glyphs, waits for Q/BREAK, returns with RET.
    INCLUDE "sharp_pc_g801.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 1
    ENDIF
    ORG PCG_USER_ORIGIN
entry:
    push ix
    push iy
    call pcg_clear
    ld hl,message
    ld de,0
    call pcg_puts
    ld hl,ship
    ld de,0x0103
    call pcg_glyph
    ld hl,rock
    ld de,0x0106
    call pcg_glyph
    ld hl,star
    ld de,0x0109
    call pcg_glyph
    ld hl,quit_message
    ld de,0x0300
    call pcg_puts
.wait:
    call pcg_key_scan
    cp PCG_KEY_Q
    jr z,.exit
    cp PCG_KEY_BREAK
    jr nz,.wait
.exit:
    pop iy
    pop ix
    ret
    INCLUDE "../lib/pcg801_runtime.asm"
    IF BUILD_LANG_EN
message:      db "PC-G801 GLYPH TEST",0
quit_message: db "Q / BREAK : RETURN",0
    ELSE
message:      db "PC-G801 TEST DE MOTIFS",0
quit_message: db "Q / BREAK : RETOUR",0
    ENDIF
ship: db 0x14,0x3E,0x7F,0x1C,0x08
rock: db 0x3E,0x77,0x63,0x77,0x3E
star: db 0x2A,0x1C,0x7F,0x1C,0x2A
program_end:
