; G850 IOCS wrappers. Include sharp_pc_g850.inc first; include this once.
; FR/EN: preserve AF/BC/DE/HL/IX/IY for output; alternate regs undefined.
; Key scan returns A and Z=(A==0), preserving BC/DE/HL/IX/IY.
; No bank changes, system RAM work areas, DI/EI or stack replacement.

pcg850_key_scan:
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG850_IOCS_KEY_SCAN
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    and PCG850_KEY_BASE_MASK
    ret

pcg850_putc:
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG850_IOCS_PUTC
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

pcg850_pattern:
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG850_IOCS_PATTERN
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

pcg850_clear:
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    ld de,0
.row:
    push de
    ld a,PCG850_ASCII_SPACE
    ld b,PCG850_LCD_COLS
    call PCG850_IOCS_REPEAT
    pop de
    inc d
    ld a,d
    cp PCG850_LCD_ROWS
    jr c,.row
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

pcg850_blit:
    ; HL -> 864-byte page buffer. Upload six rows through public IOCS.
    push af
    push bc
    push de
    push hl
    ld de,0
.page:
    ld b,PCG850_FRAME_STRIDE
    call pcg850_pattern
    push de
    ld de,PCG850_FRAME_STRIDE
    add hl,de
    pop de
    inc d
    ld a,d
    cp PCG850_FRAME_PAGES
    jr c,.page
    pop hl
    pop de
    pop bc
    pop af
    ret
