; Original Quest table format, native G801 raw key events, no Canon IO.
menu:
    xor a
    jr menu_enter
menu_vertical:
    ld a,1
menu_enter:
    ld (menu_vertical_mode),a
    xor a
    ld (previous_option),a
    ld (current_option),a
    ld a,(hl)
    ld (max_cursor_options),a
    inc hl
    ld (menu_jump_ptr),hl
    ld c,a
    ld b,0
    add hl,bc
    add hl,bc
    ld (menu_entry_ptr),hl
    ld b,a
.draw:
    ld d,(hl)
    inc hl
    ld e,(hl)
    inc hl
    ld (cursor_xy),de
    call quest_puts
.skip:
    ld a,(hl)
    inc hl
    or a
    jr nz,.skip
    djnz .draw
    call menu_draw_cursor
menu_loop:
    call quest_read_key
    cp PCG_KEY_BACKSPACE
    jr z,.cancel
    cp PCG_KEY_CLS
    jr z,.cancel
    cp PCG_KEY_RETURN
    jr z,.confirm
    cp PCG_KEY_SPACE
    jr z,.confirm
    ld b,a
    ld a,(menu_vertical_mode)
    or a
    ld a,b
    jr z,.horizontal
    cp PCG_KEY_UP
    jr z,.previous
    cp PCG_KEY_DOWN
    jr z,.next
    jr menu_loop
.horizontal:
    cp PCG_KEY_LEFT
    jr z,.previous
    cp PCG_KEY_RIGHT
    jr z,.next
    jr menu_loop
.previous:
    ld a,(current_option)
    or a
    jr z,menu_loop
    dec a
    jr .select
.next:
    ld a,(max_cursor_options)
    dec a
    ld b,a
    ld a,(current_option)
    cp b
    jr z,menu_loop
    inc a
.select:
    ld (current_option),a
    call menu_draw_cursor
    jr menu_loop
.cancel:
    ld hl,(menu_cancel_ptr)
    ld a,h
    or l
    jr z,menu_loop
    jp (hl)
.confirm:
    ld a,(current_option)
    add a,a
    ld e,a
    ld d,0
    ld hl,(menu_jump_ptr)
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    jp (hl)

menu_set_cancel_none:
    ld hl,0
    ld (menu_cancel_ptr),hl
    ret
menu_set_cancel_world_menu:
    ld hl,world_menu_leave_to_map
    jr menu_set_cancel
menu_set_cancel_castle_menu:
    ld hl,castle_menu_enter
    jr menu_set_cancel
menu_set_cancel_battle_menu:
    ld hl,battle_show_menu
menu_set_cancel:
    ld (menu_cancel_ptr),hl
    ret

menu_draw_cursor:
    ld a,(previous_option)
    ld c,' '
    call menu_cursor_at
    ld a,(current_option)
    ld (previous_option),a
    ld c,'>'
menu_cursor_at:
    ld hl,(menu_entry_ptr)
    or a
    jr z,.found
    ld b,a
.skip:
    inc hl
    inc hl
.string:
    ld a,(hl)
    inc hl
    or a
    jr nz,.string
    djnz .skip
.found:
    ld d,(hl)
    dec d
    inc hl
    ld e,(hl)
    ld (cursor_xy),de
    ld a,c
    jp quest_putc
