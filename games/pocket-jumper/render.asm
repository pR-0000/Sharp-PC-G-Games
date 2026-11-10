; FR/EN: clipped shared column blitter; band geometry comes from the target.
draw_game:
    call update_camera
    ld hl,frame_buffer
    ld de,frame_buffer+1
    ld bc,PCG_FRAME_BYTES-1
    ld (hl),0
    ldir
    ld hl,(camera_x)
    srl h
    rr l
    ld a,25
    sub l
    and 127
    ld l,a
    ld h,0
    ld (draw_x),hl
    ld hl,1
    ld (draw_y),hl
    ld hl,cloud
    ld b,12
    call draw_sprite
    IF TARGET_G850
    call draw_background
    ENDIF
    ld hl,(camera_x)
    ld a,l
    and 7
    neg
    ld (render_start_x),a
    ld hl,(camera_x)
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld a,l
    ld (render_first_x),a
    ld a,(camera_y)
    and 7
    neg
    ld (render_start_y),a
    ld a,(camera_y)
    srl a
    srl a
    srl a
    ld (render_first_y),a
    xor a
    ld (render_row),a
render_map_row:
    xor a
    ld (render_column),a
render_map_column:
    ld a,(render_first_x)
    ld b,a
    ld a,(render_column)
    add a,b
    ld b,a
    ld a,(render_first_y)
    ld c,a
    ld a,(render_row)
    add a,c
    ld c,a
    call tile_at
    or a
    jr z,render_map_next
    add a,a
    ld e,a
    ld d,0
    ld hl,tile_patterns
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    push de
    ld a,(render_column)
    add a,a
    add a,a
    add a,a
    ld b,a
    ld a,(render_start_x)
    call signed_plus_b
    ld (draw_x),hl
    ld a,(render_row)
    add a,a
    add a,a
    add a,a
    ld b,a
    ld a,(render_start_y)
    call signed_plus_b
    ld (draw_y),hl
    pop hl
    ld b,8
    call draw_sprite
render_map_next:
    ld hl,render_column
    inc (hl)
    ld a,(hl)
    cp RENDER_COLS
    jr c,render_map_column
    ld hl,render_row
    inc (hl)
    ld a,(hl)
    cp RENDER_ROWS
    jr c,render_map_row
    ld ix,enemies
    ld b,4
render_enemy:
    push bc
    ld a,(ix+8)
    or a
    jr z,render_enemy_next
    ld l,(ix+0)
    ld h,(ix+1)
    ld de,(camera_x)
    or a
    sbc hl,de
    ld (draw_x),hl
    ld a,(camera_y)
    ld b,a
    ld a,(ix+2)
    sub b
    call velocity_word
    ld (draw_y),de
    ld hl,enemy
    ld b,10
    call draw_sprite
render_enemy_next:
    ld de,9
    add ix,de
    pop bc
    djnz render_enemy
    ld a,(grace)
    and 2
    jr nz,render_upload
    ld hl,(player_x)
    call fixed_to_int
    ld de,(camera_x)
    or a
    sbc hl,de
    ld (draw_x),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,(camera_y)
    ld e,a
    ld d,0
    or a
    sbc hl,de
    ld (draw_y),hl
    ld hl,hero_a
    ld a,(frame_count)
    and 4
    jr z,render_hero_direction
    ld hl,hero_b
render_hero_direction:
    ld a,(facing_left)
    or a
    jr z,render_hero
    ld de,24
    add hl,de
render_hero:
    ld b,12
    call draw_sprite
render_upload:
    ld hl,frame_buffer
    ld de,0
    ld b,PCG_ROW_COLUMNS
render_upload_row:
    call pcg_pattern
    push de
    ld de,PCG_ROW_COLUMNS
    add hl,de
    pop de
    inc d
    ld a,d
    cp PCG_LCD_ROWS
    jr c,render_upload_row
    jp hud
; Signed A plus unsigned B -> HL.
signed_plus_b:
    call velocity_word
    ld l,b
    ld h,0
    add hl,de
    ret
update_camera:
    ld hl,(player_x)
    call fixed_to_int
    ld de,CAMERA_LEAD
    or a
    sbc hl,de
    jr nc,camera_right
    ld hl,0
camera_right:
    ld de,WORLD_W-VIEW_W
    or a
    sbc hl,de
    jr c,camera_restore
    ld hl,0
camera_restore:
    add hl,de
    ld (camera_x),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,(camera_y)
    add a,4
    cp l
    jr c,camera_down
    ld a,l
    sub 4
    jr nc,camera_limit_y
    xor a
    jr camera_store_y
camera_down:
    ld a,(camera_y)
    add a,VIEW_H-HERO_H-4
    cp l
    ret nc
    ld a,l
    sub VIEW_H-HERO_H-4
camera_limit_y:
    cp CAMERA_MAX_Y+1
    jr c,camera_store_y
    ld a,CAMERA_MAX_Y
camera_store_y:
    ld (camera_y),a
    ret

; HL = words of vertical pixel bits, B = width, draw_x/y signed pixels.
; Output uses the target pixel mask. IX/IY are preserved.
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
    cp VIEW_H
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
    cp VIEW_W
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
    cp VIEW_PAGES-1
    jr nc,sprite_column_done
    push de
    ld de,PCG_ROW_COLUMNS
    add hl,de
    pop de
    IF TARGET_G850
    ld a,d
    ELSE
    rlc e
    ld a,d
    rla
    and PCG_GLYPH_MASK
    ENDIF
    or (hl)
    ld (hl),a
    ld a,(sprite_band)
    cp VIEW_PAGES-2
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

    IF TARGET_G850
draw_background:
    ld hl,(camera_x)
    srl h
    rr l
    srl h
    rr l
    ld a,110
    sub l
    and 127
    ld l,a
    ld h,0
    ld (draw_x),hl
    ld hl,3
    ld (draw_y),hl
    ld hl,sun
    ld b,8
    call draw_sprite
    ld hl,(camera_x)
    srl h
    rr l
    ld a,92
    sub l
    and 127
    ld l,a
    ld h,0
    ld (draw_x),hl
    ld hl,7
    ld (draw_y),hl
    ld hl,cloud
    ld b,12
    call draw_sprite
    ld hl,(camera_x)
    srl h
    rr l
    srl h
    rr l
    ld a,60
    sub l
    and 127
    ld l,a
    ld h,0
    ld (draw_x),hl
    ld hl,24
    ld (draw_y),hl
    ld hl,hills
    ld b,16
    jp draw_sprite
    ENDIF
