render:
    ld a,(phase)
    or a
    jp z,render_title
    cp 5
    jp z,render_help
    cp 3
    jp z,render_result
    cp 4
    jp z,render_result
    cp 6
    jp z,render_cup
    call prepare_camera
    call prepare_rows
    call floor_render
    call draw_skyline
    call view_phase
    cp 7
    jp z,.intro_overlay
    ld ix,rival1_progress
    ld iy,projection1
    call project_rival
    ld ix,rival2_progress
    ld iy,projection2
    call project_rival
    call offset_grid_projection
    ld a,(projection1+1)
    ld b,a
    ld a,(projection2+1)
    cp b
    jr c,.first_far
    ld hl,projection2
    call draw_projection
    ld hl,projection1
    call draw_projection
    jr .player
.first_far:
    ld hl,projection1
    call draw_projection
    ld hl,projection2
    call draw_projection
.player:
    IF TARGET_G850
    ld a,(spin_frames)
    or a
    jr nz,.player_visible
    ld a,(hurt_frames)
    and 1
    jr nz,.skip_player
.player_visible:
    call select_player_sprite
    push af
    call arrival_offset
    add a,27
    ld e,a
    ld d,60
    pop af
    call draw_sprite_flags
.skip_player:
    ld a,(boosting)
    or a
    call nz,draw_flames
    ENDIF
.overlays:
    IF TARGET_G850
    call draw_hud
    call draw_minimap
    ENDIF
    call draw_start_prompt
    jr .messages
.intro_overlay:
    IF TARGET_G850
    ld a,(track_index)
    call track_name
    ld de,0x0000
    call draw_text
    ld hl,intro_skip_text
    ld de,0x0524
    call draw_text
    ENDIF
.messages:
    ld a,(phase)
    or a
    jp z,render_title
    cp 2
    IF TARGET_G850
    jp z,render_pause
    ENDIF
    cp 3
    jp z,render_result
    cp 4
    jp z,render_result
    ret

; HL packed sprite, A horizontal-mirror flag. Two fast four-cardinal-view turns.
select_player_sprite:
    ld a,(spin_frames)
    or a
    jr z,.ordinary
    ld b,a
    ld a,SPIN_DURATION
    sub b
    add a,a
    and 7
    jr .lookup
.ordinary:
    ld a,(control_keys)
    ld b,a
    xor a
    bit 0,b
    jr z,.not_left
    ld a,1
.not_left:
    bit 1,b
    jr z,.lookup
    ld a,7
.lookup:
player_sprite_at:
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,de
    ld de,player_sprites
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    ld a,(hl)
    ex de,hl
    ret
clear_frame:
    ld hl,frame
    ld de,frame+1
    ld bc,863
    ld (hl),0
    ldir
    ret

; IY projection [visible,depth,x,y,sprite pointer], IX rival structure.
project_rival:
    xor a
    ld (iy+0),a
    ld (iy+1),a
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+3)
    or a
    ret z
    ld a,(ix+4)
    and 1
    ret nz
    ld a,(camera_x+1)
    ld b,a
    ld a,(ix+7)
    sub b
    ld (project_dx),a
    ld d,a
    ld a,(camera_cos)
    ld e,a
    call mul_both_signed
    ld (dot_temp),hl
    ld a,(camera_y+1)
    ld b,a
    ld a,(ix+9)
    sub b
    ld (project_dy),a
    ld d,a
    ld a,(camera_sin)
    ld e,a
    call mul_both_signed
    ld de,(dot_temp)
    add hl,de
    call shift_hl_7
    ld a,h
    or a
    ret nz
    ld a,l
    cp 4
    ret c
    cp 62
    ret nc
    ld (project_depth),a
    ld (iy+1),a
    ld a,(project_dx)
    ld d,a
    ld a,(camera_sin)
    neg
    ld e,a
    call mul_both_signed
    ld (dot_temp),hl
    ld a,(project_dy)
    ld d,a
    ld a,(camera_cos)
    ld e,a
    call mul_both_signed
    ld de,(dot_temp)
    add hl,de
    call shift_hl_7
    ld d,l
    ld e,70
    call mul_signed
    ld a,h
    and 128
    ld (project_negative),a
    call nz,neg_hl
    ld a,(project_depth)
    ld c,a
    call divide_hl_c
    ld a,(project_negative)
    or a
    call nz,neg_hl
    ld de,72
    add hl,de
    ld a,h
    or a
    jr z,.positive_center
    inc a
    ret nz
    ld a,l
    cp 249                     ; largest sprite may still overlap from x=-7
    ret c
    jr .center_set
.positive_center:
    ld a,l
    cp 151
    ret nc
.center_set:
    ld (project_center),a
    ld hl,RIVAL_SCALE           ; use the larger supplied frames at grid distance
    ld a,(project_depth)
    ld c,a
    call divide_hl_c
    ld a,l
    ld b,0
    cp 5
    jr c,.sprite_set
    inc b
    cp 7
    jr c,.sprite_set
    inc b
    cp 9
    jr c,.sprite_set
    inc b
    cp 11
    jr c,.sprite_set
    inc b
    cp 15
    jr c,.sprite_set
    inc b
.sprite_set:
    ld a,b
    add a,a
    ld l,a
    ld h,0
    push ix
    pop de
    ld a,e
    cp LOW rival2_progress
    ld de,rival_a_table
    jr nz,.family_set
    ld de,rival_b_table
.family_set:
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld (iy+4),l
    ld (iy+5),h
    ld a,(hl)
    srl a
    ld b,a
    ld a,(project_center)
    sub b
    ld (iy+2),a
    inc hl
    ld a,(hl)
    ld (project_height),a
    ld hl,210
    ld a,(project_depth)
    ld c,a
    call divide_hl_c
    ld a,(project_height)
    ld b,a
    ld a,l
    add a,3
    sub b
    cp 8
    jr nc,.not_high
    ld a,8
.not_high:
    cp 36
    ret nc
    ld (iy+3),a
    ld (iy+0),1
    ret
draw_projection:
    ld a,(hl)
    or a
    ret z
    inc hl
    inc hl
    ld d,(hl)
    inc hl
    ld e,(hl)
    inc hl
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    jp draw_sprite

offset_grid_projection:
    call arrival_offset
    ld b,a
    ld a,(projection1+3)
    add a,b
    ld (projection1+3),a
    ld a,(projection2+3)
    add a,b
    ld (projection2+3),a
    ret

; HL [width,height,2bpp low-pair-first pixels], DE left/top; A=mirror for flags.
draw_sprite:
    xor a
draw_sprite_flags:
    ld (sprite_mirror),a
    ld a,(hl)
    ld (sprite_width),a
    inc hl
    ld c,(hl)
    inc hl
    ld a,(sprite_mirror)
    or a
    jr z,.positioned
    ld a,(sprite_width)
    dec a
    add a,d
    ld d,a
.positioned:
    xor a
    ld (sprite_pairs),a
    ld a,d
    ld (sprite_left),a
.row:
    ld a,(sprite_width)
    ld b,a
.column:
    ld a,(sprite_pairs)
    or a
    jr nz,.cached
    ld a,(hl)
    inc hl
    ld (sprite_bits),a
    ld a,4
    ld (sprite_pairs),a
.cached:
    ld a,(sprite_bits)
    and 3
    call nz,sprite_pixel
    ld a,(sprite_bits)
    rrca
    rrca
    ld (sprite_bits),a
    ld a,(sprite_pairs)
    dec a
    ld (sprite_pairs),a
    ld a,(sprite_mirror)
    or a
    jr nz,.backward
    inc d
    jr .advanced
.backward:
    dec d
.advanced:
    djnz .column
    ld a,(sprite_left)
    ld d,a
    inc e
    dec c
    jr nz,.row
    ret
