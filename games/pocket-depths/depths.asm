; POCKET DEPTHS - original Z80 grid-based first-person shooter.
; FR: PC-G805, ecran 24x4, chiffres ROM et icones coeur/balle.
; EN: PC-G805, 24x4 display, ROM digits and heart/bullet icons.
; MIT, Copyright (c) 2026 P.RAIMBAULT.
    INCLUDE "sharp_pc_g801.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 0
    ENDIF
    IFNDEF BUILD_LITE
BUILD_LITE EQU 0
    ENDIF
    ORG $0100

entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (key_last),a
    call title_screen
main_loop:
    IF !BUILD_LITE
    ld hl,entropy
    inc (hl)
    ENDIF
    call pcg_key_scan
    cp PCG_KEY_BREAK
    jp z,quit
    cp PCG_KEY_Q
    jp z,quit
    ld b,a
    ld a,(key_last)
    cp b
    jp z,main_loop
    ld a,b
    ld (key_last),a
    or a
    jp z,main_loop
    ld (input_key),a
    IF !BUILD_LITE
    cp PCG_KEY_N
    jp z,another_level
    ENDIF
    ld a,(phase)
    cp 1
    jr z,main_play
    cp 2
    jr z,main_help
    or a
    jr nz,.other
    ld a,(input_key)
    cp PCG_KEY_M
    jr nz,.other
    xor a
    ld (help_previous),a
    ld a,2
    ld (phase),a
    call help_screen
    jp main_loop
.other:
    ld a,(input_key)
    cp PCG_KEY_RETURN
    jr z,main_new
    cp PCG_KEY_SPACE
    jr z,main_new
    cp PCG_KEY_R
    jp nz,main_loop
main_new:
    call new_game
    call render
    jp main_loop
main_help:
    ld a,(help_previous)
    ld (phase),a
    or a
    jr nz,.game
    call title_screen
    jp main_loop
.game:
    call render
    jp main_loop
main_play:
    ld a,(input_key)
    cp PCG_KEY_R
    jr z,main_new
    cp PCG_KEY_M
    jr nz,.action
    ld a,1
    ld (help_previous),a
    ld a,2
    ld (phase),a
    call help_screen
    jp main_loop
.action:
    call handle_key
    or a
    jr z,.redraw
    ld a,(phase)
    cp 1
    jr nz,.redraw
    ld hl,turn_counter
    inc (hl)
    call enemies_tick
    ld a,(health)
    or a
    jr nz,.redraw
    ld a,3
    ld (phase),a
.redraw:
    ld a,(phase)
    cp 1
    jr z,.frame
    ld a,(hurt_flash)
    or a
    call nz,render               ; also blink the heart before defeat
    call result_screen
    jp main_loop
.frame:
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
    call load_level
    ld hl,enemies_template
    ld de,enemies
    ld bc,20
    ldir
    ld a,4
    ld (player_x),a
    ld a,13
    ld (player_y),a
    xor a
    ld (direction),a
    ld (key_owned),a
    ld (switches),a
    ld (turn_counter),a
    ld (kills),a
    ld (hurt_flash),a
    ld (frames),a
    ld (frames+1),a
    ld a,100
    ld (health),a
    ld a,24
    ld (ammo),a
    ld a,1
    ld (weapon),a
    ld (phase),a
    jp update_player_index

; A=map index -> HL=address; preserves BC/DE/IX/IY.
map_address:
    push bc
    ld c,a
    ld b,0
    ld hl,world
    add hl,bc
    pop bc
    ret
map_get:
    call map_address
    ld a,(hl)
    ret
; A=tile -> A=1 solid/NZ, A=0 walkable/Z.
is_solid:
    cp 1
    jr z,.yes
    cp 2
    jr z,.yes
    cp 3
    jr z,.yes
    cp 9
    jr z,.yes
    xor a
    ret
.yes:
    ld a,1
    or a
    ret
update_player_index:
    ld a,(player_y)
    rlca
    rlca
    rlca
    rlca
    ld b,a
    ld a,(player_x)
    or b
    ld (player_index),a
    ret
next_index:
    ld a,(next_y)
    rlca
    rlca
    rlca
    rlca
    ld b,a
    ld a,(next_x)
    or b
    ret

