; Adapted from the user's Canon X-07 Quest; see NOTICE.md.
; ------------------------------------------------------------
; Tile events
; ------------------------------------------------------------

world_get_player_global_coords:
	ld a,(player_x)
	srl a
	srl a
	srl a
	ld c,a

	ld a,(player_y)
	srl a
	srl a
	srl a
	ld b,a

world_get_player_global_coords_y_ok:

	ld a,(chunk_x)
	ld e,a
	add a,a
	add a,a
	add a,a
	add a,a
	sub e
	add a,c
	ld c,a

	ld a,(chunk_y)
	add a,a
	add a,a
	add a,b
	ld b,a
	ret

world_mul15_a_to_hl:
	ld l,a
	ld h,0
	ld e,l
	ld d,h
	add hl,hl
	add hl,hl
	add hl,hl
	add hl,hl
	or a
	sbc hl,de
	ret

world_get_map_packed_row_ptr_a:
	call world_mul15_a_to_hl
	ld de,map_packed
	add hl,de
	ret

world_get_map_tile_bc:
	push de
	ld a,b
	call world_get_map_packed_row_ptr_a
	ld a,c
	srl a
	ld e,a
	ld d,0
	add hl,de
	ld a,(hl)
	bit 0,c
	jr nz,world_get_map_tile_bc_low
	rrca
	rrca
	rrca
	rrca
world_get_map_tile_bc_low:
	and $0F
	pop de
	ret

check_target_tile_event:
	call world_get_target_tile_id
	call check_tile_event_from_a
	ret nz
	ld a,(target_player_x)
	srl a
	srl a
	srl a
	ld c,a

	ld a,(target_player_y)
	srl a
	srl a
	srl a
	ld b,a
	ld a,(target_chunk_x)
	ld e,a
	add a,a
	add a,a
	add a,a
	add a,a
	sub e
	add a,c
	ld c,a

	ld a,(target_chunk_y)
	add a,a
	add a,a
	add a,b
	ld b,a

	ld a,c
	cp 25
	ret nz
	ld a,b
	cp 5
	ret nz
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_OASIS
	ret nz
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_RUINS
	ret z
	ld a,EVENT_FLAG_BOSS_OASIS
	ld (battle_event_flag_mask),a
	ld a,8
	call progress_load_enemy_from_id
	xor a
	ld (battle_outcome),a
	call battle
	jp battle_return_to_map

check_tile_event:
	call world_get_player_tile_id
	jp check_tile_event_from_a

check_tile_event_from_a:
	cp TILE_CASTLE_LEFT
	jr z,world_event_dispatch_castle
	cp TILE_CASTLE_RIGHT
	jr z,world_event_dispatch_castle
	cp 4
	jr z,world_event_dispatch_village
	cp 5
	jr z,world_event_try_ruins
	cp 6
	jr z,world_event_try_cemetery
	cp 7
	jr z,world_event_try_forest
	cp 8
	jr z,world_event_try_tower
	jp world_event_none

world_event_dispatch_castle:
	call castle_menu_enter
	ld a,1
	ret

world_event_dispatch_village:
	call village_menu_enter
	ld a,1
	ret

world_event_dispatch_boss:
	call world_event_boss
	ld a,1
	ret

world_event_try_cemetery:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_CEMETERY
	jr nz,world_event_none
	ld a,EVENT_FLAG_BOSS_CEMETERY
	ld (battle_event_flag_mask),a
	ld a,5
	call progress_load_enemy_from_id
	xor a
	ld (battle_outcome),a
	call battle
	jp battle_return_to_map

world_event_try_forest:
	ld a,EVENT_FLAG_BOSS_FOREST
	ld (world_event_mask),a
	ld a,6
	ld (world_event_param),a
	jr world_event_try_boss

world_event_try_ruins:
	ld a,EVENT_FLAG_BOSS_RUINS
	ld (world_event_mask),a
	ld a,7
	ld (world_event_param),a
	jr world_event_try_boss

world_event_try_tower:
	ld a,EVENT_FLAG_BOSS_TOWER
	ld (world_event_mask),a
	ld a,9
	ld (world_event_param),a

world_event_try_boss:
	ld a,(world_event_mask)
	ld b,a
	ld a,(event_flags)
	and b
	jr nz,world_event_none
	call world_boss_is_unlocked
	jr z,world_event_none
	jr world_event_dispatch_boss

world_boss_is_unlocked:
	ld a,(world_event_mask)
	cp EVENT_FLAG_BOSS_CEMETERY
	jr z,world_boss_is_unlocked_yes
	cp EVENT_FLAG_BOSS_FOREST
	jr z,world_boss_need_cemetery
	cp EVENT_FLAG_BOSS_RUINS
	jr z,world_boss_need_forest
	cp EVENT_FLAG_BOSS_OASIS
	jr z,world_boss_need_ruins
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_OASIS
	ret

world_boss_need_cemetery:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_CEMETERY
	ret

