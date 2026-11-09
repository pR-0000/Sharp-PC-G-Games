; Keep Quest's 15x4 tile chunks. Each tile is now a 5x7 Sharp cell.
; Carte / map: columns 0..14; panneau / panel: 15..23 (nine columns).
glyph_address:                  ; A tile 0..22 -> HL, preserve BC/DE
    push de
    ld e,a
    ld d,0
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,de
    ld de,glyph_tiles
    add hl,de
    pop de
    ret

world_redraw_map_with_player:
    xor a
    ld (draw_row),a
.row:
    xor a
    ld (draw_col),a
    ld hl,row_buffer
.cell:
    push hl
    ld a,(chunk_y)
    add a,a
    add a,a
    ld b,a
    ld a,(draw_row)
    add a,b
    ld b,a
    ld a,(chunk_x)
    ld c,a
    add a,a
    add a,a
    add a,a
    add a,a
    sub c
    ld c,a
    ld a,(draw_col)
    add a,c
    ld c,a
    call world_get_map_tile_bc
    call glyph_address
    pop de
    ld bc,5
    ldir
    ex de,hl
    ld a,(draw_col)
    inc a
    ld (draw_col),a
    cp 15
    jr c,.cell
    ld a,(draw_row)
    ld d,a
    ld e,0
    ld hl,row_buffer
    ld b,120                   ; zero-filled tail clears the status area
    call pcg_pattern
    ld a,(draw_row)
    inc a
    ld (draw_row),a
    cp 4
    jr c,.row
    call draw_player
    ld de,0x1001
    ld (cursor_xy),de
    ld hl,msg_hud_hp
    call quest_puts
    ld a,(player_hp_cur)
    call quest_print_u8
    ld a,'/'
    call quest_putc
    ld a,(player_hp_max)
    call quest_print_u8
    ld de,0x1002
    ld (cursor_xy),de
    ld hl,msg_status_title
    call quest_puts
    ld a,(player_level)
    call quest_print_u8
    ld de,0x1003
    ld (cursor_xy),de
    ld hl,msg_gold
    call quest_puts
    ld hl,(player_gold)
    call quest_print_uint
    ld de,0x1004
    ld (cursor_xy),de
    ld hl,status_hint
    jp quest_puts

draw_player:
    ld a,(player_y)
    srl a
    srl a
    srl a
    ld d,a
    ld a,(player_x)
    srl a
    srl a
    srl a
    ld e,a
    ld hl,glyph_hero
    jp pcg_glyph
