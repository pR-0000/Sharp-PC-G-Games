; G80X 32 KiB: 120x28 useful pixels, four native seven-bit bands.
; Shared world renderer, 2x2 floor samples, native HUD/text/minimap.
g80x_show_frame:
    ld hl,lcd_frame
    ld de,lcd_frame+1
    ld bc,479
    ld (hl),0
    ldir
    ld a,(phase)
    or a
    jp z,g80x_title
    cp 5
    jp z,g80x_help
    cp 3
    jp z,g80x_result
    cp 4
    jp z,g80x_result
    cp 6
    jp z,g80x_result
    call render
    call g80x_sample_view
    call g80x_player
    call g80x_hud
    call g80x_minimap
    ld a,(phase)
    cp 2
    jr nz,g80x_upload
    ld a,(photo_mode)
    or a
    jr nz,g80x_upload
    ld hl,pause_text
    ld de,$0128
    call g80x_puts
    ld hl,resume_text
    ld de,$0300
    call g80x_puts
g80x_upload:
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

; Centre-sample the shared 144x40 camera into a 120x21 scene below the HUD.
; Row address/mask tables preserve every destination bit across 7-bit cells.
g80x_sample_view:
    ld ix,g80x_sample_rows
    ld a,21
    ld (sample_rows_left),a
.row:
    ld e,(ix+0)
    ld d,(ix+1)
    ld c,(ix+2)
    exx
    ld l,(ix+3)
    ld h,(ix+4)
    ld c,(ix+5)
    exx
    ld hl,g80x_sample_x
    ld b,120
.pixel:
    push hl
    ld l,(hl)
    ld h,0
    add hl,de
    ld a,(hl)
    and c
    pop hl
    jr z,.empty
    exx
    ld a,(hl)
    or c
    ld (hl),a
    exx
.empty:
    inc hl
    exx
    inc hl
    exx
    djnz .pixel
    ld bc,6
    add ix,bc
    ld hl,sample_rows_left
    dec (hl)
    jr nz,.row
    ret

; Native 5x7 text. DE = native row / pixel x, x advances five useful pixels.
g80x_puts:
    push bc
    push de
    push hl
    ld a,d
    ld (native_page),a
    ld a,e
    ld (native_x),a
.next:
    ld a,(hl)
    inc hl
    or a
    jr z,.done
    call g80x_char
    jr .next
.done:
    pop hl
    pop de
    pop bc
    ret
g80x_char:
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
    ld a,(native_page)
    cp 4
    jr nc,.overflow
    add a,a
    ld l,a
    ld h,0
    ld de,g80x_lcd_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld a,(native_x)
    cp 116
    jr nc,.overflow
    ld l,a
    ld h,0
    add hl,de
    pop de
    ld b,5
.column:
    ld a,(de)
    and 127
    ld (hl),a
    inc hl
    inc de
    djnz .column
    ld a,(native_x)
    add a,5
    ld (native_x),a
    jr .done
.overflow:
    pop hl
.done:
    pop hl
    pop de
    pop bc
    ret

g80x_title:
    ld hl,title_text
    ld de,$0019
    call g80x_puts
    ld a,(menu_choice)
    ld hl,cup_option
    or a
    jr z,.choice
    ld hl,single_option
    dec a
    jr z,.choice
    ld hl,demo_option
.choice:
    ld de,$010A
    call g80x_puts
    ld a,0
    ld (native_x),a
    ld a,'>'
    call g80x_char
    ld a,(menu_choice)
    or a
    ld hl,cup_info_text
    jr z,.detail
    ld a,(menu_track)
    call track_name
.detail:
    ld de,$0200
    call g80x_puts
    ld hl,menu_help_text
    ld de,$0300
    call g80x_puts
    jp g80x_upload
g80x_help:
    ld hl,g80x_help1
    ld de,$0000
    call g80x_puts
    ld hl,g80x_help2
    ld de,$0100
    call g80x_puts
    ld hl,g80x_help3
    ld de,$0200
    call g80x_puts
    ld hl,g80x_help4
    ld de,$0300
    call g80x_puts
    jp g80x_upload
g80x_result:
    ld hl,finish_text
    ld a,(phase)
    cp 3
    jr z,.header
    ld hl,dead_text
    cp 4
    jr z,.header
    ld hl,cup_end_text
.header:
    ld de,$0000
    call g80x_puts
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
    inc a
    ld d,a
    ld e,0
    call g80x_puts
    ld hl,rank_label
    ld e,50
    call g80x_puts
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
    call g80x_char
    ld a,75
    ld (native_x),a
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
    ld l,(hl)
    ld h,0
    ld c,10
    call divide_hl_c
    push af
    ld a,l
    add a,'0'
    call g80x_char
    pop af
    add a,'0'
    call g80x_char
    ld a,'P'
    call g80x_char
    ld a,'T'
    call g80x_char
    ld hl,result_row
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.pilot
    jp g80x_upload

g80x_hud:
    ld a,1
    ld (native_x),a
    ld a,(demo_mode)
    or a
    ld a,'V'
    jr z,.speed
    ld a,'D'