world_boss_need_forest:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_FOREST
	ret

world_boss_need_ruins:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_RUINS
	ret

world_boss_is_unlocked_yes:
	ld a,1
	ret

world_event_none:
	xor a
	ret

world_event_boss:
	ld a,(world_event_mask)
	ld (battle_event_flag_mask),a
	ld a,(world_event_param)
	call progress_load_enemy_from_id
	ld a,BATTLE_OUTCOME_NONE
	ld (battle_outcome),a
	call battle
	jp battle_return_to_map

world_get_player_tile_id:
    call world_get_player_global_coords
	jp world_get_map_tile_bc

village_menu_enter:
	call world_draw_village_screen
	call menu_set_cancel_world_menu
	ld hl,menu_village
	jp menu_vertical

village_shop_menu_enter:
	call world_draw_shop_screen
	ld a,1
	ld (world_event_param),a
	ld hl,village_menu_enter
	ld (menu_cancel_ptr),hl
	ld hl,menu_village_shop
	jp menu_vertical

castle_menu_enter:
	call world_draw_castle_screen
	call menu_set_cancel_world_menu
	ld hl,menu_castle
	jp menu_vertical

castle_shop_menu_enter:
	call world_draw_shop_screen
	xor a
	ld (world_event_param),a
	call menu_set_cancel_castle_menu
	ld hl,menu_castle_shop
	jp menu_vertical

world_menu_leave_to_map:
	jp world_redraw_map_with_player

world_show_status_menu:
    call quest_clear
    call world_draw_status_screen
    call quest_wait_confirm
    jp world_redraw_map_with_player

world_draw_village_screen:
	ld hl,msg_village
	ld d,1
	ld e,1
	jr world_draw_titled_screen

world_draw_castle_screen:
	ld hl,msg_castle
	ld d,16
	ld e,1
	jr world_draw_titled_screen

world_draw_shop_screen:
	call world_clear_menu_screen
	ld hl,msg_gold
	ld de,0x0F01
	ld (cursor_xy),de
	call quest_puts
	ld hl,(player_gold)
	jp quest_print_uint

world_draw_titled_screen:
	call world_clear_menu_screen
	ld (cursor_xy),de
	call quest_puts
	jr world_draw_gold_bottom_right

world_draw_gold_bottom_right:
	ld hl,msg_gold
	ld de,0x0F03
	ld (cursor_xy),de
	call quest_puts
	ld hl,(player_gold)
	ld de,0x0F04
	jp world_print_value_hl

world_clear_menu_screen:
	jp pcg_clear

world_draw_status_screen:
	ld hl,msg_status_title
	ld de,0x0101
	ld a,(player_level)
	call world_print_label_value_a
	ld hl,msg_gold
	ld de,0x0E01
	ld (cursor_xy),de
	call quest_puts
	ld hl,(player_gold)
	call quest_print_uint

	ld hl,msg_status_hp
	ld de,0x0102
	ld a,(player_hp_cur)
	call world_print_label_value_a
	ld a,'/'
	call quest_putc
	ld a,(player_hp_max)
	call quest_print_u8

	ld hl,msg_status_pot
	ld de,0x0103
	ld a,(inventory_potions)
	call world_print_label_value_a
	ld hl,msg_status_smoke
	ld de,0x0E03
	ld a,(inventory_smokes)
	call world_print_label_value_a

	ld hl,msg_status_sword
	ld de,0x0104
	ld a,(player_atk_bonus)
	call world_print_label_value_a
	ld hl,msg_status_shield
	ld de,0x0E04
	ld a,(player_def_bonus)
	jp world_print_label_value_a

world_print_label_value_a:
	ld (cursor_xy),de
	call quest_puts
	jp quest_print_u8

world_print_value_hl:
	ld (cursor_xy),de
	jp quest_print_uint

castle_get_story_stage:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_TOWER|EVENT_FLAG_BOSS_OASIS|EVENT_FLAG_BOSS_RUINS|EVENT_FLAG_BOSS_FOREST|EVENT_FLAG_BOSS_CEMETERY
	ret z
	ld b,0
castle_get_story_stage_loop:
	inc b
	srl a
	jr nz,castle_get_story_stage_loop
	ld a,b
	ret

castle_select_story_ptr:
	add a,a
	ld e,a
	ld d,0
	add hl,de
	ld e,(hl)
	inc hl
	ld d,(hl)
	ex de,hl
	ret

castle_palace:
	call castle_get_story_stage
	or a
	jr nz,castle_palace_followup
	call ui_show_intro_text
	jp castle_menu_enter
castle_palace_followup:
	dec a
	ld hl,castle_king_msg_table
	call castle_select_story_ptr
	call ui_show_console_message
	jp castle_menu_enter

village_talk:
	ld a,(event_flags)
	and EVENT_FLAG_BOSS_OASIS
	ld hl,msg_village_0
	jr z,village_talk_show
	ld hl,msg_village_1

village_talk_show:
	call ui_show_console_message
	jp village_menu_enter

