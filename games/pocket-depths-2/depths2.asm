; Pocket Depths 2 - runtime DDA / DDA execute sur le Z80.
; Copyright (c) 2026 P.RAIMBAULT. MIT.
    INCLUDE "game_platform.inc"
    IF TARGET_G850
    INCLUDE "targets/g850/config.inc"
    ELSE
    INCLUDE "targets/g80x/config.inc"
    ENDIF
    ORG 0x100
entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (last_key),a
    call title
main_loop:
    call pcg_key_scan
    ld b,a
    ld a,(last_key)
    cp b
    jr nz,new_key
    ld a,b
    cp PCG_KEY_UP
    jr z,new_key
    cp PCG_KEY_DOWN
    jr z,new_key
    cp PCG_KEY_LEFT
    jr z,new_key
    cp PCG_KEY_RIGHT
    jr z,new_key
    cp PCG_KEY_COMMA
    jr z,new_key
    cp PCG_KEY_SEMICOLON
    jr nz,main_loop
new_key:
    ld a,b
    ld (last_key),a
    or a
    jr z,main_loop
    cp PCG_KEY_Q
    jp z,quit
    cp PCG_KEY_BREAK
    jp z,quit
    ld b,a
    ld a,(phase)
    cp 1
    jr z,main_play
    ld a,b
    cp PCG_KEY_RETURN
    jr z,restart
    cp PCG_KEY_R
    jp nz,main_loop
restart:
    call new_game
    call render
    jp main_loop
main_play:
    ld a,b
    cp PCG_KEY_R
    jr z,restart
    cp PCG_KEY_M
    jr z,main_help
    cp PCG_KEY_P
    jr z,main_pause
    xor a
    ld (turn_used),a
    ld a,b
    call action
    ld a,(turn_used)
    or a
    jp z,main_loop
    call enemies_tick
    call render
    ld a,(hurt)
    or a
    call nz,hurt_flash
    ld a,(phase)
    cp 1
    jp z,main_loop
    call result_screen
    jp main_loop
main_help:
    call help_screen
    jr modal_wait
main_pause:
    ld hl,pause_text
    call message
modal_wait:
    call pcg_key_scan
    or a
    jr nz,modal_wait
modal_press:
    call pcg_key_scan
    or a
    jr z,modal_press
    cp PCG_KEY_Q
    jr z,quit
    cp PCG_KEY_BREAK
    jr z,quit
    ld (last_key),a
    call render
    jp main_loop
quit:
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    ret

new_game:
    ld hl,level_initial
    ld de,world
    ld bc,256
    ldir
    ld hl,actors_initial
    ld de,actors
    ld bc,27
    ldir
    ld hl,0x0380
    ld (player_x),hl
    ld hl,0x0d80
    ld (player_y),hl
    ld a,192
    ld (angle),a
    ld a,1
    ld (phase),a
    ld a,100
    ld (health),a
    ld a,24
    ld (ammo),a
    xor a
    ld (key_owned),a
    ld (hurt),a
    ld (turn_clock),a
    ret

; A key -> one action. Actions are key edges, never delay loops.
action:
    cp PCG_KEY_LEFT
    jr z,turn_left
    cp PCG_KEY_RIGHT
    jr z,turn_right
    cp PCG_KEY_SPACE
    jp z,shoot
    cp PCG_KEY_E
    jp z,open_door
    ld b,0
    cp PCG_KEY_UP
    jr z,move_key
    ld b,128
    cp PCG_KEY_DOWN
    jr z,move_key
    ld b,192
    cp PCG_KEY_COMMA
    jr z,move_key
    ld b,64
    cp PCG_KEY_SEMICOLON
    ret nz
move_key:
    ld a,(angle)
    add a,b
    ld (move_angle),a
    call move_player
    jp used_turn
turn_left:
    ld a,(angle)
    sub 8
    jr turn_store
turn_right:
    ld a,(angle)
    add a,8
turn_store:
    ld (angle),a
used_turn:
    ld a,1
    ld (turn_used),a
    ret

; A sine phase -> A signed component, magnitude <=127.
trig:
    ld c,a
    and 63
    bit 6,c
    jr z,trig_index
    neg
    add a,64
trig_index:
    ld e,a
    ld d,0
    ld hl,sin_quarter
    add hl,de
    ld a,(hl)
    bit 7,c
    ret z
    neg
    ret

