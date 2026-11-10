; Pocket Vector 0.7.0 -- monochrome PC-G850 racer and three-course cup.
; Copyright (c) 2026 P.RAIMBAULT. MIT. Original code and artwork.
    IFNDEF TARGET_G850
TARGET_G850 EQU 1
    ENDIF
    INCLUDE "game_platform.inc"
    ORG PCG_USER_ORIGIN
    IF TARGET_G850
FLOOR_SCANLINES EQU 40
    ELSE
FLOOR_SCANLINES EQU 20
    ENDIF
SPIN_DURATION EQU 8
INTRO_FRAMES EQU 32
ARRIVAL_FRAMES EQU 12
COUNTDOWN_FRAMES EQU 7
GO_FRAMES EQU 6
SPEED_NORMAL EQU 192
SPEED_BOOST EQU 240
RIVAL_SCALE EQU 150
REBOUND_FRAMES EQU 10
ACCELERATION EQU 8
BRAKING EQU 12
RIVAL_SPEED_A EQU 224
RIVAL_SPEED_B EQU 232
RIVAL_CORNER_SPEED EQU 176
RIVAL_SHARP_SPEED EQU 148
RIVAL_BOOST_A EQU 244
RIVAL_BOOST_B EQU 252
entry:
    push af
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    call new_game
    xor a
    ld (phase),a
    ld a,3
    ld (confirm_release),a
    call show_frame
main_loop:
    call menu_poll_delay
    call poll_keyboard
    call filter_screen_enter
    ld a,(keys)
    bit 7,a
    jp nz,quit
    ld a,(aux_pressed)
    bit 2,a
    jp nz,restart_action
    bit 4,a
    jr z,.no_help
    ld a,(phase)
    cp 5
    jr nz,.open_help
    ld a,(help_previous)
    ld (phase),a
    jp redraw
.open_help:
    ld (help_previous),a
    ld a,5
    ld (phase),a
    jp redraw
.no_help:
    ld a,(phase)
    or a
    jp z,menu_input
    cp 5
    jr nz,.not_help
    ld a,(aux_pressed)
    bit 0,a
    jp z,main_loop
    ld a,(help_previous)
    ld (phase),a
    jp redraw
.not_help:
    cp 2
    jp z,pause_input
    cp 3
    jp z,result_input
    cp 4
    jp z,result_input
    cp 6
    jp z,cup_input
    cp 7
    jp z,start_input
    cp 8
    jp z,start_input
    cp 9
    jp z,start_input
    cp 1
    jp nz,go_menu
    ld a,(aux_pressed)
    bit 3,a
    jp nz,pause_photo
    bit 1,a
    jr z,.no_demo_toggle
    ld a,(demo_mode)
    xor 1
    ld (demo_mode),a
.no_demo_toggle:
    ld a,(pressed)
    bit 6,a
    jp nz,pause_normal
    call race_tick
redraw:
    call show_frame
    jp main_loop
menu_input:
    call menu_navigation
    ld a,(aux_pressed)
    bit 0,a
    jr nz,.start_selected
    bit 1,a
    jr nz,.demo
    ld a,(pressed)
    and 15
    jp z,main_loop
    jp redraw
.start_selected:
    ld a,(menu_choice)
    call start_session
    jp redraw
.demo:
    ld a,2
    call start_session
    jp redraw
start_input:
    ld a,(aux_pressed)
    bit 3,a
    jp nz,pause_photo
    bit 1,a
    jr z,.no_demo
    ld a,(demo_mode)
    xor 1
    ld (demo_mode),a
.no_demo:
    ld a,(pressed)
    bit 6,a
    jp nz,pause_normal
    ld a,(phase)
    cp 7
    jr nz,.tick
    ld a,(aux_pressed)
    bit 0,a
    jr z,.tick
    call begin_arrival
    jp redraw
.tick:
    call start_tick
    jp redraw
restart_action:
    ld a,(phase)
    cp 1
    jr z,restart_manual
    cp 2
    jr z,restart_manual
    cp 7
    jr z,restart_manual
    cp 8
    jr z,restart_manual
    cp 9
    jp nz,go_menu
restart_manual:
    ld a,(session_mode)
    cp 2
    jr nz,.not_demo
    ld a,1
    ld (session_mode),a
.not_demo:
    xor a
    call begin_race
    jp redraw
result_input:
    ld a,(aux_pressed)
    bit 0,a
    jp z,main_loop
    call advance_result
    jp redraw
cup_input:
    ld a,(aux_pressed)
    bit 0,a
    jp z,main_loop
go_menu:
    call block_screen_enter
    xor a
    ld (phase),a
    ld (demo_mode),a
    ld (photo_mode),a
    jp redraw
