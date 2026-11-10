; POCKET CLASH - original G850 platform fighter. (c) 2026 P.RAIMBAULT, MIT.
    IFNDEF TARGET_G850
TARGET_G850 EQU 1
    ENDIF
    INCLUDE "game_platform.inc"
    IF TARGET_G850
CLASH_WIDTH EQU 144
CLASH_HEIGHT EQU 40
CLASH_BANDS EQU 5
CLASH_MIN_ZOOM EQU 8
CLASH_SPAN_Y EQU 24
CLASH_FIT_WIDTH EQU 121
CLASH_FIT_HEIGHT EQU 33
    ELSE
CLASH_WIDTH EQU 120
CLASH_HEIGHT EQU 21
CLASH_BANDS EQU 3
CLASH_MIN_ZOOM EQU 4
CLASH_SPAN_Y EQU 16
CLASH_FIT_WIDTH EQU 101
CLASH_FIT_HEIGHT EQU 19
    ENDIF
CLASH_FRAME_BYTES EQU CLASH_WIDTH*(CLASH_BANDS+1)
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 0
    ENDIF
    ORG $0100
FX EQU 0
FY EQU 2
FVX EQU 4
FVY EQU 5
FDAMAGE EQU 6
FSTOCK EQU 7
FCHAR EQU 8
FFACE EQU 9
FGROUND EQU 10
FJUMPS EQU 11
FATTACK EQU 12
FCOOL EQU 13
FSTUN EQU 14
FINVUL EQU 15
FENERGY EQU 16
FGUARD EQU 17
FBUTTON EQU 18
FLAST EQU 19
FSPECIAL EQU 21
FHIT EQU 22
FDROP EQU 23
FTYPE EQU 24
FAIR EQU 25
FSIZE EQU 32
BLEFT EQU 1
BRIGHT EQU 2
BJUMP EQU 4
BATTACK EQU 8
BSPECIAL EQU 16
BDOWN EQU 32
entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (last_key),a
    ld (selected),a
    ld (demo_mode),a
    ld (confirm_ready),a
    call title_screen
main_loop:
    call pcg_key_scan
    cp PCG_KEY_Q
    jp z,quit
    cp PCG_KEY_BREAK
    jp z,quit
    cp PCG_KEY_OFF
    jp z,quit
    ld c,a
    or a
    jr nz,.edge
    ld a,1
    ld (confirm_ready),a
.edge:
    ld a,(last_key)
    cp c
    ld a,c
    ld (last_key),a
    call nz,handle_key
    ld a,(phase)
    cp 1
    jr nz,.menu
    ld a,(paused)
    or a
    jr nz,.wait
    call world_step
    ld a,(phase)
    cp 1
    call z,draw_game
.wait:
    call frame_wait
    jp main_loop
.menu:
    call random_next
    jp main_loop
quit:
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    ret
frame_wait:
    ld bc,4000
.loop:
    dec bc
    ld a,b
    or c
    jr nz,.loop
    ret
handle_key:
    or a
    ret z
    ld b,a
    ld a,(phase)
    cp 4
    jr nz,.normal
    ld a,(help_previous)
    ld (phase),a
    cp 1
    jp z,draw_game
    jp title_screen
.normal:
    ld a,b
    cp PCG_KEY_R
    jr z,.restart
    cp PCG_KEY_M
    jr z,.help
    ld a,(phase)
    cp 1
    ld a,b
    jr z,.playing
    cp PCG_KEY_RETURN
    jr z,.confirm
    cp PCG_KEY_D
    jr z,.demo
    ld a,(phase)
    or a
    ret nz
    ld a,b
    cp PCG_KEY_LEFT
    jr z,.previous
    cp PCG_KEY_RIGHT
    jr z,.next
    cp PCG_KEY_1
    jr c,.none
    cp PCG_KEY_1+4
    jr nc,.none
    sub PCG_KEY_1
    jr .choose
.none:
    ret
.previous:
    ld a,(selected)
    dec a
    jr .choose
.next:
    ld a,(selected)
    inc a
.choose:
    and 3
    ld (selected),a
    jp title_screen
.restart:
    xor a
    ld (demo_mode),a
    jp start_cup
.demo:
    ld a,1
    ld (demo_mode),a
    jp start_cup
.confirm:
    ld a,(confirm_ready)
    or a
    ret z
    xor a
    ld (confirm_ready),a
    ld a,(phase)
    or a
    jr z,.restart
    cp 3
    jr z,.title
    ld hl,round_index
    inc (hl)
    jp start_round
.title:
    xor a
    ld (phase),a
    jp title_screen
.help:
    ld a,(phase)
    ld (help_previous),a
    ld a,4
    ld (phase),a
    jp help_screen
.playing:
    cp PCG_KEY_TAB
    jr z,.photo
    cp PCG_KEY_P
    jr z,.pause
    cp PCG_KEY_D
    ret nz
    ld a,(demo_mode)
    xor 1
    ld (demo_mode),a
    ret
.photo:
    ld a,(photo_mode)
    xor 1
    ld (photo_mode),a
    ld (paused),a
    jp draw_game
