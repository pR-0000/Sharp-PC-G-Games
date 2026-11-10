; POCKET RUNNER - original Lode Runner-inspired game for Sharp PC-G.
; FR/EN: plateformes, echelles, cordes, or, pieges / platforms, ladders,
; ropes, gold and traps. (c) 2026 P.RAIMBAULT, MIT.
    INCLUDE "game_platform.inc"
    IF TARGET_G850
    INCLUDE "targets/g850/config.inc"
    ELSE
    INCLUDE "targets/g80x/config.inc"
    ENDIF
    ORG 0x100
PLAYER_PERIOD EQU 3
GUARD_PERIOD  EQU 7
HOLE_TIME     EQU 96
TRAP_TIME     EQU 4
LEVEL_COUNT   EQU 3
entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (paused),a
    ld (last_key),a
    call title_screen
main_loop:
    call pcg_key_scan
    ld (held_key),a
    ld b,a
    ld a,(last_key)
    cp b
    ld a,b
    ld (last_key),a
    call nz,handle_key
    ld a,(phase)
    cp 1
    jr nz,main_loop
    ld a,(paused)
    or a
    jr nz,main_loop
    IF TARGET_G850
    ld a,(photo_frozen)
    or a
    jr nz,main_loop
    ENDIF
    call world_step
    ld a,(phase)
    cp 1
    call z,draw_game
    ld bc,RUN_FRAME_DELAY
main_delay:
    dec bc
    ld a,b
    or c
    jr nz,main_delay
    jr main_loop
quit:
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    ret
handle_key:
    cp PCG_KEY_Q
    jr z,exit_key
    cp PCG_KEY_BREAK
    jr z,exit_key
    cp PCG_KEY_OFF
    jr z,exit_key
    or a
    ret z
    ld b,a
    ld a,(phase)
    cp 4
    jr nz,handle_normal
    ld a,(help_previous)
    ld (phase),a
    cp 1
    jp z,draw_game
    jp title_screen
exit_key:
    ; handle_key was CALLed: discard that return before restoring caller.
    pop hl
    jp quit
handle_normal:
    ld a,b
    cp PCG_KEY_M
    jr z,show_help
    cp PCG_KEY_RETURN
    jr nz,handle_restart
    ld a,(phase)
    cp 1
    ret z
    jp new_game
handle_restart:
    IF TARGET_G850
    cp PCG_KEY_F
    jr nz,photo_key_done
    ld a,(photo_frozen)
    xor 1
    ld (photo_frozen),a
    ret
photo_key_done:
    ENDIF
    ld a,(phase)
    cp 1
    ret nz
    ld a,b
    cp PCG_KEY_P
    jr z,toggle_pause
    ld a,(paused)
    or a
    ret nz
    IF TARGET_G850
    ld a,(photo_frozen)
    or a
    ret nz
    ENDIF
    ld a,b
    cp PCG_KEY_R
    jp z,lose_life
    ld c,0
    cp PCG_KEY_Z
    jp z,dig
    inc c
    cp PCG_KEY_X
    jp z,dig
    ret
show_help:
    ld a,(paused)
    or a
    ret nz
    ld a,(phase)
    ld (help_previous),a
    ld a,4
    ld (phase),a
    jp help_screen
toggle_pause:
    ld a,(paused)
    xor 1
    ld (paused),a
    jp z,draw_game
    ld hl,pause_text
    jp message
new_game:
    xor a
    IF TARGET_G850
    ld (photo_frozen),a
    ENDIF
    ld (level_index),a
    ld (paused),a
    ld hl,0
    ld (score),hl
    ld a,3
    ld (lives),a
    ld a,1
    ld (phase),a
    call load_level
    jp draw_game
load_level:
    ld a,(level_index)
    add a,a
    ld e,a
    ld d,0
    ld hl,level_table
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld a,(hl)
    ld (player_pos),a
    inc hl
    ld a,(hl)
    ld (exit_pos),a
    inc hl
    ld de,guards
    ld b,3
load_guard:
    ld a,(hl)
    inc hl
    ld (de),a
    inc de
    xor a
    ld (de),a
    inc de
    dec hl
    ld a,(hl)
    inc hl
    ld (de),a
    inc de
    djnz load_guard
    ld de,gold_positions
    ld bc,8
    ldir
    ld de,world
load_run:
    ld a,(hl)
    inc hl
    or a
    jr z,load_done
    ld b,a
    ld a,(hl)
    inc hl
load_repeat:
    ld (de),a
    inc de
    djnz load_repeat
    jr load_run
load_done:
    ld a,255
    ld (gold_flags),a
    ld a,8
    ld (gold_left),a
    xor a
    ld (exit_active),a
    ld (player_clock),a
    ld (guard_clock),a
    ld (player_frame),a
    ld hl,holes
    ld b,8
