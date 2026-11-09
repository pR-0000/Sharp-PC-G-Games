; FR/EN: real two-axis, pixel-scrolled tilemapper, four seven-bit bands.
draw_game:
    call update_camera
    call render_terrain
    ld ix,cars+2*CAR_SIZE
    ld b,3
render_car:
    push bc
    ld a,b
    cp 1
    jr nz,render_car_visible
    ld a,(hit_flash)
    and 2
    jr nz,render_car_next
render_car_visible:
    call car_coords
    ld a,(car_x)
    ld l,a
    ld h,0
    ld a,(camera_x)
    add a,3
    ld e,a
    ld d,0
    or a
    sbc hl,de
    ld (draw_x),hl
    ld a,(car_y)
    ld l,a
    ld h,0
    ld a,(camera_y)
    add a,3
    ld e,a
    or a
    sbc hl,de
    ld (draw_y),hl
    ld l,(ix+4)
    ld h,0
    add hl,hl
    ld d,h
    ld e,l
    add hl,hl
    add hl,de
    add hl,hl
    add hl,de
    ld de,car_frames
    ld a,b
    cp 1
    jr z,render_car_pattern
    ld de,rival_frames
render_car_pattern:
    add hl,de
    ld b,7
    call draw_sprite
render_car_next:
    ld de,-CAR_SIZE
    add ix,de
    pop bc
    djnz render_car
    ld hl,frame_buffer
    ld de,0
    ld b,120
render_upload:
    call pcg_pattern
    push de
    ld de,120
    add hl,de
    pop de
    inc d
    ld a,d
    cp 4
    jr c,render_upload
    jp hud
update_camera:
    ld ix,cars
    call car_coords
    ld e,(ix+4)
    ld d,0
    ld hl,look_x
    add hl,de
    ld a,(hl)
    call signed_word
    ld a,(car_x)
    ld l,a
    ld h,0
    add hl,de
    ld de,50
    or a
    sbc hl,de
    ld a,92
    call camera_clamp
    ld b,a
    ld hl,camera_x
    call camera_ease
    ld e,(ix+4)
    ld d,0
    ld hl,look_y
    add hl,de
    ld a,(hl)
    call signed_word
    ld a,(car_y)
    ld l,a
    ld h,0
    add hl,de
    ld de,14
    or a
    sbc hl,de
    ld a,100
    call camera_clamp
    ld b,a
    ld hl,camera_y
    jp camera_ease
camera_clamp:
    bit 7,h
    jr nz,camera_zero
    cp l
    ret c
    ld a,l
    ret
camera_zero:
    xor a
    ret
; (HL) moves at most two pixels toward B, without overshoot.
camera_ease:
    ld a,(hl)
    cp b
    ret z
    jr c,camera_increase
    dec a
    cp b
    jr z,camera_store
    dec a
    jr camera_store
camera_increase:
    inc a
    cp b
    jr z,camera_store
    inc a
camera_store:
    ld (hl),a
    ret

; Three 48-byte row caches; each pixel uses pre-shifted column fragments.
; IX/IY/HL hold pattern pointers, DE streams directly into the framebuffer.
render_terrain:
    xor a
    ld (render_band),a
raster_band:
    ld a,(render_band)
    add a,a
    ld e,a
    ld d,0
    ld hl,buffer_rows
    call indexed_word
    ld (render_out),hl
    ld a,l
    add a,100
    ld (render_end),a
    ld a,(camera_x)
    ld b,a
    ld a,l
    sub b
    and 3
    ld (render_group_phase),a
    ld a,(render_band)
    ld b,a
    add a,a
    add a,a
    add a,a
    sub b
    ld b,a
    ld a,(camera_y)
    add a,b
    ld b,a
    and 3
    add a,a
    ld e,a
    add a,a
    add a,e
    ld e,a
    ld d,0
    ld hl,tile_phases
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    ld (render_base0),de
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    ld (render_base1),de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld (render_base2),de
    ld a,b
    srl a
    srl a
    ld (render_tile_y),a
    ld de,row_cache0
    call decode_row
    ld a,(render_tile_y)
    inc a
    ld de,row_cache1
    call decode_row
    ld a,(render_tile_y)
    add a,2
    ld de,row_cache2
    call decode_row
    ld a,(camera_x)
    ld b,a
    and 3
    ld (render_sub_x),a
    ld a,b
    srl a
    srl a
    ld (render_tile_x),a
raster_group:
    ld a,(render_tile_x)
    ld e,a
    ld d,0
    ld hl,row_cache0
    add hl,de
    ld a,(hl)
    ld hl,(render_base0)
    call pattern_pointer
    push hl
    pop ix
    ld a,(render_tile_x)
    ld e,a
    ld d,0
    ld hl,row_cache1
    add hl,de
    ld a,(hl)
    ld hl,(render_base1)
    call pattern_pointer
    push hl
    pop iy
    ld a,(render_tile_x)
    ld e,a
    ld d,0
    ld hl,row_cache2
    add hl,de
    ld a,(hl)
    ld hl,(render_base2)
    call pattern_pointer
    ld de,(render_out)
raster_column:
    ld a,(ix+0)
    inc ix
    ld c,a
    ld a,(iy+0)
    inc iy
    or c
    ld c,a
    ld a,(hl)
    inc hl
    or c
    ld (de),a
    inc de
    ld a,(render_end)
    cp e
    jr z,raster_next_band
    ld a,e
    and 3
    ld b,a
    ld a,(render_group_phase)
    cp b
    jr nz,raster_column
    ld (render_out),de
    xor a
    ld (render_sub_x),a
    ld hl,render_tile_x
    inc (hl)
    jp raster_group
raster_next_band:
    ld hl,render_band
    inc (hl)
    ld a,(hl)
    cp 4
    jp c,raster_band
    ret
; HL = shifted pattern table; A = tile ID.
pattern_pointer:
    add a,a
    add a,a
    ld e,a
    ld a,(render_sub_x)
    add a,e
    ld e,a
    ld d,0
    add hl,de
    ret