sprite_pixel:
    push bc
    push de
    push hl
    push af
    ld a,d
    ld (plot_x),a
    cp 144
    jr nc,.skip
    ld a,e
    cp 48
    jr nc,.skip
    ld b,a
    and 7
    ld l,a
    ld h,0
    ld de,pixel_masks
    add hl,de
    ld c,(hl)
    ld a,b
    and 0x38
    rrca
    rrca
    ld l,a
    ld h,0
    ld de,frame_pages
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld a,(plot_x)
    ld l,a
    ld h,0
    add hl,de
    pop af
    cp 2
    jr z,.black
    ld a,c
    cpl
    and (hl)
    jr .write
.black:
    ld a,c
    or (hl)
.write:
    ld (hl),a
    jr .done
.skip:
    pop af
.done:
    pop hl
    pop de
    pop bc
    ret
draw_flames:
    ld a,(frame_counter)
    and 1
    ld hl,exhaust_0
    jr z,.first
    ld hl,exhaust_1
.first:
    push hl
    ld de,0x3F26
    call draw_sprite
    pop hl
    ld de,0x4B26
    jp draw_sprite

draw_skyline:
    ld a,(view_heading)
    add a,a
    and 127
    ld e,a
    ld d,0
    ld hl,skyline
    add hl,de
    ld b,a
    ld a,128
    sub b
    ld c,a
    ld b,0
    push bc
    ld de,frame
    ldir
    pop bc
    ld a,144
    sub c
    ld c,a
    ld hl,skyline
    ldir
    ret
; A track index -> HL translated NUL-terminated name.
track_name:
    add a,a
    ld l,a
    ld h,0
    ld de,track_names
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ret

; Fixed 5x7 font, one page high with one top blank pixel. DE page/pixel x.
draw_start_prompt:
    call view_phase
    cp 8
    jr z,.countdown
    ld a,(go_frames)
    or a
    ret z
    ld a,3
    jr .glyph
.countdown:
    ld a,(countdown_stage)
.glyph:
    add a,a
    ld l,a
    ld h,0
    ld de,countdown_sprites
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld a,(hl)
    ld b,a
    ld a,144
    sub b
    srl a
    ld d,a
    ld e,10
    jp draw_sprite

; Fixed 5x7 menu font, one page high. DE page/pixel x.
draw_text:
    ld a,d
    ld (text_page),a
    ld a,e
    ld (text_x),a
.next:
    ld a,(hl)
    inc hl
    or a
    ret z
    call draw_char
    jr .next
draw_char:
    push bc
    push de
    push hl
    sub 32
    cp 59
    jr nc,.done
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,hl
    add hl,de
    ld de,font_columns
    add hl,de
    push hl
    ld a,(text_page)
    add a,a
    ld l,a
    ld h,0
    ld de,frame_pages
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld a,(text_x)
    cp 139
    jr nc,.overflow
    ld l,a
    ld h,0
    add hl,de
    pop de
    ld b,5
.column:
    ld a,(de)
    add a,a
    ld (hl),a
    inc hl
    inc de
    djnz .column
    ld (hl),0
    ld a,(text_x)
    add a,6
    ld (text_x),a
    jr .done
.overflow:
    pop hl
.done:
    pop hl
    pop de
    pop bc
    ret
draw_hud:
    ld a,36
    ld (hud_x),a
    ld a,(demo_mode)
    or a
    ld a,'V'
    jr z,.speed_label
    ld a,'D'
.speed_label:
    call draw_tiny_char
    ld a,(speed)
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,de
    call draw_tiny_decimal3
    ld a,58
    ld (hud_x),a
    ld hl,lap_label
    ld a,(hl)
    call draw_tiny_char
    ld a,(lap)
    cp 4
    jr c,.lap_ok
    ld a,3
.lap_ok:
    add a,'0'
    call draw_tiny_char
    ld a,'/'
    call draw_tiny_char
    ld a,'3'
    call draw_tiny_char
    ld a,82
    ld (hud_x),a
    ld a,'P'
    call draw_tiny_char
    ld a,(rank)
    add a,'0'
    call draw_tiny_char
    ld a,'/'
    call draw_tiny_char
    ld a,'3'
    call draw_tiny_char
    ld a,102
    ld (hud_x),a
    ld a,(lap)
    cp 2
    ld a,'-'
    jr c,.boost_letter
    ld a,'B'
