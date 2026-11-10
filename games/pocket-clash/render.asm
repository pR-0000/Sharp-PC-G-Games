; Native 144x40 view. Nine shared scales (8/16..16/16), masked sprites.
scale_coord:
    ld a,(zoom_n)
scale_trial:
    ld b,a
    ld d,h
    ld e,l
    ld hl,0
.multiply:
    add hl,de
    djnz .multiply
    sra h
    rr l
    sra h
    rr l
    sra h
    rr l
    sra h
    rr l
    ret
absolute_hl:
    bit 7,h
    ret z
    xor a
    sub l
    ld l,a
    sbc a,a
    sub h
    ld h,a
    ret
update_camera:
    ld hl,(fighters+FX)
    ld de,(fighters+FSIZE+FX)
    or a
    sbc hl,de
    call fixed_to_int
    call absolute_hl
    ld de,32
    add hl,de
    ld (span_x),hl
    ld hl,(fighters+FY)
    ld de,(fighters+FSIZE+FY)
    or a
    sbc hl,de
    call fixed_to_int
    call absolute_hl
    ld de,CLASH_SPAN_Y
    add hl,de
    ld (span_y),hl
    ld a,16
    ld (wanted_zoom),a
.fit:
    ld hl,(span_x)
    ld a,(wanted_zoom)
    call scale_trial
    ld de,CLASH_FIT_WIDTH
    or a
    sbc hl,de
    jr nc,.smaller
    ld hl,(span_y)
    ld a,(wanted_zoom)
    call scale_trial
    ld de,CLASH_FIT_HEIGHT
    or a
    sbc hl,de
    jr c,.fitted
.smaller:
    ld a,(wanted_zoom)
    cp CLASH_MIN_ZOOM
    jr z,.fitted
    dec a
    ld (wanted_zoom),a
    jr .fit
.fitted:
    ld a,(zoom_n)
    ld b,a
    ld a,(wanted_zoom)
    cp b
    jr z,.centre
    jr c,.zoom_out
    ld a,(frame_count)
    and 3
    jr nz,.centre
    inc b
    jr .zoom
.zoom_out:
    dec b
.zoom:
    ld a,b
    ld (zoom_n),a
.centre:
    ld hl,(fighters+FX)
    ld de,(fighters+FSIZE+FX)
    add hl,de
    sra h
    rr l
    call fixed_to_int
    ld de,8+112
    add hl,de
    sra h
    rr l                       ; gentle horizontal anchor toward the stage
    push hl
    ld a,(zoom_n)
    sub CLASH_MIN_ZOOM
    ld e,a
    ld d,0
    ld hl,half_width
    add hl,de
    ld e,(hl)
    ld d,0
    pop hl
    or a
    sbc hl,de
    ld (camera_target_x),hl
    ld hl,(fighters+FY)
    ld de,(fighters+FSIZE+FY)
    add hl,de
    sra h
    rr l
    call fixed_to_int
    ld de,8
    add hl,de
    push hl
    ld a,(zoom_n)
    sub CLASH_MIN_ZOOM
    ld e,a
    ld d,0
    ld hl,half_height
    add hl,de
    ld e,(hl)
    ld d,0
    pop hl
    or a
    sbc hl,de
    bit 7,h
    jr nz,.target_y
    ld a,(platforms+2)
    sub 8
    ld e,a
    ld d,0
    push hl
    or a
    sbc hl,de
    pop hl
    jr c,.target_y
    ex de,hl                   ; keep the ledge in view during low recoveries
.target_y:
    ld (camera_target_y),hl
    ld a,(camera_ready)
    or a
    jr nz,.ease
    inc a
    ld (camera_ready),a
    ld (camera_y),hl
    ld hl,(camera_target_x)
    ld (camera_x),hl
    ret
.ease:
    ld hl,(camera_target_x)
    ld de,(camera_x)
    call approach_camera
    ld (camera_x),hl
    ld hl,(camera_target_y)
    ld de,(camera_y)
    call approach_camera
    ld (camera_y),hl
    ret