handle_key:
    ld a,(input_key)
    cp PCG_KEY_LEFT
    jr z,.left
    cp PCG_KEY_RIGHT
    jr z,.right
    cp PCG_KEY_1
    jr z,.knife
    cp PCG_KEY_2
    jr z,.pistol
    cp PCG_KEY_3
    jr z,.shotgun
    cp PCG_KEY_SPACE
    jp z,shoot
    cp PCG_KEY_E
    jp z,use_door
    ld a,(direction)
    ld c,a
    ld a,(input_key)
    cp PCG_KEY_UP
    jr z,.move
    cp PCG_KEY_DOWN
    jr z,.back
    cp PCG_KEY_A
    jr z,.strafe_left
    cp PCG_KEY_COMMA
    jr z,.strafe_left
    cp PCG_KEY_D
    jr z,.strafe_right
    cp PCG_KEY_SEMICOLON
    jr z,.strafe_right
    xor a
    ret
.left:
    ld a,(direction)
    dec a
    jr .turn
.right:
    ld a,(direction)
    inc a
.turn:
    and 3
    ld (direction),a
    ld a,1
    ret
.knife:
    xor a
    jr .weapon
.pistol:
    ld a,1
    jr .weapon
.shotgun:
    ld a,2
.weapon:
    ld (weapon),a
    xor a
    ret
.back:
    inc c
.strafe_right:
    inc c
    jr .move
.strafe_left:
    dec c
.move:
    ld a,c
    and 3
    call direction_delta
    ld a,(player_x)
    add a,d
    ld (next_x),a
    ld a,(player_y)
    add a,e
    ld (next_y),a
    jp try_player_move

; A=direction -> D=dx E=dy.
direction_delta:
    add a,a
    ld c,a
    ld b,0
    ld hl,directions
    add hl,bc
    ld d,(hl)
    inc hl
    ld e,(hl)
    ret

try_player_move:
    call next_index
    ld (candidate_index),a
    call enemy_at
    or a
    jp nz,.blocked
    ld a,(candidate_index)
    call map_get
    ld (event_tile),a
    cp 9
    jr z,.exit
    call is_solid
    or a
    jr nz,.blocked
    jr .commit
.exit:
    ld a,(switches)
    cp 3
    jr nz,.blocked
    ld a,(key_owned)
    or a
    jr z,.blocked
    ld a,4
    ld (phase),a
.commit:
    ld a,(next_x)
    ld (player_x),a
    ld a,(next_y)
    ld (player_y),a
    call update_player_index
    ld a,(event_tile)
    cp 4
    jr z,.ammo
    cp 5
    jr z,.heal
    cp 6
    jr z,.key
    cp 7
    jr z,.switch_a
    cp 8
    jr z,.switch_b
    ld a,1
    ret
.ammo:
    ld a,(ammo)
    add a,12
    cp 100
    jr c,.ammo_store
    ld a,99
.ammo_store:
    ld (ammo),a
    jr .consume
.heal:
    ld a,(health)
    add a,25
    cp 101
    jr c,.heal_store
    ld a,100
.heal_store:
    ld (health),a
    jr .consume
.key:
    ld a,1
    ld (key_owned),a
    jr .consume
.switch_a:
    ld a,(switches)
    or 1
    jr .switch_store
.switch_b:
    ld a,(switches)
    or 2
.switch_store:
    ld (switches),a
.consume:
    ld a,(player_index)
    call map_address
    ld (hl),0
    ld a,1
    ret
.blocked:
    xor a
    ret

use_door:
    ld a,(key_owned)
    or a
    ret z
    ld a,(direction)
    call direction_delta
    ld a,(player_x)
    add a,d
    ld (next_x),a
    ld a,(player_y)
    add a,e
    ld (next_y),a
    call next_index
    call map_address
    ld a,(hl)
    cp 3
    jr nz,.none
    ld (hl),0
    ld a,1
    ret
.none:
    xor a
    ret

; A=index -> A=1/NZ if occupied, target_enemy set; IX preserved.
enemy_at:
    push ix
    ld c,a
    ld ix,enemies
    ld b,4
.loop:
    ld a,(ix+3)
    or a
    jr z,.next
    ld a,(ix+1)
    rlca
    rlca
    rlca
    rlca
    or (ix+0)
    cp c
    jr nz,.next
    ld (target_enemy),ix
    pop ix
    ld a,1
    ret
.next:
    ld de,5
    add ix,de
    djnz .loop
    pop ix
    xor a
    ret