.pause:
    xor a
    ld (photo_mode),a
    ld a,(paused)
    xor 1
    ld (paused),a
    jp draw_game

world_step:
    ld hl,frame_count
    inc (hl)
    ld hl,impact_time
    ld a,(hl)
    or a
    jr z,.impact_done
    dec (hl)
.impact_done:
    ld hl,countdown
    ld a,(hl)
    or a
    jr z,.live
    dec (hl)
    jp update_camera
.live:
    ld hl,hit_pause
    ld a,(hl)
    or a
    jr z,.controls
    dec (hl)
    ret
.controls:
    xor a
    call setup_pair
    ld a,(demo_mode)
    or a
    jr nz,.auto
    call sample_controls
    jr .opponent
.auto:
    call ai_controls
.opponent:
    ld a,1
    call setup_pair
    call ai_controls
    xor a
.actor:
    ld (actor_index),a
    call setup_pair
    call fighter_step
    call melee_hit
    ld a,(actor_index)
    inc a
    cp 2
    jr c,.actor
    call update_orbs
    ld a,(fighters+FSTOCK)
    or a
    jp z,finish_round
    ld a,(fighters+FSIZE+FSTOCK)
    or a
    jp z,finish_round
    ld hl,(round_frames)
    dec hl
    ld (round_frames),hl
    ld a,h
    or l
    jp z,finish_round
    jp update_camera
setup_pair:
    ld ix,fighters
    ld iy,fighters+FSIZE
    or a
    ret z
    ld ix,fighters+FSIZE
    ld iy,fighters
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
int_to_fixed:
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ret
velocity_word:
    ld e,a
    add a,a
    sbc a,a
    ld d,a
    ret
random_next:
    ld a,(random_state)
    srl a
    jr nc,.store
    xor $B8
.store:
    ld (random_state),a
    ret
    INCLUDE "input.asm"
    INCLUDE "physics.asm"
    INCLUDE "combat.asm"
    INCLUDE "cup.asm"
    INCLUDE "render.asm"
    INCLUDE "interface.asm"
    INCLUDE "game_runtime.asm"
    IF TARGET_G850
    INCLUDE "generated.inc"
    ELSE
    INCLUDE "targets/g80x-32k/display.asm"
    INCLUDE "targets/g80x-32k/generated.inc"
    ENDIF
; Character data / personnages: Nova, Volt, Rok, Lynx.
speeds: db 36,40,26,44
jumps: db 66,62,58,76
attack_damage: db 10,8,14,9
attack_reach: db 23,21,27,22
platform_initials:
 db 32,192,80, 52,92,54, 132,172,54, 98,126,32
 db 48,176,82, 28,72,58, 152,196,58, 92,132,38
 db 36,188,78, 56,96,50, 128,168,40, 96,128,24
background_directory: dw background_0,background_1,background_2
character_names: db "NOVA",0,"VOLT",0,"ROK ",0,"LYNX",0

; Every mutable byte and drawing buffer is emitted into the user reservation.
data_start:
phase: db 0
last_key: db 0
confirm_ready: db 0
help_previous: db 0
selected: db 0
demo_mode: db 0
photo_mode: db 0
paused: db 0
round_index: db 0
frame_count: db 0
countdown: db 0
hit_pause: db 0
actor_index: db 0
pressed_buttons: db 0
random_state: db 93
round_frames: dw 1800
points: ds 4,0
knockouts: ds 4,0
damage_scores: ds 8,0
ranking: ds 4,0
fighters: ds FSIZE*2,0
orbs: ds 12,0
platforms: ds 12,0
orb_pointer: dw 0
orb_index: db 0
old_feet: dw 0
next_feet: dw 0
fighter_left: dw 0
ai_dx: dw 0
ai_y: dw 0
ai_buttons: db 0
hit_damage: db 0
hit_direction: db 0
hit_special: db 0
impact_time: db 0
impact_x: dw 0
impact_y: dw 0
result_kind: db 0
sort_i: db 0
sort_j: db 0
sort_left: db 0
sort_right: db 0
rank_row: db 0
rank_id: db 0
zoom_n: db 16
wanted_zoom: db 16
span_x: dw 0
span_y: dw 0
camera_x: dw 0
camera_y: dw 0
camera_target_x: dw 0
camera_target_y: dw 0
camera_ready: db 0
background_ptr: dw 0
background_row: db 0
draw_x: dw 0
draw_y: dw 0
sprite_id: db 0
sprite_mirror: db 0
sprite_source: dw 0
sprite_step: dw 4
sprite_column: db 0
sprite_band: db 0
sprite_shift: db 0
sprite_clip: db 0
column_address: dw 0
column_mode: db 0
column_top: db 0
platform_draw: db 0
line_x: dw 0
line_y: dw 0
line_end: dw 0
line_width: db 0
hud_actor: db 0
menu_char: db 0
frame_buffer: ds CLASH_FRAME_BYTES,0
    IF !TARGET_G850
lcd_frame: ds 480,0
    ENDIF
program_end:
    ASSERT program_end <= $7000
