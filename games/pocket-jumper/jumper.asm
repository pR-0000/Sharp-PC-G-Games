; POCKET JUMPER - pixel platformer / jeu de plateformes au pixel.
; Original code and graphics. (c) 2026 P.RAIMBAULT, MIT.
    INCLUDE "sharp-pc-g8xx.inc"
    ORG 0x100
WORLD_W     EQU 768
VIEW_W      EQU 100
HERO_W      EQU 12
HERO_H      EQU 12
ENEMY_W     EQU 10
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
    ld (last_buttons),a
    ld (input_buttons),a
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
    call world_step
    ld a,(phase)
    cp 1
    call z,draw_game
    ld bc,1000
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
    cp PCG_KEY_M
    jr z,show_help
    cp PCG_KEY_R
    jp z,new_game
    ld a,(phase)
    cp 1
    ld a,b
    jr z,key_play
    cp PCG_KEY_RETURN
    jp z,new_game
    ret
key_play:
    cp PCG_KEY_P
    jr z,toggle_pause
    ld a,(paused)
    or a
    ret nz
    ret
request_jump:
    ld a,4
    ld (jump_buffer),a
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
    ld hl,level_initial
    ld de,world
    ld bc,576
    ldir
    ld hl,enemies_initial
    ld de,enemies
    ld bc,36
    ldir
    ld hl,PLAYER_START_X
    ld (respawn_x),hl
    ld hl,0
    ld (score),hl
    xor a
    ld (coins),a
    ld (checkpoint),a
    ld (paused),a
    ld (frame_count),a
    ld (last_buttons),a
    ld (input_buttons),a
    ld a,3
    ld (lives),a
    ld a,1
    ld (phase),a
    call reset_player
    jp draw_game
reset_player:
    ld hl,(respawn_x)
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld (player_x),hl
    ld hl,PLAYER_START_Y*16
    ld (player_y),hl
    xor a
    ld (velocity_x),a
    ld (velocity_y),a
    ld (jump_buffer),a
    ld (coyote),a
    ld (facing_left),a
    ld a,1
    ld (grounded),a
    ld a,40
    ld (grace),a
    ld a,20
    ld (camera_y),a
    ret
world_step:
    xor a
    ld (died),a
    ld hl,frame_count
    inc (hl)
    ld a,(grace)
    or a
    jr z,world_input
    dec a
    ld (grace),a
world_input:
    call sample_controls
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    ld (previous_y),a
    call horizontal_input
    ld a,(velocity_y)
    add a,6
    cp 65
    jr c,gravity_store
    bit 7,a
    jr nz,gravity_store
    ld a,64
gravity_store:
    ld (velocity_y),a
    ld a,(grounded)
    or a
    jr z,world_coyote
    ld a,3
    ld (coyote),a
    jr world_jump
world_coyote:
    ld a,(coyote)
    or a
    jr z,world_jump
    dec a
    ld (coyote),a
world_jump:
    ld a,(jump_buffer)
    or a
    jr z,world_move
    dec a
    ld (jump_buffer),a
    ld a,(coyote)
    or a
    jr z,world_move
    ld a,-52
    ld (velocity_y),a
    xor a
    ld (jump_buffer),a
    ld (coyote),a
world_move:
    xor a
    ld (grounded),a
    call move_x
    call move_y
    call check_ground
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    cp 48
    jp nc,lose_life
    call collect_items
    ld a,(phase)
    cp 1
    ret nz
    ld a,(died)
    or a
    ret nz
    call enemies_step
    jp enemy_contact
horizontal_input:
    ld a,(input_buttons)
    and 3
    cp JUMP_LEFT
    jr z,input_left
    cp JUMP_RIGHT
    jr z,input_right
    ld a,(grounded)
    or a
    ret z
    ld a,(velocity_x)
    or a
    ret z
    jp m,input_friction_left
    sub 4
    jr nc,input_store
    xor a
    jr input_store
input_friction_left:
    add a,4
    jr nc,input_store
    xor a
    jr input_store
input_left:
    ld a,1
    ld (facing_left),a
    ld a,(velocity_x)
    sub 8
    cp 224
    jr nc,input_store
    bit 7,a
    jr z,input_store
    ld a,-32
    jr input_store
input_right:
    xor a
    ld (facing_left),a
    ld a,(velocity_x)
    add a,8
    bit 7,a
    jr nz,input_store
    cp 33
    jr c,input_store
    ld a,32
input_store:
    ld (velocity_x),a
    ret
fixed_to_int:
    sra h
    rr l
    sra h
    rr l
    sra h
    rr l
    sra h
    rr l
    ret
; A signed velocity -> DE signed 16-bit.
velocity_word:
    ld e,a
    rla
    sbc a,a
    ld d,a
    ret

    INCLUDE "input.asm"
    INCLUDE "physics.asm"
    INCLUDE "enemies.asm"
    INCLUDE "render.asm"
    INCLUDE "interface.asm"
    INCLUDE "../../lib/pcg801_runtime.asm"
    INCLUDE "generated.inc"
data_start:
phase: db 0
paused: db 0
held_key: db 0
last_key: db 0
input_buttons: db 0
last_buttons: db 0
keys_zx: db 0
help_previous: db 0
frame_count: db 0
player_x: dw 0
player_y: dw 0
velocity_x: db 0
velocity_y: db 0
grounded: db 0
coyote: db 0
jump_buffer: db 0
facing_left: db 0
previous_y: db 0
grace: db 0
lives: db 0
coins: db 0
score: dw 0
checkpoint: db 0
respawn_x: dw 0
died: db 0
camera_x: dw 0
camera_y: db 0
candidate_x: dw 0
candidate_y: db 0
target_fixed: dw 0
axis_old: dw 0
axis_end: dw 0
axis_direction: db 0
box_left: db 0
box_right: db 0
box_top: db 0
box_bottom: db 0
box_row: db 0
box_column: db 0
hit_kind: db 0
hit_pointer: dw 0
enemy_candidate: dw 0
render_row: db 0
render_column: db 0
render_first_x: db 0
render_first_y: db 0
render_start_x: db 0
render_start_y: db 0
draw_x: dw 0
draw_y: dw 0
sprite_source: dw 0
sprite_width: db 0
sprite_column: db 0
sprite_band: db 0
sprite_shift: db 0
sprite_clip: db 0
enemies: ds 36,0
world: ds 576,0
frame_buffer: ds 480,0
program_end:
    ASSERT program_end <= 0x17e3
