; FR/EN: native 18x5 view, original 8x8 artwork, shared 30x16 world and rules.
glyph_address:                  ; A=tile -> HL, BC/DE preserved
    push de
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    ld de,glyph_tiles
    add hl,de
    pop de
    ret

world_redraw_map_with_player:
    xor a
    ld (battle_scene),a
    call world_get_player_global_coords
    ld a,c
    sub 9
    jr nc,.x_positive
    xor a
.x_positive:
    cp 13
    jr c,.x_ready
    ld a,12
.x_ready:
    ld (camera_x),a
    ld a,b
    sub 2
    jr nc,.y_positive
    xor a
.y_positive:
    cp 12
    jr c,.y_ready
    ld a,11
.y_ready:
    ld (camera_y),a
    xor a
    ld (draw_row),a
    ld de,frame_buffer+144
.row:
    xor a
    ld (draw_col),a
.cell:
    ld a,(camera_y)
    ld b,a
    ld a,(draw_row)
    add a,b
    ld b,a
    ld a,(camera_x)
    ld c,a
    ld a,(draw_col)
    add a,c
    ld c,a
    call world_get_map_tile_bc
    call glyph_address
    ld bc,8
    ldir
    ld a,(draw_col)
    inc a
    ld (draw_col),a
    cp 18
    jr c,.cell
    ld a,(draw_row)
    inc a
    ld (draw_row),a
    cp 5
    jr c,.row
    call draw_player
    ld hl,frame_buffer+144
    ld de,0x0100
.upload:
    ld b,144
    call pcg_pattern
    ld bc,144
    add hl,bc
    inc d
    ld a,d
    cp 6
    jr c,.upload
    ; One native-font status row, never over the world.
    ld de,0
    ld a,' '
    ld b,24
    call quest_repeat_physical
    ld a,HUD_HP
    call pcg_putc
    inc e
    ld a,(player_hp_cur)
    call quest_hud_u8
    ld a,'/'
    call pcg_putc
    inc e
    ld a,(player_hp_max)
    call quest_hud_u8
    ld e,9
    ld a,HUD_LEVEL
    call pcg_putc
    inc e
    ld a,(player_level)
    call quest_hud_u8
    ld e,14
    ld a,HUD_GOLD
    call pcg_putc
    inc e
    ld hl,(player_gold)
    call quest_hud_uint
    ld e,22
    ld a,'M'
    jp pcg_putc

draw_player:
    call world_get_player_global_coords
    ld a,(camera_y)
    ld e,a
    ld a,b
    sub e
    inc a
    ld hl,frame_buffer
    ld de,144
.page:
    add hl,de
    dec a
    jr nz,.page
    ld a,(camera_x)
    ld e,a
    ld a,c
    sub e
    add a,a
    add a,a
    add a,a
    ld e,a
    ld d,0
    add hl,de
    ex de,hl
    ld hl,glyph_hero
    ld bc,8
    ldir
    ret

quest_hud_u8:
    ld l,a
    ld h,0
quest_hud_uint:
    ld ix,decimal_powers
    ld bc,0x0500
.digit:
    push bc
    ld c,(ix+0)
    ld b,(ix+1)
    ld a,'0'-1
.subtract:
    inc a
    or a
    sbc hl,bc
    jr nc,.subtract
    add hl,bc
    pop bc
    cp '0'
    jr nz,.emit
    push af
    ld a,c
    or a
    jr nz,.zero
    ld a,b
    cp 1
    jr z,.zero
    pop af
    jr .next
.zero:
    pop af
.emit:
    ld c,1
    call pcg_putc
    inc e
.next:
    inc ix
    inc ix
    djnz .digit
    ret

quest_repeat_physical:
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    call PCG_IOCS_REPEAT
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret
