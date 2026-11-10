; FR/EN: names, 16x16 portraits, HP below them; shared menus on rows 5 and 6.
battle_draw_scene:
    call quest_clear
    ld a,1
    ld (battle_scene),a
    ld hl,msg_hero
    ld de,0x0101
    ld (cursor_xy),de
    call quest_puts
    ld hl,(battle_enemy_name_ptr)
    ld de,0x0F01
    ld (cursor_xy),de
    call quest_puts
    jp battle_refresh_status

battle_prepare_menu_ui:
    call battle_refresh_status
    jr battle_clear_bottom_rows

battle_refresh_status:
    ld d,1
    call quest_clear_row
    ld a,15
    ld e,2
    call battle_portrait
    ld a,(battle_enemy_tile)
    ld e,18
    call battle_portrait
    ld hl,msg_status_hp
    ld de,0x0102
    ld a,(player_hp_cur)
    call world_print_label_value_a
    ld a,'/'
    call quest_putc
    ld a,(player_hp_max)
    call quest_print_u8
    ld hl,msg_status_hp
    ld de,0x0F02
    ld a,(battle_enemy_hp_cur)
    jp world_print_label_value_a

battle_portrait:                ; A=tile, E=physical column (6 pixels)
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld bc,portrait_tiles
    add hl,bc
    ld d,1
    ld b,16
    call pcg_pattern
    ld bc,16
    add hl,bc
    inc d
    ld b,16
    jp pcg_pattern

battle_clear_bottom_rows:
    ld d,2
    call quest_clear_row
    ld d,3
    jp quest_clear_row

battle_show_message:
    push hl
    call battle_clear_bottom_rows
    pop hl
    ld de,0x0103
    ld (cursor_xy),de
    call quest_puts
    jp quest_wait_confirm
