; Runtime Q8.8 floorcaster, 2x1 samples, all world reads executed by Z80.
; Quarter-turn symmetry stores 16 headings, 40 scanlines each (5 KiB).
prepare_camera:
    ld a,(heading)
    ld (view_heading),a
    ld a,10
    ld (camera_distance),a
    ld hl,(player_x)
    ld (camera_center_x),hl
    ld hl,(player_y)
    ld (camera_center_y),hl
    call view_phase
    cp 7
    jr nz,.follow
    ld a,(intro_angle)
    ld (view_heading),a
    ld a,24
    ld (camera_distance),a
    ld hl,(intro_center_x)
    ld (camera_center_x),hl
    ld hl,(intro_center_y)
    ld (camera_center_y),hl
.follow:
    ld a,(view_heading)
    call get_direction
    ld a,d
    ld (camera_cos),a
    ld a,e
    ld (camera_sin),a
    ld a,(camera_distance)
    ld e,a
    call mul_signed
    ex de,hl
    ld hl,(camera_center_x)
    or a
    sbc hl,de
    ld (camera_x),hl
    ld a,(camera_sin)
    ld d,a
    ld a,(camera_distance)
    ld e,a
    call mul_signed
    ex de,hl
    ld hl,(camera_center_y)
    or a
    sbc hl,de
    ld (camera_y),hl
    ret
prepare_rows:
    ld a,(view_heading)
    ld b,a
    rrca
    rrca
    rrca
    rrca
    and 3
    ld (camera_quadrant),a
    ld a,b
    and 15
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    ld e,l
    ld d,h
    add hl,hl
    add hl,hl
    add hl,de
    add hl,hl
    add hl,hl
    add hl,hl
    IF TARGET_G850
    add hl,hl
    ENDIF
    ld de,perspective_offsets
    add hl,de
    push hl
    pop ix
    ld iy,row_table
    ld a,FLOOR_SCANLINES
    ld (rows_to_prepare),a
.row:
    ld l,(ix+0)
    ld h,(ix+1)
    ld e,(ix+2)
    ld d,(ix+3)
    call rotate_pair
    ld bc,(camera_x)
    add hl,bc
    ld (iy+0),l
    ld (iy+1),h
    ex de,hl
    ld bc,(camera_y)
    add hl,bc
    ld (iy+2),l
    ld (iy+3),h
    ld l,(ix+4)
    ld h,(ix+5)
    ld e,(ix+6)
    ld d,(ix+7)
    call rotate_pair
    ld (iy+4),l
    ld (iy+5),h
    ld (iy+6),e
    ld (iy+7),d
    ld bc,8
    add ix,bc
    add iy,bc
    ld hl,rows_to_prepare
    dec (hl)
    jr nz,.row
    ret
rotate_pair:
    ld a,(camera_quadrant)
    or a
    ret z
    ld b,a
.turn:
    ex de,hl
    call neg_hl
    djnz .turn
    ret

floor_render:
    call clear_frame
    ld hl,frame+144
    ld (floor_band),hl
    IF TARGET_G850
    ld a,1
    ELSE
    ld a,3
    ENDIF
    ld (floor_bit+1),a
    ld a,FLOOR_SCANLINES
    ld (floor_rows),a
    ld ix,row_table
.scanline:
    ld l,(ix+0)
    ld h,(ix+1)
    ld e,(ix+4)
    ld d,(ix+5)
    exx
    ld l,(ix+2)
    ld h,(ix+3)
    ld e,(ix+6)
    ld d,(ix+7)
    ld b,72
    exx
    ld iy,(floor_band)
.sample:
    ld a,h
    rrca
    rrca
    rrca
    and 15
    ld c,a
    exx
    ld a,h
    exx
    ld b,a
    and 15
    rlca
    rlca
    rlca
    rlca
    or c
    ld c,a
    ld a,b
    rrca
    rrca
    rrca
    rrca
    and 7
    add a,HIGH texture_map
    ld b,a
    ld a,(bc)
    ex af,af'
    ld a,h
    and 7
    ld c,a
    ld b,HIGH texture_masks
    ld a,(bc)
    ld b,a
    ex af,af'
    and b
    jr z,floor_bit.white
    ld a,(iy+0)
floor_bit:
    or 1
    ld (iy+0),a
    ld (iy+1),a
.white:
    inc iy
    inc iy
    add hl,de
    exx
    add hl,de
    djnz .next_sample
    exx
    ld a,(floor_bit+1)
    rlca
    IF !TARGET_G850
    rlca
    ENDIF
    ld (floor_bit+1),a
    jr nc,.same_band
    ld hl,(floor_band)
    ld de,144
    add hl,de
    ld (floor_band),hl
.same_band:
    ld bc,8
    add ix,bc
    ld a,(floor_rows)
    dec a
    ld (floor_rows),a
    jp nz,floor_render.scanline
    ret
.next_sample:
    exx
    jp floor_render.sample
