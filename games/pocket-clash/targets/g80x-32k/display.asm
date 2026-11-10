; Repack the 8-bit internal view into three seven-bit LCD rows.
; Pixel y=7 and y=14 continue on the next glyph row, with no lost source row.
g80x_upload:
    ld hl,frame_buffer
    ld de,lcd_frame
    ld bc,120
    ldir
    ld ix,frame_buffer+240
    ld iy,lcd_frame+240
    ld b,120
.column:
    ld a,(ix-120)
    and 127
    ld (iy-120),a
    ld a,(ix-120)
    rlca
    and 1
    ld c,a
    ld a,(ix+0)
    add a,a
    or c
    and 127
    ld (iy+0),a
    ld a,(ix+0)
    rlca
    rlca
    and 3
    ld c,a
    ld a,(ix+120)
    add a,a
    add a,a
    or c
    and 127
    ld (iy+120),a
    inc ix
    inc iy
    djnz .column
    ld hl,lcd_frame
    ld de,0
.row:
    ld b,120
    call pcg_pattern
    ld bc,120
    add hl,bc
    inc d
    ld a,d
    cp 4
    jr c,.row
    ret