approach_camera:
    push de
    or a
    sbc hl,de
    bit 7,h
    jr nz,.negative
    ld a,h
    or a
    jr nz,.positive_limit
    ld a,l
    cp 9
    jr c,.add
.positive_limit:
    ld hl,8
    jr .add
.negative:
    ld a,h
    cp 255
    jr nz,.negative_limit
    ld a,l
    cp 248
    jr nc,.add
.negative_limit:
    ld hl,-8
.add:
    pop de
    add hl,de
    ret

project_actor:
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    call fixed_to_int
    ld de,(camera_x)
    or a
    sbc hl,de
    call scale_coord
    ld (draw_x),hl
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    ld de,(camera_y)
    or a
    sbc hl,de
    call scale_coord
    ld (draw_y),hl
    ret

draw_game:
    ld hl,frame_buffer
    ld (hl),0
    ld de,frame_buffer+1
    ld bc,CLASH_WIDTH-1
    ldir
    ld a,(round_index)
    add a,a
    ld e,a
    ld d,0
    ld hl,background_directory
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    push hl
    ld hl,(camera_x)
    sra h
    rr l
    sra h
    rr l
    ld a,l
    and 31
    ld e,a
    ld d,0
    pop hl
    add hl,de
    ld de,frame_buffer+CLASH_WIDTH
    ld b,CLASH_BANDS
.background:
    push bc
    ld bc,CLASH_WIDTH
    ldir
    ld bc,48
    add hl,bc
    pop bc
    djnz .background
    xor a
    ld (platform_draw),a
.platform:
    ld a,(platform_draw)
    ld b,a
    add a,a
    add a,b
    ld e,a
    ld d,0
    ld hl,platforms
    add hl,de
    ld a,(hl)
    inc hl
    ld c,(hl)
    inc hl
    ld b,(hl)
    push bc
    ld l,a
    ld h,0
    ld de,(camera_x)
    or a
    sbc hl,de
    call scale_coord
    ld (line_x),hl
    pop bc
    push bc
    ld l,c
    ld h,0
    ld de,(camera_x)
    or a
    sbc hl,de
    call scale_coord
    ld (line_end),hl
    pop bc
    ld l,b
    ld h,0
    ld de,(camera_y)
    or a
    sbc hl,de
    call scale_coord
    ld (line_y),hl
    call draw_hline
    ld hl,(line_y)
    inc hl
    ld (line_y),hl
    call draw_hline
    ld hl,(line_y)
    inc hl
    inc hl
    ld (line_y),hl
    call draw_hline
    ld hl,platform_draw
    inc (hl)
    ld a,(hl)
    cp 4
    jp c,.platform
    ld ix,fighters
    call draw_fighter
    ld ix,fighters+FSIZE
    call draw_fighter
    xor a
    ld (orb_index),a
.orb:
    ld a,(orb_index)
    call orb_address
    ld (orb_pointer),hl
    ld de,5
    add hl,de
    ld a,(hl)
    or a
    jr z,.next_orb
    ld hl,(orb_pointer)
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    call fixed_to_int
    ld de,(camera_x)
    or a
    sbc hl,de
    ld de,8
    or a
    sbc hl,de
    call scale_coord
    ld (draw_x),hl
    ld hl,(orb_pointer)
    inc hl
    inc hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    call fixed_to_int
    ld de,(camera_y)
    or a
    sbc hl,de
    ld de,8
    or a
    sbc hl,de
    call scale_coord
    ld (draw_y),hl
    xor a
    ld (sprite_mirror),a
    ld a,25
    call draw_sprite
.next_orb:
    ld hl,orb_index
    inc (hl)
    ld a,(hl)
    cp 2
    jp c,.orb
    ld a,(impact_time)
    or a
    jr z,.hud
    ld hl,(impact_x)
    call fixed_to_int
    ld de,(camera_x)
    or a
    sbc hl,de
    call scale_coord
    ld (draw_x),hl
    ld hl,(impact_y)
    call fixed_to_int
    ld de,(camera_y)
    or a
    sbc hl,de
    call scale_coord
    ld (draw_y),hl
    xor a
    ld (sprite_mirror),a
    ld a,26
    call draw_sprite