; Walking: 1/4 cell per press; collision radius 32/256 cell, slide axes.
move_player:
    ld a,(move_angle)
    add a,64
    call trig
    call move_component
    ld hl,(player_x)
    add hl,de
    ld (candidate),hl
    ld a,h
    ld (probe_x),a
    ld a,(player_y+1)
    ld (probe_y),a
    ld a,e
    ld hl,player_x
    call try_axis
    ld a,(move_angle)
    call trig
    call move_component
    ld hl,(player_y)
    add hl,de
    ld (candidate),hl
    ld a,h
    ld (probe_y),a
    ld a,(player_x+1)
    ld (probe_x),a
    ld a,e
    ld hl,player_y
    call try_axis
    jp collect
move_component:
    sra a
    ld e,a
    rla
    sbc a,a
    ld d,a
    ret
try_axis:
    push hl
    ld hl,(player_x)
    ld (test_x),hl
    ld hl,(player_y)
    ld (test_y),hl
    pop de
    push de
    ld a,e
    cp player_x & 255
    ld hl,(candidate)
    jr nz,try_y
    ld (test_x),hl
    jr try_probe
try_y:
    ld (test_y),hl
try_probe:
    call position_clear
    pop de
    ret nc
    ld hl,(candidate)
    ex de,hl
    ld (hl),e
    inc hl
    ld (hl),d
    ret
; Check all four corners of a 64/256-cell bounding square.
position_clear:
    ld hl,(test_x)
    ld de,-32
    add hl,de
    ld b,h
    ld hl,(test_y)
    add hl,de
    ld c,h
    call point_clear
    ret nc
    ld hl,(test_x)
    ld de,32
    add hl,de
    ld b,h
    call point_clear
    ret nc
    ld hl,(test_y)
    ld de,32
    add hl,de
    ld c,h
    call point_clear
    ret nc
    ld hl,(test_x)
    ld de,-32
    add hl,de
    ld b,h
point_clear:
    call tile_at
    cp 2
    jr z,try_blocked
    cp 1
    jr z,try_blocked
    ; Do not walk through a live monster's cell.
    ld ix,actors
    ld a,3
try_actor:
    push af
    ld a,(ix+2)
    or a
    jr z,try_actor_next
    ld a,(ix+0)
    cp b
    jr nz,try_actor_next
    ld a,(ix+1)
    cp c
    jr z,try_actor_blocked
try_actor_next:
    ld de,3
    add ix,de
    pop af
    dec a
    jr nz,try_actor
    scf
    ret
try_actor_blocked:
    pop af
try_blocked:
    or a
    ret

; BC integer map coordinates, returns tile A; preserves BC. OOB solid.
tile_at:
    ld a,b
    cp 16
    jr nc,tile_out
    ld a,c
    cp 16
    jr nc,tile_out
    add a,a
    add a,a
    add a,a
    add a,a
    add a,b
    ld l,a
    ld h,0
    ld de,world
    add hl,de
    ld a,(hl)
    ret
tile_out:
    ld a,1
    ret

collect:
    ld a,(player_x+1)
    ld b,a
    ld a,(player_y+1)
    ld c,a
    call tile_at
    cp 3
    jr z,pick_health
    cp 4
    jr z,pick_ammo
    cp 5
    jr z,pick_key
    cp 6
    ret nz
    ld a,(key_owned)
    or a
    ret z
    ld a,4
    ld (phase),a
    ret
pick_health:
    ld a,100
    ld (health),a
    jr pick_clear
pick_ammo:
    ld a,(ammo)
    add a,12
    cp 100
    jr c,pick_ammo_store
    ld a,99
pick_ammo_store:
    ld (ammo),a
    jr pick_clear
pick_key:
    ld a,1
    ld (key_owned),a
pick_clear:
    xor a
    ld (hl),a
    ret

; E opens a door <=1.5 cell ahead using the exact centre DDA.
open_door:
    ld a,(angle)
    call cast_ray
    ld a,(hit_tile)
    cp 2
    ret nz
    ld hl,(hit_distance)
    ld de,384
    or a
    sbc hl,de
    ret nc
    ld a,(map_x)
    ld b,a
    ld a,(map_y)
    ld c,a
    call tile_at
    ld (hl),0
    jp used_turn

; Hitscan in camera coordinates, nearest live target inside reticle.
shoot:
    ld a,(ammo)
    or a
    ret z
    dec a
    ld (ammo),a
    ld a,(angle)
    call cast_ray
    ld hl,(hit_distance)
    ld (shot_limit),hl
    ld hl,0x7fff
    ld (best_distance),hl
    ld hl,0
    ld (best_actor),hl
    ld ix,actors
    ld b,3
