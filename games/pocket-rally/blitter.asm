; HL = words of vertical pixel bits, B = width, draw_x/y signed pixels.
; Every output byte is masked to seven bits. IX/IY are preserved.
draw_sprite:
    ld (sprite_source),hl
    ld a,b
    ld (sprite_width),a
    xor a
    ld (sprite_column),a
    ld (sprite_clip),a
    ld (sprite_band),a
    ld (sprite_shift),a
    ld hl,(draw_y)
    bit 7,h
    jr z,sprite_positive_y
    ld a,l
    neg
    cp 12
    ret nc
    ld (sprite_clip),a
    jr sprite_next_column
sprite_positive_y:
    ld a,h
    or a
    ret nz
    ld a,l
    cp RALLY_HEIGHT
    ret nc
    ld b,0
sprite_y_divide:
    cp PCG_GLYPH_HEIGHT
    jr c,sprite_y_ready
    sub PCG_GLYPH_HEIGHT
    inc b
    jr sprite_y_divide
sprite_y_ready:
    ld (sprite_shift),a
    ld a,b
    ld (sprite_band),a
sprite_next_column:
    ld hl,(draw_x)
    ld a,(sprite_column)
    ld e,a
    ld d,0
    add hl,de
    ld a,h
    or a
    jp nz,sprite_column_done
    ld a,l
    cp RALLY_WIDTH
    jp nc,sprite_column_done
    push hl
    ld a,(sprite_band)
    add a,a
    ld e,a
    ld d,0
    ld hl,buffer_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    pop hl
    add hl,de
    push hl
    ld hl,(sprite_source)
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld a,(sprite_clip)
    or a
    jr z,sprite_no_clip
    ld b,a
sprite_clip_loop:
    srl d
    rr e
    djnz sprite_clip_loop
sprite_no_clip:
    ld c,0
    ld a,(sprite_shift)
    or a
    jr z,sprite_bits_ready
    ld b,a
sprite_shift_loop:
    sla e
    rl d
    rl c
    djnz sprite_shift_loop
sprite_bits_ready:
    pop hl
    ld a,e
    and PCG_GLYPH_MASK
    or (hl)
    ld (hl),a
    ld a,(sprite_band)
    cp RALLY_PAGES-1
    jr nc,sprite_column_done
    push de
    ld de,PCG_ROW_COLUMNS
    add hl,de
    pop de
    IF !TARGET_G850
    rlc e
    ENDIF
    ld a,d
    IF !TARGET_G850
    rla
    ENDIF
    and PCG_GLYPH_MASK
    or (hl)
    ld (hl),a
    ld a,(sprite_band)
    cp RALLY_PAGES-2
    jr nc,sprite_column_done
    push de
    ld de,PCG_ROW_COLUMNS
    add hl,de
    pop de
    IF TARGET_G850
    ld a,c
    ELSE
    ld a,d
    rlca
    rlca
    and 3
    ld b,a
    ld a,c
    add a,a
    add a,a
    or b
    and PCG_GLYPH_MASK
    ENDIF
    or (hl)
    ld (hl),a
sprite_column_done:
    ld hl,(sprite_source)
    inc hl
    inc hl
    ld (sprite_source),hl
    ld hl,sprite_column
    inc (hl)
    ld a,(sprite_width)
    cp (hl)
    jp nz,sprite_next_column
    ret

