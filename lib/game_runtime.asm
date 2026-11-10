; Shared public-IOCS interface; include game_platform.inc before this file.
; FR/EN: preserve the original G80X implementation and use G850 wrappers.
    IF TARGET_G850
    INCLUDE "pcg850_runtime.asm"
pcg_key_scan EQU pcg850_key_scan
pcg_putc EQU pcg850_putc
pcg_pattern EQU pcg850_pattern
pcg_clear EQU pcg850_clear
pcg_glyph:
    push bc
    ld b,5                   ; existing five-column HUD icons, not a ROM cell
    call pcg_pattern
    pop bc
    ret
pcg_puts:
    push af
    push bc
    push de
    push hl
.next:
    ld a,e
    cp PCG_LCD_COLS
    jr nc,.done
    ld a,(hl)
    or a
    jr z,.done
    call pcg_putc
    inc hl
    inc e
    jr .next
.done:
    pop hl
    pop de
    pop bc
    pop af
    ret
    ELSE
    INCLUDE "pcg801_runtime.asm"
    ENDIF