.hud:
    call draw_stock_icons
    call upload_frame
    call draw_hud
    ld a,(countdown)
    or a
    jr z,.pause
    ld b,'1'
    cp 21
    jr c,.digit
    inc b
    cp 41
    jr c,.digit
    inc b
.digit:
    ld a,b
    ld de,$020B
    jp pcg_putc
.pause:
    ld a,(paused)
    or a
    ret z
    ld a,(photo_mode)
    or a
    ret nz
    ld hl,pause_text
    ld de,$0207
    jp pcg_puts

draw_fighter:
    ld a,(ix+FSTOCK)
    or a
    ret z
    ld a,(ix+FINVUL)
    and 2
    ret nz
    call project_actor
    ld b,0
    ld a,(ix+FGUARD)
    or a
    jr z,.hurt
    ld b,5
    jr .pose
.hurt:
    ld a,(ix+FSTUN)
    or a
    jr z,.attack
    ld b,4
    jr .pose
.attack:
    ld a,(ix+FATTACK)
    or a
    jr z,.jump
    ld b,3
    jr .pose
.jump:
    ld a,(ix+FGROUND)
    or a
    jr nz,.run
    ld b,2
    jr .pose
.run:
    ld a,(ix+FVX)
    or a
    jr z,.pose
    ld a,(frame_count)
    and 4
    jr z,.pose
    ld b,1
.pose:
    ld a,(ix+FCHAR)
    ld c,a
    add a,a
    add a,c
    add a,a
    add a,b
    ld b,a
    ld a,(ix+FFACE)
    ld (sprite_mirror),a
    ld a,b
    call draw_sprite
    ld a,(ix+FTYPE)
    cp 2
    ret z
    ld a,(ix+FATTACK)
    cp 5
    ret c
    ld b,10
    ld a,(ix+FTYPE)
    or a
    jr z,.slash_window
    ld b,16
.slash_window:
    ld a,(ix+FATTACK)
    cp b
    ret nc
    ld a,(zoom_n)
    srl a
    ld e,a
    ld d,0
    ld hl,(draw_x)
    ld a,(ix+FFACE)
    or a
    jr z,.slash_right
    or a
    sbc hl,de
    jr .slash
.slash_right:
    add hl,de
.slash:
    ld (draw_x),hl
    ld a,24
    jp draw_sprite

upload_frame:
    IF TARGET_G850
    ld hl,frame_buffer
    ld de,0
.row:
    ld b,CLASH_WIDTH
    call pcg_pattern
    ld bc,CLASH_WIDTH
    add hl,bc
    inc d
    ld a,d
    cp 6
    jr c,.row
    ret
    ELSE
    jp g80x_upload
    ENDIF

; line_x <= x < line_end, line_y in viewport coordinates, all edges clipped.
draw_hline:
    ld hl,(line_y)
    ld a,h
    or a
    ret nz
    ld a,l
    cp CLASH_HEIGHT
    ret nc
    and 7
    ld e,a
    ld d,0
    ld hl,bit_masks
    add hl,de
    ld c,(hl)
    ld a,(line_y)
    srl a
    srl a
    srl a
    add a,a
    ld e,a
    ld hl,buffer_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    push de
    ld hl,(line_x)
    bit 7,h
    jr z,.start
    ld hl,0
.start:
    ld a,h
    or a
    jr nz,.outside
    ld a,l
    cp CLASH_WIDTH
    jr nc,.outside
    push hl
    ld hl,(line_end)
    bit 7,h
    jr nz,.bad_end
    ld a,h
    or a
    jr nz,.limit
    ld a,l
    cp CLASH_WIDTH+1
    jr c,.end
.limit:
    ld hl,CLASH_WIDTH