.boost_letter:
    call draw_tiny_char
    ld a,(energy)
    srl a
    srl a
    ld c,a
    ld a,(hurt_frames)
    and 1
    jr z,.bar
    ld c,0
.bar:
    ld hl,frame+720+113
    ld (hl),0
    inc hl
    ld (hl),0x7C
    inc hl
    ld b,25
.fill:
    ld a,0x44
    ld d,a
    ld a,c
    or a
    jr z,.empty
    dec c
    ld d,0x7C
.empty:
    ld a,(hl)
    and 1
    or d
    ld d,a
    ld (hl),d
    inc hl
    djnz .fill
    ld (hl),0x7C
    inc hl
    ld (hl),0
    ret

; Fixed y=42: 3x5 ink, local white halo. Gaps between groups retain the floor.
draw_tiny_char:
    push bc
    push de
    push hl
    sub 32
    cp 59
    jr nc,.done
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,de
    ld de,tiny_font
    add hl,de
    push hl
    ld a,(hud_x)
    dec a
    ld l,a
    ld h,0
    ld de,frame+720
    add hl,de
    push hl
    ld b,5
.halo:
    ld a,(hl)
    and 1
    ld (hl),a
    inc hl
    djnz .halo
    pop hl
    inc hl
    pop de
    ld b,3
.column:
    ld a,(de)
    add a,a
    add a,a
    or (hl)
    ld (hl),a
    inc hl
    inc de
    djnz .column
    ld a,(hud_x)
    add a,4
    ld (hud_x),a
.done:
    pop hl
    pop de
    pop bc
    ret

draw_tiny_decimal3:
    ld b,'0'
    ld de,100
.hundreds:
    or a
    sbc hl,de
    jr c,.hundreds_done
    inc b
    jr .hundreds
.hundreds_done:
    add hl,de
    ld a,b
    call draw_tiny_char
    ld b,'0'
    ld de,10
.tens:
    or a
    sbc hl,de
    jr c,.tens_done
    inc b
    jr .tens
.tens_done:
    add hl,de
    ld a,b
    call draw_tiny_char
    ld a,l
    add a,'0'
    jp draw_tiny_char

; The circuit contour has an opaque contrast halo; the rest stays transparent.
draw_minimap:
    ld a,(track_index)
    add a,a
    ld l,a
    ld h,0
    ld de,minimap_table
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld de,frame+576
    call blend_minimap_page
    push hl
    ld hl,112
    add hl,de
    ex de,hl
    pop hl
    call blend_minimap_page
    ld ix,rival1_progress
    call draw_map_rival
    ld ix,rival2_progress
    call draw_map_rival
    ld a,(player_x+1)
    ld d,a
    ld a,(player_y+1)
    ld e,a
    call map_position
    dec d
    dec e
    ld hl,map_player
    ld a,(frame_counter)
    and 4
    jr z,.player
    ld hl,map_player_flash
.player:
    jp draw_sprite
blend_minimap_page:
    ld b,32
.column:
    ld a,(de)
    and (hl)
    inc hl
    or (hl)
    inc hl
    ld (de),a
    inc de
    djnz .column
    ret
draw_map_rival:
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+3)
    or a
    ret z
    ld d,(ix+7)
    ld e,(ix+9)
    call map_position
    ld hl,map_rival
    jp draw_sprite
map_position:
    srl d
    srl d
    srl e
    srl e
    srl e
    ld a,e
    add a,32
    ld e,a
    ret

render_title:
    call clear_frame
    ld hl,title_text
    ld de,0x0021
    call draw_text
    xor a
    call invert_page
    ld a,(menu_choice)
    or a
    jr nz,.track
    ld hl,cup_info_text
    ld de,0x0112
    call draw_text
    jr .choices