pause_photo:
    ld a,1
    ld (photo_mode),a
    jr enter_pause
pause_normal:
    xor a
    ld (photo_mode),a
enter_pause:
    push af
    ld a,(phase)
    ld (pause_previous),a
    pop af
    ld a,2
    ld (phase),a
    jp redraw
pause_input:
    ld a,(aux_pressed)
    bit 3,a
    jr nz,.photo
    bit 0,a
    jr nz,.resume
    ld a,(pressed)
    bit 6,a
    jp z,main_loop
.resume:
    ld a,(pause_previous)
    ld (phase),a
    jp redraw
.photo:
    ld a,(photo_mode)
    xor 1
    ld (photo_mode),a
    jr z,.resume
    jp redraw
show_frame:
    IF TARGET_G850
    call render
    ld hl,frame
    jp pcg850_blit
    ELSE
    jp g80x_show_frame
    ENDIF
quit:
    xor a
    out (PCG_PORT_KEYS_LOW),a
    out (PCG_PORT_KEYS_HIGH),a
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    pop af
    ret

    INCLUDE "math.asm"
    INCLUDE "keyboard.asm"
    INCLUDE "physics.asm"
    INCLUDE "cup.asm"
    INCLUDE "start.asm"
    INCLUDE "floor.asm"
    INCLUDE "render.asm"
    IF TARGET_G850
    INCLUDE "../../lib/pcg850_runtime.asm"
    ELSE
    INCLUDE "../../lib/pcg801_runtime.asm"
    INCLUDE "targets/g80x-32k/display.asm"
    ENDIF
title_text: db "POCKET VECTOR",0
model_text: db "PC-G850",0
demo_text: db "DEMO",0
speed_label: db "V",0
rank_label: db "P",0
laps_suffix: db "/3",0
pilot_names: dw player_name,rival_a_name,rival_b_name
rival_a_name: db "RIVAL A",0
rival_b_name: db "RIVAL B",0
points_text: db "PT",0
    IF BUILD_LANG_EN
intro_skip_text: db "ENTER:START GRID",0
player_name: db "YOU",0
cup_info_text: db "3 RACES 3 LAPS",0
cup_option: db "NOVA CUP",0
single_option: db "SINGLE RACE",0
demo_option: db "DEMONSTRATION",0
menu_help_text: db "ENTER:RACE M:HELP",0
next_text: db "ENTER:NEXT RACE",0
standings_text: db "ENTER:STANDINGS",0
menu_return_text: db "ENTER:MENU",0
cup_end_text: db "FINAL STANDINGS",0
cup_win_text: db "NOVA CUP WINNER",0
lap_label: db "L",0
start_text: db "ENTER:RACE D:DEMO",0
help_title_text: db "M:HELP Q:QUIT",0
pause_text: db "PAUSE",0
resume_text: db "P:RESUME Q:QUIT",0
photo_text: db "F:PHOTO",0
help1: db "ARROWS:DRIVE",0
help2: db "SPACE:BOOST (LAP 2)",0
help3: db "X:SPIN P:PAUSE",0
help4: db "F:PHOTO R:RESTART",0
help5: db "Q:QUIT D:AUTO",0
help6: db "ENTER:RETURN",0
finish_text: db "RACE COMPLETE",0
dead_text: db "SHIP DESTROYED",0
again_text: db "ENTER:RETRY Q:QUIT",0
    ELSE
intro_skip_text: db "ENTER:DEPART",0
player_name: db "VOUS",0
cup_info_text: db "3 COURSES 3 TOURS",0
cup_option: db "COUPE NOVA",0
single_option: db "COURSE LIBRE",0
demo_option: db "DEMONSTRATION",0
menu_help_text: db "ENTER:JOUER M:AIDE",0
next_text: db "ENTER:COURSE SUIVANTE",0
standings_text: db "ENTER:CLASSEMENT",0
menu_return_text: db "ENTER:MENU",0
cup_end_text: db "CLASSEMENT FINAL",0
cup_win_text: db "COUPE NOVA REMPORTEE",0
lap_label: db "T",0
start_text: db "ENTER:COURSE D:DEMO",0
help_title_text: db "M:AIDE Q:QUITTER",0
pause_text: db "PAUSE",0
resume_text: db "P:REPRENDRE Q:QUITTER",0
photo_text: db "F:PHOTO",0
help1: db "FLECHES:PILOTER",0
help2: db "ESPACE:TURBO (TOUR 2)",0
help3: db "X:VRILLE P:PAUSE",0
help4: db "F:PHOTO R:REJOUER",0
help5: db "Q:QUITTER D:AUTO",0
help6: db "ENTER:RETOUR",0
finish_text: db "COURSE TERMINEE",0
dead_text: db "VAISSEAU DETRUIT",0
again_text: db "ENTER:REJOUER Q:QUITTER",0
    ENDIF

    IF TARGET_G850
    INCLUDE "assets.inc"
    ELSE
    INCLUDE "targets/g80x-32k/assets.inc"
    ENDIF
    ASSERT LOW texture_map == 0
    ASSERT LOW texture_masks == 0