shoot_next:
    push bc
    ld a,(ix+2)
    or a
    jr z,shoot_skip
    call actor_transform
    call actor_in_front
    jr nc,shoot_skip
    ld hl,(view_side)
    call abs_hl
    ld de,100
    or a
    sbc hl,de
    jr nc,shoot_skip
    ld hl,(view_forward)
    ld de,(shot_limit)
    or a
    sbc hl,de
    jr nc,shoot_skip
    ld hl,(view_forward)
    ld de,(best_distance)
    or a
    sbc hl,de
    jr nc,shoot_skip
    call line_of_sight
    jr nc,shoot_skip
    ld hl,(view_forward)
    ld (best_distance),hl
    ld (best_actor),ix
shoot_skip:
    ld de,3
    add ix,de
    pop bc
    djnz shoot_next
    ld ix,(best_actor)
    push ix
    pop hl
    ld a,h
    or l
    jr z,shot_done
    dec (ix+2)
shot_done:
    jp used_turn

; Stationary sentries: one volley / 8 actions, within 3 cells and LOS.
enemies_tick:
    xor a
    ld (hurt),a
    ld a,(phase)
    cp 1
    ret nz
    ld hl,turn_clock
    inc (hl)
    ld a,(hl)
    and 7
    ret nz
    ld ix,actors
    ld b,3
enemy_next:
    push bc
    ld a,(ix+2)
    or a
    jr z,enemy_skip
    ; Exact grid LOS via a DDA aimed at the actor's cell centre.
    call actor_transform
    ld hl,(actor_dx)
    call abs_hl
    ld de,768
    or a
    sbc hl,de
    jr nc,enemy_skip
    ld hl,(actor_dy)
    call abs_hl
    ld de,768
    or a
    sbc hl,de
    jr nc,enemy_skip
    call line_of_sight
    jr nc,enemy_skip
    ld a,(health)
    sub 8
    jr nc,enemy_health
    xor a
enemy_health:
    ld (health),a
    ld a,1
    ld (hurt),a
enemy_skip:
    ld de,3
    add ix,de
    pop bc
    djnz enemy_next
    ld a,(health)
    or a
    ret nz
    ld a,3
    ld (phase),a
    ret

    INCLUDE "raycaster.asm"
    INCLUDE "render.asm"
    IF TARGET_G850
    INCLUDE "targets/g850/weapon.asm"
    ENDIF
    INCLUDE "interface.asm"
    INCLUDE "../../lib/game_runtime.asm"
    IF TARGET_G850
    INCLUDE "targets/g850/generated.inc"
    ELSE
    INCLUDE "generated.inc"
    ENDIF

; Mutable storage is emitted/reserved in USER, never in firmware RAM.
data_start:
phase:          db 0
last_key:       db 0
turn_used:      db 0
turn_clock:     db 0
hurt:           db 0
    IF TARGET_G850
gun_column: db 0
gun_row: db 0
gun_bits: dw 0
gun_mask: dw 0
    ENDIF
health:         db 0
ammo:           db 0
key_owned:      db 0
angle:          db 0
move_angle:     db 0
player_x:       dw 0
player_y:       dw 0
candidate:      dw 0
test_x:         dw 0
test_y:         dw 0
probe_x:        db 0
probe_y:        db 0
map_x:          db 0
map_y:          db 0
step_x:         db 0
step_y:         db 0
side_x:         dw 0
side_y:         dw 0
delta_x:        dw 0
delta_y:        dw 0
hit_distance:   dw 0
hit_tile:       db 0
hit_side:       db 0
hit_u:          db 0
ray_angle:      db 0
ray_index:      db 0
ray_budget:     db 0
wall_height:    db 0
wall_top:       db 0
draw_x:         db 0
draw_y:         db 0
draw_bottom:    db 0
draw_kind:      db 0
draw_step:      db 0
actor_dx:       dw 0
actor_dy:       dw 0
view_forward:   dw 0
view_side:      dw 0
transform_sign: db 0
transform_angle: db 0
shot_limit:     dw 0
best_distance:  dw 0
best_actor:     dw 0
sprite_x:       db 0
sprite_left:    db 0
sprite_width:   db 0
sprite_column:  db 0
sprite_row:     db 0
sprite_bits:    db 0
sprite_counter: db 0
actor_order:    ds 9,0
actor_depths:   ds 18,0
billboard_source: dw 0
billboard_kind: db 0
sprite_row_masks: ds VIEW_H,0
actors:         ds 27,0
world:          ds 256,0
depth_buffer:   ds RAY_COUNT*2,0
frame_buffer:   ds PCG_FRAME_BYTES,0
program_end:
    IF TARGET_G850
    ASSERT program_end <= 0x7000
    ELSE
    ASSERT program_end <= 0x17e3
    ENDIF