load_clear:
    ld (hl),a
    inc hl
    djnz load_clear
    ret

world_step:
    xor a
    ld (died),a
    call holes_tick
    ld a,(died)
    or a
    ret nz
    ld hl,player_clock
    inc (hl)
    ld a,(hl)
    cp PLAYER_PERIOD
    jr c,world_guards
    ld (hl),0
    call player_step
    call collect_gold
    call check_contact
    ld a,(died)
    or a
    ret nz
    ld a,(exit_active)
    or a
    jr z,world_guards
    ld a,(exit_pos)
    ld b,a
    ld a,(player_pos)
    cp b
    jr nz,world_guards
    ld hl,100
    call add_score
    ld hl,level_index
    inc (hl)
    ld a,(hl)
    cp LEVEL_COUNT
    jp c,load_level
    ld a,3
    ld (phase),a
    ld hl,win_text
    jp result_screen
world_guards:
    ld hl,guard_clock
    inc (hl)
    ld a,(hl)
    cp GUARD_PERIOD
    ret c
    ld (hl),0
    call build_distances
    call guards_step
    jp check_contact
player_step:
    ld a,(player_pos)
    call supported
    ld c,3
    jr nc,player_move
    ld a,(held_key)
    ld c,0
    cp PCG_KEY_LEFT
    jr z,player_move
    inc c
    cp PCG_KEY_RIGHT
    jr z,player_move
    inc c
    cp PCG_KEY_UP
    jr z,player_move
    inc c
    cp PCG_KEY_DOWN
    ret nz
player_move:
    ld a,(player_pos)
    call can_move
    ret nc
    ld (player_pos),a
    ld a,(player_frame)
    xor 1
    ld (player_frame),a
    ret

; A index -> effective terrain A, HL points at mutable terrain, BC intact.
tile:
    ld l,a
    ld h,0
    ld de,world
    add hl,de
    ld a,(hl)
    cp 7
    ret nz
    ld a,(exit_active)
    or a
    ret z
    ld a,3
    ret
; A cell and C dir (left/right/up/down = 0/1/2/3) -> A neighbor, carry.
neighbor:
    ld b,a
    ld a,c
    cp 2
    jr z,neighbor_up
    cp 3
    jr z,neighbor_down
    ld a,b
neighbor_column:
    cp 20
    jr c,neighbor_edge
    sub 20
    jr neighbor_column
neighbor_edge:
    ld d,a
    ld a,c
    or a
    jr nz,neighbor_right
    ld a,d
    or a
    ret z
    ld a,b
    dec a
    scf
    ret
neighbor_right:
    ld a,d
    cp 19
    jr z,move_invalid
    ld a,b
    inc a
    scf
    ret
neighbor_up:
    ld a,b
    cp 20
    jr c,move_invalid
    sub 20
    scf
    ret
neighbor_down:
    ld a,b
    cp 220
    jr nc,move_invalid
    add a,20
    scf
    ret
move_invalid:
    or a
    ret
can_move:
    cp 240
    jr nc,move_invalid
    ld (move_from),a
    call tile
    cp 1
    jr z,move_invalid
    cp 2
    jr z,move_invalid
    ld a,(move_from)
    call neighbor
    ret nc
    ld (move_to),a
    call tile
    cp 1
    jr z,move_invalid
    cp 2
    jr z,move_invalid
    ld a,c
    cp 3
    jr z,move_valid
    cp 2
    jr z,move_up
    ld a,(move_from)
    call supported
    ret nc
    jr move_valid
move_up:
    ld a,(move_from)
    call tile
    cp 3
    jr nz,move_invalid
move_valid:
    ld a,(move_to)
    scf
    ret
supported:
    ld (support_pos),a
    call tile
    cp 3
    jr z,support_yes
    cp 4
    jr z,support_yes
    ld a,(support_pos)
    add a,20
    cp 240
    jr nc,support_yes
    ld (support_below),a
    call tile
    cp 1
    jr z,support_yes
    cp 2
    jr z,support_yes
    cp 3
    jr z,support_yes
    push ix
    ld ix,guards
    ld a,3
support_guard:
    push af
    ld a,(ix+1)
    or a
    jr z,support_next
    ld a,(support_below)
    cp (ix+0)
    jr z,support_head
support_next:
    ld de,3
    add ix,de
    pop af
    dec a
    jr nz,support_guard
    pop ix
    or a
    ret
support_head:
    pop af
    pop ix
support_yes:
    scf
    ret

; Dig left/right diagonal, with an unobstructed adjacent cell.
dig:
    ld a,(player_pos)
    call supported
    ret nc
    ld a,(player_pos)
    call neighbor
    ret nc
    ld (dig_side),a
    call tile
    cp 1
    ret z
    cp 2
    ret z
    ld a,(dig_side)
    cp 220
    ret nc
    add a,20
    cp 240
    ret nc
    ld (dig_target),a
    call tile
    cp 1
    ret nz
    ld hl,holes+1
    ld b,4