castle_inn_menu_enter:
	xor a
	ld (world_event_param),a
	jr inn_menu_enter

village_rest:
	ld a,1
	ld (world_event_param),a

inn_menu_enter:
	call world_draw_inn_screen
	ld a,(world_event_param)
	or a
	ld hl,castle_menu_enter
	jr z,inn_menu_enter_set_cancel
	ld hl,village_menu_enter
inn_menu_enter_set_cancel:
	ld (menu_cancel_ptr),hl
	ld hl,menu_castle_inn
	jp menu_vertical

castle_inn_yes:
	ld a,(player_hp_cur)
	ld b,a
	ld a,(player_hp_max)
	cp b
	jr nz,castle_inn_yes_pay
	ld hl,msg_full_hp
	call ui_show_modal_message
	jr inn_reenter

castle_inn_yes_pay:
	call world_get_inn_cost_hl
	call world_try_spend_gold_hl
	jr c,castle_inn_apply
	ld hl,msg_no_gold
	call ui_show_modal_message
	jr inn_reenter

castle_inn_apply:
	call progress_heal_player_full
	call game_autosave
inn_reenter:
	call inn_return_menu
	jp (hl)

inn_return_menu:
	ld a,(world_event_param)
	or a
	ld hl,castle_menu_enter
	ret z
	ld hl,village_menu_enter
	ret

shop_buy_potion:
	call shop_get_potion_cost_hl
	ld bc,inventory_potions
	jr shop_buy_stock

shop_buy_smoke:
	call shop_get_smoke_cost_hl
	ld bc,inventory_smokes

shop_buy_stock:
	call world_try_spend_gold_hl
	jp nc,shop_show_no_gold
	ld a,(bc)
	inc a
	ld (bc),a
	jp shop_saved

shop_buy_blade:
	ld hl,player_atk_bonus
	jr shop_buy_upgrade

shop_buy_armor:
	ld hl,player_def_bonus

shop_buy_upgrade:
	push hl
	call shop_get_upgrade_target
	ld b,a
	pop hl
	ld a,(hl)
	cp b
	jp nc,shop_show_upgrade_owned
	push hl
	call shop_get_upgrade_cost_hl
	push bc
	call world_try_spend_gold_hl
	pop bc
	pop hl
	jp nc,shop_show_no_gold
	ld (hl),b
	jp shop_upgrade_saved

shop_return_menu:
	ld a,(world_event_param)
	or a
	ld hl,castle_shop_menu_enter
	ret z
	ld hl,village_shop_menu_enter
	ret

shop_reenter:
	call shop_return_menu
	jp (hl)

shop_show_no_gold:
	ld hl,msg_no_gold
	call ui_show_modal_message
	jp shop_reenter

shop_show_upgrade_owned:
	ld hl,msg_upgrade_owned
	call ui_show_modal_message
	jp shop_reenter

shop_saved:
	call game_autosave
	jp shop_reenter

shop_upgrade_saved:
	call progress_sync_player_stats_from_level
	jp shop_saved

world_try_spend_gold_hl:
	ex de,hl
	ld hl,(player_gold)
	or a
	sbc hl,de
	jr c,world_try_spend_gold_fail
	ld (player_gold),hl
	scf
	ret

world_try_spend_gold_fail:
	or a
	ret

shop_get_potion_cost_hl:
	ld hl,shop_potion_cost_table
	jr shop_get_cost_hl

shop_get_smoke_cost_hl:
	ld hl,shop_smoke_cost_table
	jr shop_get_cost_hl

shop_get_upgrade_cost_hl:
	ld hl,shop_upgrade_cost_table

shop_get_cost_hl:
	ld a,(world_event_param)
	ld e,a
	ld d,0
	add hl,de
	ld a,(hl)
	ld l,a
	ld h,0
	ret

shop_get_upgrade_target:
	ld a,(world_event_param)
	ld e,a
	ld d,0
	ld hl,shop_upgrade_target_table
	add hl,de
	ld a,(hl)
	ret

shop_potion_cost_table:
	.db 14,22

shop_smoke_cost_table:
	.db 22,32

shop_upgrade_cost_table:
	.db 48,144

shop_upgrade_target_table:
	.db 1,2

world_get_inn_cost_hl:
	ld a,(player_level)
	srl a
	srl a
	srl a
	srl a
	add a,8
	ld l,a
	ld h,0
	ret

world_patch_inn_offer_price:
	call world_get_inn_cost_hl
	ld a,l
	ld hl,msg_inn_offer_price
	jp battle_store_two_digits_a

world_draw_inn_screen:
	call world_clear_menu_screen
	call world_draw_gold_bottom_right
	ld hl,msg_inn
	ld d,13
	ld e,1
	ld (cursor_xy),de
	call quest_puts
	call world_patch_inn_offer_price
	ld hl,msg_inn_offer
	ld d,5
	ld e,2
	ld (cursor_xy),de
	jp quest_puts
