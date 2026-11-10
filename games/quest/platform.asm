; Sharp IOCS platform layer. All state is inside the emitted image.
; Legacy Quest UI coordinates: cursor_xy high byte=X, low byte=Y, 1-based.

    IF TARGET_G850
; Normal menus use the four centre rows. Battles reserve 16 pixels for actors.
quest_clear:
    call pcg_clear
    push af
    xor a
    ld (battle_scene),a
    pop af
    ret
quest_row:                      ; A=legacy zero-based row -> physical G850 row
    push bc
    ld b,a
    ld a,(battle_scene)
    or a
    ld a,b
    jr z,.normal
    or a
    jr z,.done
    inc a
.normal:
    inc a
.done:
    pop bc
    ret
    ELSE
quest_clear EQU pcg_clear
    ENDIF

quest_putc:
    push af
    push bc
    push de
    push hl
    ld c,a
    ld hl,(cursor_xy)
    cp 13
    jr z,.newline
    cp 10
    jr z,.done
    ld a,h
    dec a
    cp 24
    jr nc,.done
    ld e,a
    ld a,l
    dec a
    cp 4
    jr nc,.done
    IF TARGET_G850
    call quest_row
    ENDIF
    ld d,a
    ld a,c
    call pcg_putc
    inc h
    jr .save
.newline:
    ld h,1
    ld a,l
    cp 4
    jr nc,.save
    inc l
.save:
    ld (cursor_xy),hl
.done:
    pop hl
    pop de
    pop bc
    pop af
    ret

quest_puts:
    push af
    push hl
.loop:
    ld a,(hl)
    inc hl
    or a
    jr z,.done
    call quest_putc
    jr .loop
.done:
    pop hl
    pop af
    ret

quest_print_u8:                 ; A unsigned / non signe, 0..255
    ld l,a
    ld h,0
quest_print_uint:               ; HL unsigned, 0..65535, no leading zeroes
    push af
    push bc
    push de
    push hl
    push ix
    ld ix,decimal_powers
    ld bc,0x0500               ; B=digits left, C=started
.digit:
    ld e,(ix+0)
    ld d,(ix+1)
    inc ix
    inc ix
    ld a,'0'-1
.subtract:
    inc a
    or a
    sbc hl,de
    jr nc,.subtract
    add hl,de
    cp '0'
    jr nz,.emit
    ld d,a
    ld a,c
    or a
    ld a,d
    jr nz,.emit
    ld d,a
    ld a,b
    cp 1
    ld a,d
    jr nz,.next
.emit:
    ld c,1
    call quest_putc
.next:
    djnz .digit
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

quest_clear_row:                ; D = Sharp row, preserves all main registers
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    IF TARGET_G850
    ld a,d
    call quest_row
    ld d,a
    ENDIF
    ld e,0
    ld a,' '
    ld b,24
    call PCG_IOCS_REPEAT
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

quest_poll_key:                 ; one event per press, A=raw or zero; Z valid
    call pcg_key_scan
    cp PCG_KEY_BREAK
    jp z,quit
    cp PCG_KEY_OFF
    jp z,quit
    push bc
    ld b,a
    ld a,(key_last)
    cp b
    ld a,b
    ld (key_last),a
    jr nz,.new
    xor a
.new:
    pop bc
    or a
    ret

quest_read_key:
    call quest_poll_key
    jr z,quest_read_key
    ret

quest_key_ascii:
    call quest_poll_key
    ret z
    cp 64
    jr nc,.invalid
    push hl
    push de
    ld e,a
    ld d,0
    ld hl,raw_ascii
    add hl,de
    ld a,(hl)
    pop de
    pop hl
    or a
    ret
.invalid:
    xor a
    ret

quest_wait_confirm:
    call quest_read_key
    cp PCG_KEY_RETURN
    ret z
    cp PCG_KEY_SPACE
    jr nz,quest_wait_confirm
    ret

ui_show_modal_message:
ui_show_console_message:
    jp ui_message_common
ui_show_intro_text:
    ld hl,INTRO_TEXT_PTR
ui_message_common:
    call quest_clear
    ld de,0x0101
    ld (cursor_xy),de
    call quest_puts
    jp quest_wait_confirm

rng8:                           ; nonzero 8-bit Galois LFSR
    ld a,(rng_seed)
    or a
    jr nz,.step
    ld a,0xB8
.step:
    srl a
    jr nc,.save
    xor 0xB8
.save:
    ld (rng_seed),a
    ret

battle_return_to_map:
    ld a,4
    ld (encounter_cooldown),a
    call game_autosave
    call world_redraw_map_with_player
    ld a,1
    ret

game_over_restart:
    call quest_clear
    ld hl,msg_game_over
    ld de,0x0602
    ld (cursor_xy),de
    call quest_puts
    call quest_wait_confirm
    call progress_heal_player_full
    call world_set_home_position
    call game_autosave
    call world_redraw_map_with_player
    ld sp,(saved_return_sp)
    jp main