dig_slot:
    ld a,(hl)
    or a
    jr z,dig_open
    inc hl
    inc hl
    djnz dig_slot
    ret
dig_open:
    ld (hl),HOLE_TIME
    dec hl
    ld a,(dig_target)
    ld (hl),a
    call tile
    ld (hl),0
    ret
holes_tick:
    ld iy,holes
    ld b,4
hole_next:
    push bc
    ld a,(iy+1)
    or a
    jr z,hole_done
    dec (iy+1)
    jr nz,hole_done
    ld a,(iy+0)
    call tile
    ld (hl),1
    ld a,(player_pos)
    cp (iy+0)
    jr nz,hole_guards
    call lose_life
    pop bc
    ret
hole_guards:
    ld ix,guards
    ld b,3
hole_guard:
    ld a,(ix+0)
    cp (iy+0)
    jr nz,hole_guard_next
    call respawn_guard
    ld hl,25
    call add_score
hole_guard_next:
    ld de,3
    add ix,de
    djnz hole_guard
hole_done:
    ld de,2
    add iy,de
    pop bc
    djnz hole_next
    ret
hole_at:
    ld hl,holes
    ld b,4
hole_find:
    cp (hl)
    jr nz,hole_find_next
    inc hl
    ld a,(hl)
    or a
    jp z,move_invalid
    scf
    ret
hole_find_next:
    inc hl
    inc hl
    djnz hole_find
    or a
    ret

collect_gold:
    ld hl,gold_positions
    ld c,1
    ld b,8
gold_find:
    ld a,(player_pos)
    cp (hl)
    jr nz,gold_next
    ld a,(gold_flags)
    and c
    jr z,gold_next
    ld a,c
    cpl
    ld c,a
    ld a,(gold_flags)
    and c
    ld (gold_flags),a
    ld hl,10
    call add_score
    ld hl,gold_left
    dec (hl)
    ret nz
    ld a,1
    ld (exit_active),a
    ret
gold_next:
    inc hl
    sla c
    djnz gold_find
    ret
add_score:
    push bc
    push de
    ld de,(score)
    add hl,de
    ld de,9999
    or a
    sbc hl,de
    jr c,score_restore
    ld hl,9999
    jr score_store
score_restore:
    add hl,de
score_store:
    ld (score),hl
    pop de
    pop bc
    ret
check_contact:
    ld ix,guards
    ld b,3
contact_next:
    ld a,(ix+1)
    or a
    jr nz,contact_safe
    ld a,(player_pos)
    cp (ix+0)
    jp z,lose_life
contact_safe:
    ld de,3
    add ix,de
    djnz contact_next
    ret
lose_life:
    ld a,1
    ld (died),a
    ld hl,lives
    dec (hl)
    jp nz,load_level
    ld a,2
    ld (phase),a
    ld hl,over_text
    jp result_screen

    INCLUDE "guards.asm"
    INCLUDE "render.asm"
    INCLUDE "interface.asm"
    INCLUDE "game_runtime.asm"
    INCLUDE "generated.inc"
data_start:
phase:          db 0
paused:         db 0
help_previous:  db 0
held_key:       db 0
last_key:       db 0
level_index:    db 0
player_pos:     db 0
player_frame:   db 0
player_clock:   db 0
guard_clock:    db 0
lives:          db 0
score:          dw 0
gold_left:      db 0
gold_flags:     db 0
exit_pos:       db 0
exit_active:    db 0
died:           db 0
move_from:      db 0
move_to:        db 0
support_pos:    db 0
support_below:  db 0
dig_side:       db 0
dig_target:     db 0
bfs_head:       db 0
bfs_tail:       db 0
bfs_to:         db 0
bfs_from:       db 0
bfs_dir:        db 0
guard_best:     db 0
guard_target:   db 0
guard_dir:      db 0
spawn_row:      db 0
spawn_try:      db 0
camera_y:       db 0
draw_cell:      db 0
draw_row:       db 0
draw_column:    db 0
stamp_mode:     db 0
stamp_source:   dw 0
gold_positions: ds 8,0
guards:         ds 9,0
holes:          ds 8,0
world:          ds 240,0
frame_buffer:   ds PCG_FRAME_BYTES,0
    IF TARGET_G850
photo_frozen: db 0
    ENDIF
ai_dist         EQU frame_buffer
ai_queue        EQU frame_buffer+240
program_end:
    IF TARGET_G850
    ASSERT program_end <= 0x7000
    ELSE
    ASSERT program_end <= 0x17e3
    ENDIF
