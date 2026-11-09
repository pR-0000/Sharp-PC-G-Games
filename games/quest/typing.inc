; Adapted from Canon X-07 Quest; see NOTICE.md.
; ------------------------------------------------------------
; Typing challenge
; ------------------------------------------------------------

typing_challenge:
	call typing_select_word
	call typing_flush_keys
	xor a
	ld (typing_index),a
	ld (typing_result),a
	ld a,TYPING_TICK_RELOAD
	ld (typing_tick_div),a
	call battle_clear_bottom_rows
	call typing_draw_word
	call typing_draw_cursor

typing_challenge_loop:
	ld a,(typing_tick_div)
	dec a
	ld (typing_tick_div),a
	jr nz,typing_challenge_poll_key
	ld a,TYPING_TICK_RELOAD
	ld (typing_tick_div),a
	ld a,(typing_timeout)
	dec a
	ld (typing_timeout),a
	jr z,typing_challenge_timeout

typing_challenge_poll_key:
	call quest_key_ascii
	jr z,typing_challenge_no_key
	call typing_normalize_key
	or a
	jr z,typing_challenge_loop
	; quest_poll_key gere deja les fronts / already requires a new key press.
	ld b,a
	call typing_process_key
	or a
	jr z,typing_challenge_loop
	jr typing_challenge_done

typing_challenge_no_key:
	jr typing_challenge_loop

typing_challenge_timeout:
	jr typing_challenge_timeout_miss

typing_challenge_timeout_miss:
	xor a
	ld (typing_result),a
	jr typing_challenge_done

typing_challenge_done:
	ret

typing_process_key:
	ld a,(typing_index)
	ld e,a
	ld d,0
	ld hl,(typing_word_ptr)
	add hl,de
	ld a,(hl)
	cp b
	jr z,typing_process_key_correct
	jr typing_process_key_miss

typing_process_key_miss:
	xor a
	ld (typing_result),a
	ld a,1
	ret

typing_process_key_correct:
	ld a,(typing_index)
	inc a
	ld (typing_index),a
	ld b,a
	ld a,(typing_word_len)
	cp b
	jr z,typing_process_key_done
	call typing_draw_cursor
	xor a
	ret

typing_process_key_done:
	ld a,(typing_timeout)
	ld b,a
	ld a,(typing_bonus_limit)
	cp b
	jr z,typing_process_key_amp
	jr c,typing_process_key_amp
	ld a,TYPING_RESULT_NORMAL
	ld (typing_result),a
	ld a,1
	ret

typing_process_key_amp:
	ld a,TYPING_RESULT_AMP
	ld (typing_result),a
	ld a,1
	ret

typing_select_word:
	ld a,(player_level)
	cp 6
	jr nc,typing_select_group_1
	xor a
	jr typing_select_group_ready
typing_select_group_1:
	ld a,1
	ld b,a
	ld a,(player_level)
	cp 12
	ld a,b
	jr c,typing_select_group_ready
	ld a,2
	ld b,a
	ld a,(player_level)
	cp 24
	ld a,b
	jr c,typing_select_group_ready
	ld a,3
typing_select_group_ready:
	add a,a
	add a,a
	ld c,a
	call rng8
	ld b,a
	ld a,r
	xor b
	and $03
	add a,c
	add a,a
	ld e,a
	ld d,0
	ld hl,typing_word_ptrs
	add hl,de
	ld e,(hl)
	inc hl
	ld d,(hl)
	ex de,hl
	ld (typing_word_ptr),hl
	push hl
	ld b,0

typing_select_word_len_loop:
	ld a,(hl)
	or a
	jr z,typing_select_word_len_done
	inc b
	inc hl
	jr typing_select_word_len_loop

typing_select_word_len_done:
	ld a,b
	ld (typing_word_len),a
	pop hl

	ld a,(player_level)
	srl a
	srl a
	ld b,a
	ld a,72
	sub b
	jr nc,typing_timeout_nonneg
	xor a
typing_timeout_nonneg:
	cp 34
	jr nc,typing_timeout_store
	ld a,34
typing_timeout_store:
	ld (typing_timeout),a
	sub 30
	jr nc,typing_bonus_nonneg
	xor a
typing_bonus_nonneg:
	cp 12
	jr nc,typing_bonus_store
	ld a,12
typing_bonus_store:
	ld (typing_bonus_limit),a
	ret

typing_flush_keys:
	call quest_key_ascii
	ret z
	jr typing_flush_keys

typing_draw_word:
	ld a,(typing_word_len)
	srl a
	ld b,a
	ld a,13
	sub b
	ld (typing_word_x),a
	ld d,a
	ld e,3
	ld hl,(typing_word_ptr)
	ld (cursor_xy),de
	jp quest_puts

typing_draw_cursor:
    ld d,3
    call quest_clear_row
    ld a,(typing_word_x)
    ld b,a
    ld a,(typing_index)
    add a,b
    ld d,a
    ld e,4
    ld a,'^'
    ld (cursor_xy),de
    jp quest_putc

typing_normalize_key:
typing_normalize_key_uppercase_check:
	cp "A"
	jr c,typing_normalize_key_invalid
	cp "Z"+1
	ret c

typing_normalize_key_invalid:
	xor a
	ret