; World D=x E=y -> D=signed lateral, E=signed forward.
relative_position:
    ld a,(player_x)
    ld b,a
    ld a,d
    sub b
    ld c,a
    ld a,(player_y)
    ld b,a
    ld a,e
    sub b
    ld b,a
    ld a,(direction)
    or a
    jr z,.north
    dec a
    jr z,.east
    dec a
    jr z,.south
    xor a
    sub c
    ld e,a
    xor a
    sub b
    ld d,a
    ret
.north:
    ld d,c
    xor a
    sub b
    ld e,a
    ret
.east:
    ld e,c
    ld d,b
    ret
.south:
    ld e,b
    xor a
    sub c
    ld d,a
    ret

; A=x pixel -> A=first wall depth for its three-pixel strip.
depth_at_x:
    ld c,0
.divide:
    sub 3
    jr c,.done
    inc c
    jr .divide
.done:
    ld b,0
    ld hl,ray_depths
    add hl,bc
    ld a,(hl)
    ret

; D=lateral E=forward -> A=centre x, Z/C not specified, FF if culled.
project_x:
    ld a,e
    or a
    jr z,.outside
    cp 8
    jr nc,.outside
    ld a,d
    add a,8
    cp 16
    jr nc,.outside
    ld c,a
    ld a,e
    rlca
    rlca
    rlca
    rlca
    add a,c
    ld c,a
    ld b,0
    ld hl,projection_x
    add hl,bc
    ld a,(hl)
    ret
.outside:
    ld a,255
    ret

shoot:
    ld a,(weapon)
    or a
    jr z,.ready
    ld b,a
    ld a,(ammo)
    cp b
    jp c,.dry
    sub b
    ld (ammo),a
.ready:
    ld a,8
    ld (shot_distance),a
    xor a
    ld (target_enemy),a
    ld (target_enemy+1),a
    ld ix,enemies
    ld a,4
    ld (actor_count),a
.loop:
    ld a,(ix+3)
    or a
    jr z,.next
    ld d,(ix+0)
    ld e,(ix+1)
    call relative_position
    ld a,e
    or a
    jr z,.next
    cp 8
    jr nc,.next
    ld a,(shot_distance)
    cp e
    jr c,.next
    jr z,.next
    ld a,(weapon)
    cp 2
    jr z,.cone
    ld a,d
    or a
    jr nz,.next
    ld a,(weapon)
    or a
    jr nz,.visible
    ld a,e
    cp 2
    jr nc,.next
    jr .visible
.cone:
    ld a,e
    cp 4
    jr nc,.next
    ld a,d
    inc a
    cp 3
    jr nc,.next
.visible:
    ld a,e
    ld (candidate_depth),a
    call project_x
    cp 120
    jr nc,.next
    call depth_at_x
    ld b,a
    ld a,(candidate_depth)
    add a,a
    add a,a
    add a,a
    cp b
    jr nc,.next
    ld a,(candidate_depth)
    ld (shot_distance),a
    ld (target_enemy),ix
.next:
    ld de,5
    add ix,de
    ld hl,actor_count
    dec (hl)
    jp nz,.loop
    ld hl,(target_enemy)
    ld a,h
    or l
    jr z,.shot_done
    push hl
    pop ix
    ld a,(weapon)
    cp 2
    ld b,1
    jr nz,.damage
    ld b,3
.damage:
    ld a,(ix+3)
    sub b
    jr nc,.store
    xor a
.store:
    ld (ix+3),a
    or a
    jr nz,.shot_done
    ld hl,kills
    inc (hl)
.shot_done:
    ld a,1
    ret
.dry:
    xor a
    ret

enemy_distance:
    ld a,(player_x)
    sub (ix+0)
    jp p,.x
    neg
.x:
    ld c,a
    ld a,(player_y)
    sub (ix+1)
    jp p,.y
    neg
.y:
    add a,c
    ret

; IX enemy -> A=1 if axis-aligned, clear line to player, max six cells.
enemy_los:
    ld a,(player_x)
    cp (ix+0)
    jr z,.vertical
    ld a,(player_y)
    cp (ix+1)
    jr nz,.blocked
    ld a,(player_x)
    cp (ix+0)
    ld b,1
    jr nc,.start
    ld b,255
    jr .start
.vertical:
    ld a,(player_y)
    cp (ix+1)
    ld b,16
    jr nc,.start
    ld b,240
.start:
    ld a,(ix+1)
    rlca
    rlca
    rlca
    rlca
    or (ix+0)
    ld e,a
    ld a,(player_index)
    ld c,a
    ld d,7