.track:
    ld a,1
    ld (text_page),a
    xor a
    ld (text_x),a
    ld a,'<'
    call draw_char
    ld a,(menu_track)
    add a,'1'
    call draw_char
    ld a,(menu_track)
    call track_name
    ld de,0x0112
    call draw_text
    ld a,'>'
    call draw_char
.choices:
    ld hl,cup_option
    ld de,0x020C
    call draw_text
    ld hl,single_option
    ld de,0x030C
    call draw_text
    ld hl,demo_option
    ld de,0x040C
    call draw_text
    ld hl,menu_help_text
    ld de,0x0500
    call draw_text
    ld a,(menu_choice)
    add a,2
    jp invert_page
invert_page:
    add a,a
    ld l,a
    ld h,0
    ld de,frame_pages
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld b,144
.invert:
    ld a,(hl)
    cpl
    ld (hl),a
    inc hl
    djnz .invert
    ret
render_pause:
    ld a,(photo_mode)
    or a
    ret nz
    ld hl,pause_text
    ld de,0x0239
    call draw_text
    ld hl,resume_text
    ld de,0x0300
    call draw_text
    ld hl,photo_text
    ld de,0x042D
    jp draw_text
render_help:
    call clear_frame
    ld hl,help1
    ld de,0x0000
    call draw_text
    ld hl,help2
    ld de,0x0100
    call draw_text
    ld hl,help3
    ld de,0x0200
    call draw_text
    ld hl,help4
    ld de,0x0300
    call draw_text
    ld hl,help5
    ld de,0x0400
    call draw_text
    ld hl,help6
    ld de,0x0500
    jp draw_text
render_result:
    call clear_frame
    ld a,(phase)
    cp 3
    ld hl,finish_text
    jr z,.text
    ld hl,dead_text
.text:
    ld de,0x0018
    call draw_text
    ld a,(track_index)
    call track_name
    ld de,0x0100
    call draw_text
    call draw_scores
    ld hl,menu_return_text
    ld a,(session_mode)
    or a
    jr nz,.footer
    ld hl,next_text
    ld a,(cup_round)
    cp 2
    jr c,.footer
    ld hl,standings_text
.footer:
    ld de,0x0500
    jp draw_text
render_cup:
    call clear_frame
    ld a,(cup_place)
    cp 1
    ld hl,cup_end_text
    jr nz,.title
    ld hl,cup_win_text
.title:
    ld de,0x0006
    call draw_text
    ld hl,cup_option
    ld de,0x012A
    call draw_text
    call draw_scores
    ld hl,menu_return_text
    ld de,0x0500
    jp draw_text
draw_scores:
    xor a
    ld (result_row),a
.pilot:
    ld a,(result_row)
    add a,a
    ld l,a
    ld h,0
    ld de,pilot_names
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld a,(result_row)
    add a,2
    ld d,a
    ld e,6
    call draw_text
    ld hl,rank_label
    ld e,66
    call draw_text
    ld a,(result_row)
    ld l,a
    ld h,0
    ld de,race_places
    ld a,(phase)
    cp 6
    jr nz,.place
    ld de,cup_places
.place:
    add hl,de
    ld a,(hl)
    add a,'0'
    call draw_char
    ld a,96
    ld (text_x),a
    ld a,(phase)
    cp 6
    ld a,' '
    jr z,.sign
    ld a,'+'
.sign:
    call draw_char
    ld a,(result_row)
    ld l,a
    ld h,0
    ld de,race_points
    ld a,(phase)
    cp 6
    jr nz,.points
    ld de,cup_points
.points:
    add hl,de
    ld a,(hl)
    call draw_decimal2
    ld hl,points_text
    ld a,(result_row)
    add a,2
    ld d,a
    ld e,120
    call draw_text
    ld hl,result_row
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.pilot
    ret
draw_decimal2:
    ld l,a
    ld h,0
    ld c,10
    call divide_hl_c
    push af
    ld a,l
    add a,'0'
    call draw_char
    pop af
    add a,'0'
    jp draw_char

frame_pages:
    dw frame,frame+144,frame+288,frame+432,frame+576,frame+720
pixel_masks: db 1,2,4,8,16,32,64,128
