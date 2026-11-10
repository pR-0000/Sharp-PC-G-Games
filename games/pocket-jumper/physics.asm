; FR/EN: Q12.4 positions, signed Q4.4 velocities, swept pixel collision.
move_x:
    ld a,(velocity_x)
    ld (axis_direction),a
    call velocity_word
    ld hl,(player_x)
    add hl,de
    ld (target_fixed),hl
    call fixed_to_int
    ld (axis_end),hl
    ld hl,(player_x)
    call fixed_to_int
    ld (candidate_x),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    ld (candidate_y),a
move_x_loop:
    ld hl,(candidate_x)
    ld de,(axis_end)
    or a
    sbc hl,de
    jr z,move_x_finish
    ld hl,(candidate_x)
    ld (axis_old),hl
    ld a,(axis_direction)
    bit 7,a
    jr nz,move_x_left
    inc hl
    jr move_x_probe
move_x_left:
    dec hl
move_x_probe:
    ld (candidate_x),hl
    call box_free
    jr c,move_x_loop
    xor a
    ld (velocity_x),a
    ld hl,(axis_old)
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld (player_x),hl
    ret
move_x_finish:
    ld hl,(target_fixed)
    ld (player_x),hl
    ret
move_y:
    ld a,(velocity_y)
    ld (axis_direction),a
    call velocity_word
    ld hl,(player_y)
    add hl,de
    ld (target_fixed),hl
    call fixed_to_int
    ld (axis_end),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    ld (candidate_y),a
    ld hl,(player_x)
    call fixed_to_int
    ld (candidate_x),hl
move_y_loop:
    ld a,(candidate_y)
    ld b,a
    ld a,(axis_end)
    cp b
    jr z,move_y_finish
    ld a,b
    ld (axis_old),a
    ld a,(axis_direction)
    bit 7,a
    ld a,b
    jr nz,move_y_up
    inc a
    jr move_y_probe
move_y_up:
    dec a
move_y_probe:
    ld (candidate_y),a
    call box_free
    jr c,move_y_loop
    ld a,(axis_direction)
    bit 7,a
    call nz,head_hit
    ld a,(axis_old)
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld (player_y),hl
    xor a
    ld (velocity_y),a
    ret
move_y_finish:
    ld hl,(target_fixed)
    ld (player_y),hl
    ret
check_ground:
    ld a,(velocity_y)
    bit 7,a
    ret nz
    ld hl,(player_x)
    call fixed_to_int
    ld (candidate_x),hl
    ld hl,(player_y)
    call fixed_to_int
    inc l
    ld a,l
    ld (candidate_y),a
    call box_free
    ret c
    ld a,1
    ld (grounded),a
    xor a
    ld (velocity_y),a
    ld hl,(player_y)
    ld a,l
    and 240
    ld l,a
    ld (player_y),hl
    ret

; B tile x, C tile y -> tile A, pointer HL. X outside is solid; below is air.
tile_at:
    ld a,b
    cp 96
    jr nc,tile_wall
    ld a,c
    cp WORLD_ROWS
    jr nc,tile_air_return
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld d,h
    ld e,l
    add hl,hl
    add hl,de
    ld e,b
    ld d,0
    add hl,de
    ld de,world
    add hl,de
    ld a,(hl)
    ret
tile_wall:
    ld a,1
    ret
tile_air_return:
    xor a
    ret
is_solid:
    cp 1
    jr c,not_solid
    cp 4
    jr c,solid_yes
    cp 8
    jr z,solid_yes
not_solid:
    or a
    ret
solid_yes:
    scf
    ret
box_bounds:
    ld a,(candidate_y)
    cp WORLD_H+16
    jr nc,not_solid
    ld hl,(candidate_x)
    ld a,h
    cp 3
    jr nc,not_solid
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld a,l
    ld (box_left),a
    ld (box_column),a
    ld hl,(candidate_x)
    ld de,HERO_W-1
    add hl,de
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld a,l
    ld (box_right),a
    ld a,(candidate_y)
    srl a
    srl a
    srl a
    ld (box_top),a
    ld (box_row),a
    ld a,(candidate_y)
    add a,HERO_H-1
    srl a
    srl a
    srl a
    ld (box_bottom),a
    scf
    ret
box_free:
    xor a
    ld (hit_kind),a
    call box_bounds
    ret nc
box_probe:
    ld a,(box_column)
    ld b,a
    ld a,(box_row)
    ld c,a
    call tile_at
    call is_solid
    jr c,box_hit
    call box_next
    jr c,box_probe
    scf
    ret
box_hit:
    ld (hit_kind),a
    ld (hit_pointer),hl
    or a
    ret
box_next:
    ld a,(box_column)
    ld b,a
    ld a,(box_right)
    cp b
    jr z,box_next_row
    ld hl,box_column
    inc (hl)
    scf
    ret
box_next_row:
    ld a,(box_row)
    ld b,a
    ld a,(box_bottom)
    cp b
    jp z,not_solid
    ld hl,box_row
    inc (hl)
    ld a,(box_left)
    ld (box_column),a
    scf
    ret
head_hit:
    ld a,(hit_kind)
    cp 2
    jr z,break_brick
    cp 3
    ret nz
    ld hl,(hit_pointer)
    ld (hl),8
    call coin_increment
    ld hl,50
    jp add_score
break_brick:
    ld hl,(hit_pointer)
    ld (hl),0
    ld hl,10
    jp add_score
collect_items:
    ld hl,(player_x)
    call fixed_to_int
    ld (candidate_x),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    ld (candidate_y),a
    call box_bounds
    ret nc
collect_probe:
    ld a,(box_column)
    ld b,a
    ld a,(box_row)
    ld c,a
    call tile_at
    cp 4
    jr z,collect_coin
    cp 5
    jp z,lose_life
    cp 6
    jr z,reach_goal
    cp 7
    jr z,reach_checkpoint
collect_next:
    call box_next
    jr c,collect_probe
    ret
collect_coin:
    ld (hl),0
    call coin_increment
    ld hl,10
    call add_score
    jr collect_next
reach_checkpoint:
    ld a,(checkpoint)
    or a
    jr nz,collect_next
    inc a
    ld (checkpoint),a
    ld a,(box_column)
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    ld (respawn_x),hl
    jr collect_next
reach_goal:
    ld hl,500
    call add_score
    ld a,3
    ld (phase),a
    ld hl,win_text
    jp result_screen
coin_increment:
    ld a,(coins)
    cp 99
    ret nc
    inc a
    ld (coins),a
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
lose_life:
    ld a,1
    ld (died),a
    ld hl,lives
    dec (hl)
    jp nz,reset_player
    ld a,2
    ld (phase),a
    ld hl,over_text
    jp result_screen

