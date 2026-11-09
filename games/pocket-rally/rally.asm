; POCKET RALLY - original top-down Z80 racer / course vue de dessus.
; (c) 2026 P.RAIMBAULT. MIT. No Tiny CarZ code, tracks or graphics.
    INCLUDE "sharp-pc-g8xx.inc"
    ORG 0x100
CAR_SIZE EQU 11
entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (track_index),a
    ld (last_key),a
    call title_screen
main_loop:
    call pcg_key_scan
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
    call world_step
    ld a,(phase)
    cp 1
    call z,draw_game
    ld bc,800
frame_delay:
    dec bc
    ld a,b
    or c
    jr nz,frame_delay
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
    jr nz,key_normal
    ld a,(help_previous)
    ld (phase),a
    cp 1
    jp z,draw_game
    jp title_screen
exit_key:
    pop hl
    jp quit
key_normal:
    ld a,b
    cp PCG_KEY_R
    jp z,new_game
    cp PCG_KEY_M
    jr z,show_help
    ld a,(phase)
    cp 1
    ld a,b
    jr z,key_play
    cp PCG_KEY_RETURN
    jp z,new_game
    cp PCG_KEY_N
    ret nz
    ld a,(track_index)
    xor 1
    ld (track_index),a
    jp title_screen
key_play:
    cp PCG_KEY_P
    jr z,toggle_pause
    cp PCG_KEY_F
    ret nz
    ld a,(auto_throttle)
    xor 1
    ld (auto_throttle),a
    ret
toggle_pause:
    ld a,(paused)
    xor 1
    ld (paused),a
    jp z,draw_game
    ld hl,pause_text
    jp message
show_help:
    ld a,(paused)
    or a
    ret nz
    ld a,(phase)
    ld (help_previous),a
    ld a,4
    ld (phase),a
    jp help_screen
new_game:
    ld a,(track_index)
    ld e,a
    ld d,0
    ld hl,gate_counts
    add hl,de
    ld a,(hl)
    ld (gate_count),a
    sla e
    ld hl,track_maps
    call indexed_word
    ld (active_map),hl
    ld hl,track_gates
    call indexed_word
    ld (active_gates),hl
    ld hl,track_starts
    call indexed_word
    ld de,cars
    ld bc,3*CAR_SIZE
    ldir
    xor a
    ld (paused),a
    ld (auto_throttle),a
    ld (frame_count),a
    ld (hit_flash),a
    ld (camera_x),a
    ld (camera_y),a
    ld hl,0
    ld (race_ticks),hl
    ld a,1
    ld (phase),a
    ld a,3
    ld (race_rank),a
    call update_camera
    jp draw_game
indexed_word:
    add hl,de
    ld a,(hl)
    inc hl
    ld h,(hl)
    ld l,a
    ret
world_step:
    ld hl,frame_count
    inc (hl)
    ld hl,(race_ticks)
    ld de,9999
    or a
    sbc hl,de
    add hl,de
    jr nc,tick_full
    inc hl
    ld (race_ticks),hl
tick_full:
    ld a,(hit_flash)
    or a
    jr z,world_input
    dec a
    ld (hit_flash),a
world_input:
    call sample_controls
    ld ix,cars
    call player_controls
    call car_drive
    call pass_gate
    ld ix,cars+CAR_SIZE
    ld b,2
world_ai:
    push bc
    ld a,(ix+8)
    or a
    jr nz,world_ai_next
    call ai_controls
    call car_drive
    call pass_gate
world_ai_next:
    ld de,CAR_SIZE
    add ix,de
    pop bc
    djnz world_ai
    call car_contact
    call update_rank
    ld a,(cars+8)
    or a
    ret z
    ld a,3
    ld (phase),a
    jp result_screen
fixed_to_int:
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ret
signed_word:
    ld e,a
    rla
    sbc a,a
    ld d,a
    ret
    INCLUDE "input.asm"
    INCLUDE "driving.asm"
    INCLUDE "race.asm"
    INCLUDE "render.asm"
    INCLUDE "blitter.asm"
    INCLUDE "interface.asm"
    INCLUDE "../../lib/pcg801_runtime.asm"
    INCLUDE "generated.inc"
data_start:
phase: db 0
paused: db 0
last_key: db 0
help_previous: db 0
track_index: db 0
gate_count: db 0
active_map: dw 0
active_gates: dw 0
buttons: db 0
auto_throttle: db 0
frame_count: db 0
hit_flash: db 0
race_ticks: dw 0
race_rank: db 0
camera_x: db 0
camera_y: db 0
camera_target: db 0
car_x: db 0
car_y: db 0
candidate_x: dw 0
candidate_y: dw 0
drive_dx: db 0
drive_dy: db 0
gate_dx: db 0
gate_dy: db 0
gate_signs: db 0
desired_angle: db 0
desired_speed: db 0
player_progress: db 0
player_distance: db 0
render_band: db 0
render_tile_x: db 0
render_tile_y: db 0
render_sub_x: db 0
render_shift_y: db 0
render_end: db 0
render_group_phase: db 0
render_base0: dw 0
render_base1: dw 0
render_base2: dw 0
render_out: dw 0
draw_x: dw 0
draw_y: dw 0
sprite_source: dw 0
sprite_width: db 0
sprite_column: db 0
sprite_band: db 0
sprite_shift: db 0
sprite_clip: db 0
cars: ds 3*CAR_SIZE,0
row_cache0: ds 48,0
row_cache1: ds 48,0
row_cache2: ds 48,0
frame_buffer: ds 480,0
program_end:
    ASSERT program_end <= 0x17e3
