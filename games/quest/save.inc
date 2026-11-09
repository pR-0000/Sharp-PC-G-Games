; Adapted Quest save/new-game logic; see NOTICE.md.
world_set_home_position:
	ld a,HOME_CHUNK_X
	ld (chunk_x),a
	ld a,HOME_CHUNK_Y
	ld (chunk_y),a
	ld a,HOME_PLAYER_X
	ld (player_x),a
	ld a,HOME_PLAYER_Y
	ld (player_y),a
	ret

game_has_save:
	ld a,(save_magic)
	cp SAVE_MAGIC_VALUE
	ret

game_autosave:
	ld a,SAVE_MAGIC_VALUE
	ld (save_magic),a
    ld hl,player_save_record
    ld de,save_chunk_x
    ld bc,PLAYER_SAVE_BYTES
    ldir
	ret

game_load_save:
    ld hl,save_chunk_x
    ld de,player_save_record
    ld bc,PLAYER_SAVE_BYTES
    ldir
	call progress_sync_player_stats_from_level
    call reset_transient
	xor a
	ld (encounter_cooldown),a
	ret

reset_transient:
    xor a
    ld hl,transient_start
    ld (hl),a
    ld de,transient_start+1
    ld bc,transient_end-transient_start-1
    ldir
    ret

game_begin_from_title:
	call game_has_save
	jr nz,game_begin_new
	jp game_load_save

game_begin_new:
	call init_player_state
	call world_set_home_position
	call game_autosave
	IF DEBUG_SKIP_INTRO
	jp game_autosave
	ENDIF
	call ui_show_intro_text
	jp game_autosave

