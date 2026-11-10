; Native gun silhouette: black ink, opaque white interior, clear outside.
draw_weapon:
    xor a
    ld (gun_column),a
    ld ix,gun_sprite
.column:
    ld l,(ix+0)
    ld h,(ix+1)
    ld (gun_bits),hl
    ld l,(ix+2)
    ld h,(ix+3)
    ld (gun_mask),hl
    xor a
    ld (gun_row),a
.row:
    ld hl,(gun_mask)
    srl h
    rr l
    ld (gun_mask),hl
    jr nc,.skip
    ld a,(gun_row)
    add a,VIEW_H-12
    ld b,a
    ld a,(gun_column)
    add a,VIEW_W/2-5
    ld c,a
    ld hl,(gun_bits)
    bit 0,l
    jr z,.white
    call plot
    jr .skip
.white:
    call erase
.skip:
    ld hl,(gun_bits)
    srl h
    rr l
    ld (gun_bits),hl
    ld hl,gun_row
    inc (hl)
    ld a,(hl)
    cp 12
    jr c,.row
    ld de,4
    add ix,de
    ld hl,gun_column
    inc (hl)
    ld a,(hl)
    cp 11
    jr c,.column
    ret