.end:
    pop de
    or a
    sbc hl,de
    jr c,.outside
    ld a,h
    or l
    jr z,.outside
    ld b,l
    pop hl
    add hl,de
.pixels:
    ld a,(hl)
    or c
    ld (hl),a
    inc hl
    djnz .pixels
    ret
.bad_end:
    pop hl
.outside:
    pop hl
    ret

; A=sprite ID, width/height=zoom_n, signed draw_x/y. Mirror source columns.
draw_sprite:
    ld (sprite_id),a
    ld l,a
    ld h,0
    ld e,a
    ld d,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,de
    IF !TARGET_G850
    add hl,de
    add hl,de
    add hl,de
    add hl,de
    ENDIF
    ld a,(zoom_n)
    sub CLASH_MIN_ZOOM
    ld e,a
    add hl,de
    add hl,hl
    ld de,sprite_directory
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld de,4
    ld a,(sprite_mirror)
    or a
    jr z,.source
    ld a,(zoom_n)
    dec a
    add a,a
    add a,a
    ld e,a
    ld d,0
    add hl,de
    ld de,-4
.source:
    ld (sprite_step),de
    ld (sprite_source),hl
    xor a
    ld (sprite_clip),a
    ld (sprite_column),a
    ld (sprite_band),a
    ld (sprite_shift),a
    ld hl,(draw_y)
    bit 7,h
    jr z,.positive_y
    ld a,l
    neg
    ld b,a
    ld a,(zoom_n)
    cp b
    ret c
    ret z
    ld a,b
    ld (sprite_clip),a
    jr .column
.positive_y:
    ld a,h
    or a
    ret nz
    ld a,l
    cp CLASH_HEIGHT
    ret nc
    and 7
    ld (sprite_shift),a
    ld a,l
    srl a
    srl a
    srl a
    ld (sprite_band),a
.column:
    ld hl,(draw_x)
    ld a,(sprite_column)
    ld e,a
    ld d,0
    add hl,de
    ld a,h
    or a
    jr nz,.next
    ld a,l
    cp CLASH_WIDTH
    jr nc,.next
    push hl
    ld a,(sprite_band)
    add a,a
    ld e,a
    ld hl,buffer_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    pop hl
    add hl,de
    ld (column_address),hl
    ld hl,(sprite_source)
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    push hl
    ld a,1
    call blit_column
    pop hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    xor a
    call blit_column
.next:
    ld hl,(sprite_source)
    ld de,(sprite_step)
    add hl,de
    ld (sprite_source),hl
    ld hl,sprite_column
    inc (hl)
    ld a,(zoom_n)
    cp (hl)
    jp nz,.column
    ret
blit_column:
    ld (column_mode),a
    ld a,(sprite_clip)
    or a
    jr z,.shift
    ld b,a
.clip:
    srl d
    rr e
    djnz .clip
.shift:
    ld c,0
    ld a,(sprite_shift)
    or a
    jr z,.paint
    ld b,a
.bits:
    sla e
    rl d
    rl c
    djnz .bits
.paint:
    ld hl,(column_address)
    ld a,e
    call put_column_byte
    ld a,(sprite_band)
    cp CLASH_BANDS-1
    ret nc
    push de
    ld de,CLASH_WIDTH
    add hl,de
    pop de
    ld a,d
    call put_column_byte
    ld a,(sprite_band)
    cp CLASH_BANDS-2
    ret nc
    ld de,CLASH_WIDTH
    add hl,de
    ld a,c
put_column_byte:
    ld b,a
    ld a,(column_mode)
    or a
    ld a,b
    jr z,.ink
    cpl
    and (hl)
    ld (hl),a
    ret
.ink:
    or (hl)
    ld (hl),a
    ret
    IF TARGET_G850
buffer_rows: dw frame_buffer+144,frame_buffer+288,frame_buffer+432,frame_buffer+576,frame_buffer+720
    ELSE
buffer_rows: dw frame_buffer+120,frame_buffer+240,frame_buffer+360
    ENDIF
bit_masks: db 1,2,4,8,16,32,64,128