state_begin:
phase: db 0
demo_mode: db 0
photo_mode: db 0
help_previous: db 0
pause_previous: db 1
intro_angle: db 0
start_timer: db 0
countdown_stage: db 0
go_frames: db 0
intro_center_x: dw 0
intro_center_y: dw 0
view_heading: db 0
camera_distance: db 0
camera_center_x: dw 0
camera_center_y: dw 0
race_awarded: db 0
auto_delta: db 0
auto_dx: db 0
auto_dy: db 0
auto_cos: db 0
auto_sin: db 0
auto_cross: dw 0
auto_cross_sign: db 0
auto_dot: dw 0
keys: db 0
previous_keys: db 0
pressed: db 0
aux_keys: db 0
previous_aux: db 0
aux_pressed: db 0
confirm_release: db 0
control_keys: db 0
control_pressed: db 0
player_x: dw 0
player_y: dw 0
player_started: db 0
candidate_x: dw 0
candidate_y: dw 0
velocity_x: dw 0
velocity_y: dw 0
heading: db 0
speed: db 0
energy: db 0
lap: db 0
rank: db 0
section: db 0
old_section: db 0
checkpoint: db 0
finish_order: db 0
player_finish: db 0
rival1_finish: db 0
rival2_finish: db 0
frame_counter: dw 0
boosting: db 0
spin_frames: db 0
spin_cooldown: db 0
hurt_frames: db 0
rebound_frames: db 0
blocked_axes: db 0
bounce_ax: db 0
bounce_ay: db 0
motion_sin: db 0
sample_x: db 0
sample_y: db 0
search_node: db 0
search_left: db 0
best_distance: db 0
bounce_nx: db 0
bounce_ny: db 0
bounce_projection: db 0
push_dx: dw 0
push_dy: dw 0
rival1_progress: dw 0
rival1_lap: db 0
rival1_energy: db 0
rival1_hit: db 0
rival1_stun: db 0
rival1_x: dw 0
rival1_y: dw 0
rival1_speed: db 0
rival1_push_x: dw 0
rival1_push_y: dw 0
rival1_started: db 0
rival2_progress: dw 0
rival2_lap: db 0
rival2_energy: db 0
rival2_hit: db 0
rival2_stun: db 0
rival2_x: dw 0
rival2_y: dw 0
rival2_speed: db 0
rival2_push_x: dw 0
rival2_push_y: dw 0
rival2_started: db 0
rival_step_scale: dw 0
unpack_count: db 0
rival_node: db 0
rival_fraction: db 0
rival_base_x: db 0
rival_base_y: db 0
rival_heading: db 0
rival_turn: db 0
camera_x: dw 0
camera_y: dw 0
camera_cos: db 0
camera_sin: db 0
camera_quadrant: db 0
rows_to_prepare: db 0
floor_band: dw 0
floor_rows: db 0
projection1: ds 6,0
projection2: ds 6,0
project_dx: db 0
project_dy: db 0
project_depth: db 0
project_negative: db 0
project_center: db 0
project_height: db 0
dot_temp: dw 0
sprite_width: db 0
sprite_left: db 0
sprite_bits: db 0
sprite_pairs: db 0
sprite_mirror: db 0
plot_x: db 0
hud_x: db 0
text_x: db 0
text_page: db 0
score_index: db 0
key_index: db 0
target_key: dw 0
racer_keys: ds 6,0
race_places: ds 3,0
race_points: ds 3,0
result_row: db 0
state_end:
; These values survive a per-race reset, but start_session clears cup totals.
menu_choice: db 0
menu_track: db 0
session_mode: db 0
track_index: db 0
cup_round: db 0
cup_points: ds 3,0
cup_place:
cup_places: ds 3,0
row_table: ds FLOOR_SCANLINES*8,0
frame: ds 864,0
    IF !TARGET_G850
lcd_frame: ds 480,0
native_page: db 0
native_x: db 0
sample_rows_left: db 0
native_bits: db 0
    ENDIF
path_nodes: ds 512,0
skyline: ds 144,0
    ALIGN 256
texture_map: ds 2048,0
road_map: ds 2048,0
program_end:
    ; Leave BASIC/monitor workspace and the caller's stack above the game.
    ASSERT program_end <= 0x7000