.speed:
    call g80x_tiny
    ld a,(speed)
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,de
    call g80x_decimal3
    ld a,23
    ld (native_x),a
    ld a,(lap_label)
    call g80x_tiny
    ld a,(lap)
    cp 4
    jr c,.lap
    ld a,3
.lap:
    add a,'0'
    call g80x_tiny
    ld a,'/'
    call g80x_tiny
    ld a,'3'
    call g80x_tiny
    ld a,45
    ld (native_x),a
    ld a,'P'
    call g80x_tiny
    ld a,(rank)
    add a,'0'
    call g80x_tiny
    ld a,'/'
    call g80x_tiny
    ld a,'3'
    call g80x_tiny
    ld a,67
    ld (native_x),a
    ld a,(lap)
    cp 2
    ld a,'-'
    jr c,.boost
    ld a,'B'
.boost:
    call g80x_tiny
    ld a,(energy)
    srl a
    srl a
    ld c,a
    ld hl,lcd_frame+83
    ld (hl),$3E
    inc hl
    ld b,25
.bar:
    ld a,c
    or a
    ld a,$22
    jr z,.empty
    dec c
    ld a,$3E
.empty:
    ld (hl),a
    inc hl
    djnz .bar
    ld (hl),$3E
    ret
g80x_tiny:
    push bc
    push de
    push hl
    sub 32
    ld l,a
    ld h,0
    ld e,l
    ld d,h
    add hl,hl
    add hl,de
    ld de,tiny_font
    add hl,de
    ex de,hl
    ld a,(native_x)
    ld l,a
    ld h,0
    ld bc,lcd_frame
    add hl,bc
    ld b,3
.column:
    ld a,(de)
    add a,a
    ld (hl),a
    inc hl
    inc de
    djnz .column
    ld a,(native_x)
    add a,4
    ld (native_x),a
    pop hl
    pop de
    pop bc
    ret
g80x_decimal3:
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
    call g80x_tiny
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
    call g80x_tiny
    ld a,l
    add a,'0'
    jp g80x_tiny

g80x_minimap:
    ld a,(track_index)
    add a,a
    ld l,a
    ld h,0
    ld de,g80x_map_table
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ld de,lcd_frame+240
    call g80x_map_band
    ld de,lcd_frame+360
    call g80x_map_band
    ld ix,rival1_progress
    call g80x_map_rival
    ld ix,rival2_progress
    call g80x_map_rival
    ld a,(player_x+1)
    ld d,a
    ld a,(player_y+1)
    ld e,a
    call g80x_map_position
    ld a,(frame_counter)
    and 4
    ld a,2
    jr z,.player
    ld a,1
.player:
    jp g80x_dot
g80x_map_band:
    ld b,16
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
g80x_map_rival:
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+3)
    or a
    ret z
    ld d,(ix+7)
    ld e,(ix+9)
    call g80x_map_position
    ld a,2
    jp g80x_dot
g80x_map_position:
    srl d
    srl d
    srl d
    srl e
    srl e
    srl e
    srl e
    ld a,e
    add a,20
    ld e,a
    ret

; Keep the full 23x11 editable ship readable on the cell LCD.
g80x_player:
    call view_phase
    cp 7
    ret z
    ld a,(spin_frames)
    or a
    jr nz,.visible
    ld a,(hurt_frames)
    and 1
    ret nz
.visible:
    call select_player_sprite
    push af
    push hl
    call arrival_offset
    srl a
    add a,17
    ld e,a
    ld d,48
    pop hl
    pop af
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
    call nz,g80x_dot
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
; A=1 white / 2 black, DE=x/y. Native seven-bit pixel address.
g80x_dot:
    ld (native_bits),a
    push bc
    push de
    push hl
    ld a,d
    cp 120
    jr nc,.done
    ld a,e
    cp 28
    jr nc,.done
    ld b,0
.row:
    cp 7
    jr c,.bit
    sub 7
    inc b
    jr .row
.bit:
    ld e,a
    ld a,1
    inc e
.shift:
    dec e
    jr z,.address
    add a,a
    jr .shift
.address:
    ld c,a
    ld a,b
    add a,a
    ld l,a
    ld h,0
    ld e,d
    ld d,0
    push de
    ld de,g80x_lcd_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    pop hl
    add hl,de
    ld a,(native_bits)
    cp 2
    ld a,c
    jr z,.black
    cpl
    and (hl)
    jr .write
.black:
    or (hl)
.write:
    ld (hl),a
.done:
    pop hl
    pop de
    pop bc
    ret
g80x_lcd_rows: dw lcd_frame,lcd_frame+120,lcd_frame+240,lcd_frame+360
    IF BUILD_LANG_EN
g80x_help1: db "ARROWS:DRIVE SPACE:BOOST",0
g80x_help2: db "X:SPIN P:PAUSE F:PHOTO",0
g80x_help3: db "D:AUTO R:RESTART Q:QUIT",0
g80x_help4: db "BOOST:LAP 2 ENTER:RETURN",0
    ELSE
g80x_help1: db "FLECHES ESPACE:TURBO",0
g80x_help2: db "X:VRILLE P:PAUSE F:PHOTO",0
g80x_help3: db "D:AUTO R:REJOUER Q:FIN",0
g80x_help4: db "TURBO:TOUR 2 ENTER:RETOUR",0
    ENDIF
