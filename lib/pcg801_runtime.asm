; Small conservative IOCS wrappers. Include ONCE after your program code.
; FR : wrappers IOCS préservant les registres ; inclure UNE fois après le code.
; Include sharp_pc_g801.inc before this file. MIT licence.
; All wrappers preserve BC, DE, HL, IX, IY. Alternate registers undefined.
; Output wrappers also preserve AF. Scan returns A and Z=(A==0), other
; flags undefined. No system RAM pointers, stack replacement or DI/EI.

pcg_key_scan:
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG_IOCS_KEY_SCAN
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    and PCG_KEY_BASE_MASK
    ret

pcg_putc:                         ; A = ASCII, DE = cell
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG_IOCS_PUTC
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

pcg_pattern:                      ; HL -> B columns, DE = cell
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG_IOCS_PATTERN
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

pcg_glyph:                        ; HL -> five columns, DE = cell
    push bc
    ld b,PCG_GLYPH_WIDTH
    call pcg_pattern
    pop bc
    ret

pcg_clear:                        ; clear four rows; preserves AF too
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    ld de,0
.row:
    push de
    ld a,PCG_ASCII_SPACE
    ld b,PCG_LCD_COLS
    call PCG_IOCS_REPEAT
    pop de
    inc d
    ld a,d
    cp PCG_LCD_ROWS
    jr c,.row
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

    IFNDEF PCG_RUNTIME_NO_PUTS
pcg_puts:                         ; HL -> NUL string, DE = cell
    push af                      ; clip at col 24, NEVER scroll
    push bc
    push de
    push hl
.loop:
    ld a,e
    cp PCG_LCD_COLS
    jr nc,.done
    ld a,(hl)
    or a
    jr z,.done
    call pcg_putc
    inc hl
    inc e
    jr .loop
.done:
    pop hl
    pop de
    pop bc
    pop af
    ret
    ENDIF
