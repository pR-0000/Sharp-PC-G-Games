; FR/EN: waypoint-guided AI and ordered gates, without stored trajectories.
gate_delta:
    call car_coords
    ld a,(ix+6)
    add a,a
    ld e,a
    ld d,0
    ld hl,(active_gates)
    add hl,de
    ld b,(hl)
    inc hl
    ld c,(hl)
    ld l,0
    ld a,(car_x)
    ld e,a
    ld a,b
    sub e
    jr nc,gate_dx_ready
    neg
    set 0,l
gate_dx_ready:
    ld (gate_dx),a
    ld a,(car_y)
    ld e,a
    ld a,c
    sub e
    jr nc,gate_dy_ready
    neg
    set 1,l
gate_dy_ready:
    ld (gate_dy),a
    ld a,l
    ld (gate_signs),a
    ret
gate_distance:
    ld a,(gate_dx)
    ld b,a
    ld a,(gate_dy)
    cp b
    ret nc
    ld a,b
    ret
pass_gate:
    call gate_delta
    ld a,(gate_dx)
    cp 10
    ret nc
    ld a,(gate_dy)
    cp 10
    ret nc
    ld a,(ix+6)
    or a
    jr nz,gate_touched
    ld a,(gate_dx)
    or a
    jr z,gate_touched
    ld a,(gate_signs)
    and 1                    ; finish line requires x >= start x
    ret z
gate_touched:
    ld a,(gate_count)
    ld b,a
    ld a,(ix+6)
    ld c,a
    inc a
    cp b
    jr c,gate_store
    xor a
gate_store:
    ld (ix+6),a
    ld a,c
    or a
    ret nz
    inc (ix+7)
    ld a,(ix+7)
    cp 3
    ret c
    ld (ix+8),1
    ld (ix+5),0
    ld hl,(race_ticks)
    ld (ix+9),l
    ld (ix+10),h
    ret
ai_controls:
    call gate_delta
    ld a,(gate_dx)
    srl a
    ld b,a
    ld a,(gate_dy)
    cp b
    jr c,ai_horizontal
    srl a
    ld b,a
    ld a,(gate_dx)
    cp b
    jr c,ai_vertical
    ld a,2
    jr ai_quadrant
ai_horizontal:
    xor a
    jr ai_quadrant
ai_vertical:
    ld a,4
ai_quadrant:
    ld b,a
    ld a,(gate_signs)
    bit 0,a
    jr z,ai_y_sign
    ld a,8
    sub b
    ld b,a
ai_y_sign:
    ld a,(gate_signs)
    bit 1,a
    ld a,b
    jr z,ai_angle_ready
    neg
    and 15
ai_angle_ready:
    ld (desired_angle),a
    sub (ix+4)
    and 15
    ld b,a
    push ix
    pop hl
    ld a,l
    cp LOW(cars+CAR_SIZE)
    ld a,5
    jr nz,ai_cruise_speed
    dec a
ai_cruise_speed:
    ld (desired_speed),a
    ld a,b
    cp 3
    jr c,ai_steering
    cp 14
    jr nc,ai_steering
    ld a,3
    ld (desired_speed),a
ai_steering:
    ld a,(frame_count)
    and 1
    jr nz,ai_speed
    ld a,b
    or a
    jr z,ai_speed
    cp 8
    ld a,(ix+4)
    jr nc,ai_left
    inc a
    jr ai_store_angle
ai_left:
    dec a
ai_store_angle:
    and 15
    ld (ix+4),a
ai_speed:
    ld a,(frame_count)
    and 3
    ret nz
    ld a,(desired_speed)
    cp (ix+5)
    ret z
    jr c,ai_slow
    inc (ix+5)
    ret
ai_slow:
    dec (ix+5)
    ret
car_contact:
    ld a,(hit_flash)
    or a
    ret nz
    ld ix,cars
    call car_coords
    ld ix,cars+CAR_SIZE
    ld b,2
contact_next:
    push bc
    ld l,(ix+0)
    ld h,(ix+1)
    call fixed_to_int
    ld a,(car_x)
    sub l
    jr nc,contact_dx
    neg
contact_dx:
    cp 7
    jr nc,contact_skip
    ld l,(ix+2)
    ld h,(ix+3)
    call fixed_to_int
    ld a,(car_y)
    sub l
    jr nc,contact_dy
    neg
contact_dy:
    cp 6
    jr nc,contact_skip
    ld a,1
    ld (cars+5),a
    ld a,8
    ld (hit_flash),a
contact_skip:
    ld de,CAR_SIZE
    add ix,de
    pop bc
    djnz contact_next
    ret
progress_of_car:
    ld a,(ix+7)
    rlca
    rlca
    rlca
    rlca
    ld b,a
    ld a,(ix+6)
    or a
    jr nz,progress_gate
    ld a,(gate_count)
progress_gate:
    dec a
    add a,b
    ret
update_rank:
    ld a,1
    ld (race_rank),a
    ld ix,cars
    call progress_of_car
    ld (player_progress),a
    call gate_delta
    call gate_distance
    ld (player_distance),a
    ld ix,cars+CAR_SIZE
    ld b,2
rank_next:
    push bc
    ld a,(cars+8)
    and (ix+8)
    jr z,rank_progress
    ld l,(ix+9)
    ld h,(ix+10)
    ld de,(cars+9)
    or a
    sbc hl,de
    jr c,rank_ahead
    jr rank_skip
rank_progress:
    call progress_of_car
    ld b,a
    ld a,(player_progress)
    cp b
    jr c,rank_ahead
    jr nz,rank_skip
    call gate_delta
    call gate_distance
    ld b,a
    ld a,(player_distance)
    cp b
    jr z,rank_skip
    jr c,rank_skip
rank_ahead:
    ld hl,race_rank
    inc (hl)
rank_skip:
    ld de,CAR_SIZE
    add ix,de
    pop bc
    djnz rank_next
    ret