.step:
    ld a,e
    add a,b
    ld e,a
    cp c
    jr z,.clear
    call map_get
    call is_solid
    or a
    jr nz,.blocked
    dec d
    jr nz,.step
.blocked:
    xor a
    ret
.clear:
    ld a,1
    ret

enemies_tick:
    ld ix,enemies
    ld a,4
    ld (actor_count),a
.loop:
    ld a,(ix+3)
    or a
    jp z,.next
    call enemy_distance
    cp 8
    jr nc,.forget
    cp 2
    jr c,.threat
    ld a,(ix+2)
    or a
    jr z,.approach
    call enemy_los
    or a
    jr z,.approach
.threat:
    ld a,(ix+4)
    or a
    jr z,.alert
    ld (ix+4),0
    ld b,8
    ld a,(ix+2)
    or a
    jr z,.hurt
    ld b,6
.hurt:
    ld a,(health)
    sub b
    jr nc,.hp
    xor a
.hp:
    ld (health),a
    ld a,1
    ld (hurt_flash),a
    jr .next
.alert:
    ld (ix+4),1
    jr .next
.forget:
    ld (ix+4),0
    jr .next
.approach:
    ld (ix+4),0
    ld a,(turn_counter)
    and 1
    jr nz,.next
    call move_enemy
.next:
    ld de,5
    add ix,de
    ld hl,actor_count
    dec (hl)
    jp nz,.loop
    ret

move_enemy:
    ld a,(ix+0)
    ld (next_x),a
    ld a,(ix+1)
    ld (next_y),a
    ld a,(player_x)
    cp (ix+0)
    jr z,.try_y
    ld a,(ix+0)
    jr c,.x_minus
    inc a
    jr .x_store
.x_minus:
    dec a
.x_store:
    ld (next_x),a
    call enemy_try_step
    or a
    ret nz
    ld a,(ix+0)
    ld (next_x),a
.try_y:
    ld a,(player_y)
    cp (ix+1)
    ret z
    ld a,(ix+1)
    jr c,.y_minus
    inc a
    jr .y_store
.y_minus:
    dec a
.y_store:
    ld (next_y),a
    jp enemy_try_step

enemy_try_step:
    call next_index
    ld c,a
    ld a,(player_index)
    cp c
    jr z,.blocked
    ld a,c
    ld (candidate_index),a
    call map_get
    call is_solid
    or a
    jr nz,.blocked
    ld a,(candidate_index)
    call enemy_at
    or a
    jr nz,.blocked
    ld a,(next_x)
    ld (ix+0),a
    ld a,(next_y)
    ld (ix+1),a
    ld a,1
    ret
.blocked:
    xor a
    ret

    INCLUDE "level.asm"
    INCLUDE "render.asm"
    INCLUDE "interface.asm"
    INCLUDE "../../lib/pcg801_runtime.asm"
directions: db 0,255,1,0,0,1,255,0
    INCLUDE "generated.inc"

data_start:
phase: db 0
help_previous: db 0
key_last: db 0
input_key: db 0
player_x: db 8
player_y: db 12
player_index: db 0
direction: db 0
health: db 100
ammo: db 24
weapon: db 1
key_owned: db 0
switches: db 0
turn_counter: db 0
kills: db 0
frames: dw 0
next_x: db 0
next_y: db 0
candidate_index: db 0
event_tile: db 0
target_enemy: dw 0
actor_count: db 0
candidate_depth: db 0
shot_distance: db 0
current_ray: db 0
ray_visual: db 0
hit_kind: db 0
transform_base: dw 0
hurt_flash: db 0
    IF !BUILD_LITE
level_seed: db 22
random_state: db 0
entropy: db 0
chunks_left: db 0
level_rows: db 0
level_columns: db 0
    ENDIF
profile_pointer: dw 0
write_pointer: dw 0
row_count: db 0
entity_depth: db 0
sprite_kind: db 0
sprite_center: db 0
sprite_depth: db 0
sprite_source: dw 0
sprite_width: db 0
sprite_left: db 0
sprite_x: db 0
sprite_columns: db 0
sprite_row: dw 0
sprite_visible: db 0
world: ds 256,0
enemies: ds 20,0
ray_depths: ds 40,0
screen_buffer: ds 480,0
program_end:
    IF BUILD_LITE
    ASSERT program_end <= $17E3
    ENDIF
    ASSERT program_end < $7800
