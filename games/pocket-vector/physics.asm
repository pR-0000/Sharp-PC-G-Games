; Original arcade rules inspired by QL-Zero. No QL implementation is copied.
; Coordinates/velocities Q8.8; heading 0..63, 128 ordered path nodes.
new_game:
    push af
    ld a,(keys)
    ld d,a
    ld a,(aux_keys)
    ld e,a
    push de
    ld hl,state_begin
    ld de,state_begin+1
    ld bc,state_end-state_begin-1
    ld (hl),0
    ldir
    pop de
    ld a,d
    ld (keys),a
    ld a,e
    ld (aux_keys),a
    pop af
    ld (demo_mode),a
    call load_track
    ld a,1
    ld (phase),a
    ld (lap),a
    ld (rival1_lap),a
    ld (rival2_lap),a
    ld a,100
    ld (energy),a
    ld a,48
    ld (rival1_energy),a
    ld (rival2_energy),a
    ld a,124
    ld (section),a
    call node_pointer
    ld d,(hl)
    inc hl
    ld b,(hl)
    inc hl
    ld a,(hl)
    ld (heading),a
    ld a,d
    ld (player_x+1),a
    ld a,b
    ld (player_y+1),a
    ld hl,0x7E00
    ld (rival1_progress),hl
    ld hl,0x7F00
    ld (rival2_progress),hl
    ld ix,rival1_progress
    call place_rival
    ld ix,rival2_progress
    call place_rival
    jp update_rank

race_tick:
    ld hl,(frame_counter)
    inc hl
    ld (frame_counter),hl
    ld hl,go_frames
    call decay_byte
    ld hl,hurt_frames
    call decay_byte
    ld hl,rebound_frames
    call decay_byte
    ld hl,spin_cooldown
    call decay_byte
    ld hl,spin_frames
    call decay_byte
    ld hl,rival1_hit
    call decay_byte
    ld hl,rival2_hit
    call decay_byte
    ld hl,rival1_stun
    call decay_byte
    ld hl,rival2_stun
    call decay_byte
    ld a,(keys)
    ld (control_keys),a
    ld a,(pressed)
    ld (control_pressed),a
    ld a,(demo_mode)
    or a
    call nz,autopilot
    call start_spin
    call drive_player
    call update_section
    call update_laps
    call update_rivals
    call ship_contacts
    call update_rank
    ld a,(energy)
    or a
    jr nz,.not_dead
    ld a,4
    ld (phase),a
.not_dead:
    ld a,(phase)
    cp 1
    ret z
    jp finish_race
decay_byte:
    ld a,(hl)
    or a
    ret z
    dec (hl)
    ret

autopilot:
    ; Aim at an actual waypoint, so rebounds are corrected laterally as well.
    ld a,(section)
    add a,3
    call node_pointer
    ld a,(player_x+1)
    ld b,a
    ld a,(hl)
    sub b
    ld (auto_dx),a
    inc hl
    ld a,(player_y+1)
    ld b,a
    ld a,(hl)
    sub b
    ld (auto_dy),a
    ld a,(heading)
    call get_direction
    ld a,d
    ld (auto_cos),a
    ld a,e
    ld (auto_sin),a
    ld a,(auto_dx)
    ld d,a
    call mul_both_signed
    ld (auto_cross),hl
    ld a,(auto_dy)
    ld d,a
    ld a,(auto_cos)
    ld e,a
    call mul_both_signed
    ld de,(auto_cross)
    or a
    sbc hl,de
    ld (auto_cross),hl
    ld a,(auto_dx)
    ld d,a
    ld a,(auto_cos)
    ld e,a
    call mul_both_signed
    ld (auto_dot),hl
    ld a,(auto_dy)
    ld d,a
    ld a,(auto_sin)
    ld e,a
    call mul_both_signed
    ld de,(auto_dot)
    add hl,de
    ld (auto_dot),hl
    ld hl,(auto_cross)
    ld a,h
    and 128
    ld (auto_cross_sign),a
    call nz,neg_hl
    ld (auto_cross),hl
    ld de,64
    or a
    sbc hl,de
    ld c,4
    jr c,.straight
    ld a,(auto_cross_sign)
    or a
    jr nz,.left
    set 1,c
    jr .straight
.left:
    set 0,c
.straight:
    ld de,(auto_dot)
    bit 7,d
    jr nz,.slow
    ld hl,(auto_cross)
    add hl,hl
    add hl,hl
    or a
    sbc hl,de
    jr c,.bend_ok
.slow:
    ld a,(speed)
    cp 96
    jr c,.bend_ok
    res 2,c
    set 3,c
.bend_ok:
    ld a,(lap)
    cp 2
    jr c,.no_boost
    ld a,(section)
    cp 24
    jr nc,.no_boost
    ld a,(energy)
    cp 55
    jr c,.no_boost
    set 4,c
.no_boost:
    ld a,c
    ld (control_keys),a
    xor a
    ld (control_pressed),a
    ret

start_spin:
    ld a,(control_pressed)
    and 32
    ret z
    ld a,(spin_cooldown)
    or a
    ret nz
    ld a,SPIN_DURATION
    ld (spin_frames),a
    ld a,48
    ld (spin_cooldown),a
    ret

drive_player:
    xor a
    ld (boosting),a
    ld a,(spin_frames)
    or a
    jp nz,move_player
    ld a,(heading)
    ld b,a
    ld a,(control_keys)
    ld c,a
    bit 0,c
    jr z,.not_left
    dec b
    ld a,(demo_mode)
    or a
    jr nz,.not_left
    dec b
.not_left:
    bit 1,c
    jr z,.not_right
    inc b
    ld a,(demo_mode)
    or a
    jr nz,.not_right
    inc b
.not_right:
    ld a,b
    and 63
    ld (heading),a
    ld b,SPEED_NORMAL
    bit 3,c
    jr nz,.no_boost
    ld a,(lap)
    cp 2
    jr c,.no_boost
    bit 4,c
    jr z,.no_boost
    ld a,(energy)
    cp 13
    jr c,.no_boost
    dec a
    ld (energy),a
    ld a,1
    ld (boosting),a
    ld b,SPEED_BOOST
    set 2,c
.no_boost:
    ld a,(speed)
    bit 3,c
    jr nz,.brake
    bit 2,c
    jr z,.coast
    add a,ACCELERATION
    jr c,.maximum_speed
    cp b
    jr c,.speed_set
.maximum_speed:
    ld a,b
    jr .speed_set
.brake:
    sub BRAKING
    jr nc,.speed_set
    xor a
    jr .speed_set
.coast:
    sub 3
    jr nc,.speed_set
    xor a
.speed_set:
    ld (speed),a
    ld a,(heading)
    call get_direction
    ld a,e
    ld (motion_sin),a
    ld a,(speed)
    ld e,a
    call mul_signed
    call shift_hl_5
    ld de,(velocity_x)
    call ease_velocity
    ld (velocity_x),hl
    ld a,(motion_sin)
    ld d,a
    ld a,(speed)
    ld e,a
    call mul_signed
    call shift_hl_5
    ld de,(velocity_y)
    call ease_velocity
    ld (velocity_y),hl
move_player:
    ld hl,(velocity_x)
    ld de,(player_x)
    add hl,de
    ld (candidate_x),hl
    ld hl,(velocity_y)
    ld de,(player_y)
    add hl,de
    ld (candidate_y),hl
    ; Endpoint and midpoint checks prevent stepping across a thin corner.
    call segment_on_road
    jp z,border_collision
    ld hl,(candidate_x)
    ld (player_x),hl
    ld hl,(candidate_y)
    ld (player_y),hl
    ret
segment_on_road:
    call candidate_on_road
    ret z
    ld hl,(candidate_x)
    ld de,(player_x)
    add hl,de
    srl h
    rr l
    ld a,h
    ld (sample_x),a
    ld hl,(candidate_y)
    ld de,(player_y)
    add hl,de
    srl h
    rr l
    ld a,h
    ld (sample_y),a
    jp sample_road
border_collision:
    ; Keep any valid tangent motion before reflecting the blocked component.
    xor a
    ld (blocked_axes),a
    ld hl,(candidate_y)
    push hl
    ld hl,(player_y)
    ld (candidate_y),hl
    call segment_on_road
    jr nz,.slide_x
    ld a,1
    ld (blocked_axes),a
    jr .no_x
.slide_x:
    ld hl,(candidate_x)
    ld (player_x),hl
.no_x:
    pop hl
    ld (candidate_y),hl
    ld hl,(player_x)
    ld (candidate_x),hl
    call segment_on_road
    jr nz,.slide_y
    ld a,(blocked_axes)
    or 2
    ld (blocked_axes),a
    jr .no_y
.slide_y:
    ld hl,(candidate_y)
    ld (player_y),hl
.no_y:
    jp border_bounce
; target HL, current DE -> current+(target-current)/2, with visible inertia.
ease_velocity:
    or a
    sbc hl,de
    ld b,1
    ld a,(rebound_frames)
    or a
    jr z,.ease
    ld b,4                     ; let the collision impulse survive the throttle
.ease:
    sra h
    rr l
    djnz .ease
    add hl,de
    ret
candidate_on_road:
    ld a,(candidate_x+1)
    ld (sample_x),a
    ld a,(candidate_y+1)
    ld (sample_y),a
sample_road:
    ld a,(sample_x)
    bit 7,a
    jr nz,.outside
    ld b,a
    ld a,(sample_y)
    bit 7,a
    jr nz,.outside
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ld a,b
    rrca
    rrca
    rrca
    and 15
    ld e,a
    ld d,0
    add hl,de
    ld de,road_map
    add hl,de
    ld a,b
    and 7
    ld e,a
    ld d,0
    push hl
    ld hl,texture_masks
    add hl,de
    ld a,(hl)
    pop hl
    and (hl)
    ret
.outside:
    xor a
    ret
border_bounce:
    call road_normal
    call reflect_velocity
    ld a,(spin_frames)
    or a
    ret nz
    ld a,(speed)
    ld b,a
    srl a
    srl a
    ld c,a
    ld a,b
    sub c
    ld (speed),a
    ld a,4
    jp hurt_player

    INCLUDE "collisions.asm"

; Q0.7 inward normal: preserve tangent velocity, reflect an incoming component.
reflect_velocity:
    ld a,REBOUND_FRAMES
    ld (rebound_frames),a
    ld hl,(velocity_x)
    call shift_hl_3
    ld d,l
    ld a,(bounce_nx)
    ld e,a
    call mul_both_signed
    ld (dot_temp),hl
    ld hl,(velocity_y)
    call shift_hl_3
    ld d,l
    ld a,(bounce_ny)
    ld e,a
    call mul_both_signed
    ld de,(dot_temp)
    add hl,de
    call shift_hl_7
    ld a,l
    ld (bounce_projection),a
    or a
    jp p,.minimum
    ld d,a
    ld a,(bounce_nx)
    ld e,a
    call mul_both_signed
    call shift_hl_3
    ex de,hl
    ld hl,(velocity_x)
    or a
    sbc hl,de
    ld (velocity_x),hl
    ld a,(bounce_projection)
    ld d,a
    ld a,(bounce_ny)
    ld e,a
    call mul_both_signed
    call shift_hl_3
    ex de,hl
    ld hl,(velocity_y)
    or a
    sbc hl,de
    ld (velocity_y),hl
    ld a,(bounce_projection)
    neg
.minimum:
    ; Prevent stationary contacts and pixel-sized corners from holding a ship.
    cp 16
    ret nc
    ld a,(bounce_nx)
    call normal_bias
    ld hl,(velocity_x)
    add hl,de
    ld (velocity_x),hl
    ld a,(bounce_ny)
    call normal_bias
    ld hl,(velocity_y)
    add hl,de
    ld (velocity_y),hl
    ret
normal_bias:                   ; signed normal byte -> small Q8.8 inward impulse
    ld e,a
    rla
    sbc a,a
    ld d,a
    ret
hurt_player:
    ld b,a
    ld a,(hurt_frames)
    or a
    ret nz
    ld a,(energy)
    sub b
    jr nc,.set
    xor a
.set:
    ld (energy),a
    ld a,8
    ld (hurt_frames),a
    ret

update_section:
    ld a,(section)
    ld (old_section),a
    sub 4
    and 127
    ld (search_node),a
    ld a,255
    ld (best_distance),a
    ld a,9
    ld (search_left),a
.search:
    ld a,(search_node)
    call node_pointer
    ld a,(player_x+1)
    sub (hl)
    jp p,.positive_x
    neg
.positive_x:
    ld b,a
    inc hl
    ld a,(player_y+1)
    sub (hl)
    jp p,.positive_y
    neg
.positive_y:
    add a,b
    ld b,a
    ld a,(best_distance)
    cp b
    jr c,.skip
    jr z,.skip
    ld a,b
    ld (best_distance),a
    ld a,(search_node)
    ld (section),a
.skip:
    ld a,(search_node)
    inc a
    and 127
    ld (search_node),a
    ld hl,search_left
    dec (hl)
    jr nz,.search
    ret
update_laps:
    ld a,(section)
    cp 44
    jr c,.not_recharge
    cp 52
    jr nc,.not_recharge
    ld a,(energy)
    add a,2
    cp 101
    jr c,.recharged
    ld a,100
.recharged:
    ld (energy),a
.not_recharge:
    ld a,(section)
    and 0x60
    rlca
    rlca
    rlca
    ld b,a
    ld a,(checkpoint)
    inc a
    cp b
    jr nz,.not_gate
    ld (checkpoint),a
.not_gate:
    ld a,(old_section)
    cp 120
    ret c
    ld a,(section)
    cp 8
    ret nc
    ld a,(player_started)
    or a
    jr nz,.complete_lap
    inc a
    ld (player_started),a
    ret
.complete_lap:
    ld a,(checkpoint)
    cp 3
    ret nz
    xor a
    ld (checkpoint),a
    ld hl,lap
    inc (hl)
    ld a,(hl)
    cp 4
    ret c
    ld hl,finish_order
    inc (hl)
    ld a,(hl)
    ld (player_finish),a
    ld a,3
    ld (phase),a
    ret

; Rival: progress(2), lap, energy, hit, stun, x/y(2+2), speed, push x/y(2+2), started.
update_rivals:
    ld ix,rival1_progress
    call drive_rival
    ld ix,rival2_progress
drive_rival:
    ld a,(ix+3)
    or a
    ret z
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+1)
    cp 44
    jr c,.target
    cp 52
    jr nc,.target
    ld a,(ix+3)
    add a,2
    cp 49
    jr c,.recharge
    ld a,48
.recharge:
    ld (ix+3),a
.target:
    call rival_target
    call accelerate_rival
    ; Convert world speed to progress using this circuit's mean node length.
    ld e,(ix+10)
    ld a,(rival_step_scale)
    ld d,a
    call mul_unsigned
    ld c,h
    ld a,(rival_step_scale+1)
    ld d,a
    call mul_unsigned
    ld b,0
    add hl,bc
    ld b,h
    ld c,l
    jp rival_tick
rival_target:
    ld a,(ix+1)
    call node_pointer
    inc hl
    inc hl
    ld b,(hl)
    ld a,(ix+1)
    add a,3
    call node_pointer
    inc hl
    inc hl
    ld a,(hl)
    sub b
    add a,32
    and 63
    sub 32
    jp p,.turn_positive
    neg
.turn_positive:
    ld (rival_turn),a
    ld b,RIVAL_SPEED_A
    push ix
    pop hl
    ld a,l
    cp LOW rival1_progress
    jr z,.curve
    ld b,RIVAL_SPEED_B
.curve:
    ld a,(rival_turn)
    cp 3
    jr c,.boost
    ld b,RIVAL_CORNER_SPEED
    cp 6
    ret c
    ld b,RIVAL_SHARP_SPEED
    ret
.boost:
    cp 2
    ret nc
    ld a,(ix+2)
    cp 2
    ret c
    ld a,(frame_counter)
    and 63
    cp 16
    ret nc
    ld a,(ix+3)
    cp 17
    ret c
    ld a,(frame_counter)
    and 1
    jr nz,.boost_speed
    dec (ix+3)
.boost_speed:
    ld b,RIVAL_BOOST_A
    push ix
    pop hl
    ld a,l
    cp LOW rival1_progress
    ret z
    ld b,RIVAL_BOOST_B
    ret
accelerate_rival:
    ld a,(ix+10)
    add a,8
    jr c,.maximum
    cp b
    jr c,.set
.maximum:
    ld a,b
.set:
    ld (ix+10),a
    ld c,a
    ld b,0
    ret
rival_tick:
    ld a,(ix+3)
    or a
    ret z
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+5)
    or a
    jr z,.full_speed
    srl b
    rr c
    srl b
    rr c
.full_speed:
    ld l,(ix+0)
    ld h,(ix+1)
    add hl,bc
    bit 7,h
    jr z,.no_lap
    res 7,h
    ld a,(ix+15)
    or a
    jr nz,.lap_complete
    ld (ix+15),1
    jr .no_lap
.lap_complete:
    inc (ix+2)
.no_lap:
    ld (ix+0),l
    ld (ix+1),h
place_rival:
    ld l,(ix+0)
    ld h,(ix+1)
    ld a,h
    ld (rival_node),a
    ld a,l
    ld (rival_fraction),a
    ld a,h
    call node_pointer
    ld a,(hl)
    ld (rival_base_x),a
    inc hl
    ld a,(hl)
    ld (rival_base_y),a
    inc hl
    ld a,(hl)
    ld (rival_heading),a
    ld a,(rival_node)
    inc a
    call node_pointer
    ld a,(rival_base_x)
    ld b,a
    ld a,(hl)
    sub b
    ld d,a
    ld a,(rival_fraction)
    ld e,a
    push hl
    call mul_signed
    ld a,(rival_base_x)
    ld d,a
    ld e,0
    add hl,de
    ld (ix+6),l
    ld (ix+7),h
    pop hl
    inc hl
    ld a,(rival_base_y)
    ld b,a
    ld a,(hl)
    sub b
    ld d,a
    ld a,(rival_fraction)
    ld e,a
    call mul_signed
    ld a,(rival_base_y)
    ld d,a
    ld e,0
    add hl,de
    ld (ix+8),l
    ld (ix+9),h
    ld l,(ix+11)
    ld h,(ix+12)
    call damp_push
    ld (ix+11),l
    ld (ix+12),h
    ld e,(ix+6)
    ld d,(ix+7)
    add hl,de
    ld (ix+6),l
    ld (ix+7),h
    ld l,(ix+13)
    ld h,(ix+14)
    call damp_push
    ld (ix+13),l
    ld (ix+14),h
    ld e,(ix+8)
    ld d,(ix+9)
    add hl,de
    ld (ix+8),l
    ld (ix+9),h
    ; Opposite lanes, about 1.5 units from the centreline.
    ld a,(rival_heading)
    call get_direction
    ld a,e
    neg
    ld d,a
    ld e,3
    call mul_signed
    call rival_lane_sign
    ld e,(ix+6)
    ld d,(ix+7)
    add hl,de
    ld (ix+6),l
    ld (ix+7),h
    ld a,(rival_heading)
    call get_direction
    ld e,3
    call mul_signed
    call rival_lane_sign
    ld e,(ix+8)
    ld d,(ix+9)
    add hl,de
    ld (ix+8),l
    ld (ix+9),h
    ld a,(ix+2)
    cp 4
    ret c
    call rival_finish_pointer
    ld a,(hl)
    or a
    ret nz
    push hl
    ld hl,finish_order
    inc (hl)
    ld a,(hl)
    pop hl
    ld (hl),a
    ret
rival_finish_pointer:
    push ix
    pop hl
    ld a,l
    cp LOW rival1_progress
    ld hl,rival1_finish
    ret z
    ld hl,rival2_finish
    ret
rival_lane_sign:
    push ix
    pop de
    ld a,e
    cp LOW rival1_progress
    ret z
    jp neg_hl
damp_push:
    ld e,l
    ld d,h
    call shift_hl_3
    ex de,hl
    or a
    sbc hl,de
    ret

ship_contacts:
    ld ix,rival1_progress
    call contact_rival
    ld ix,rival2_progress
contact_rival:
    ld a,(ix+2)
    cp 4
    ret nc
    ld a,(ix+3)
    or a
    ret z
    ld a,(ix+4)
    or a
    ret nz
    ld a,(player_x+1)
    sub (ix+7)
    jp p,.positive_x
    neg
.positive_x:
    cp 3
    ret nc
    ld b,a
    ld a,(player_y+1)
    sub (ix+9)
    jp p,.positive_y
    neg
.positive_y:
    cp 3
    ret nc
    add a,b
    cp 4
    ret nc
    ld (ix+4),16
    ld (ix+5),12
    call contact_normal
    call reflect_velocity
    call knock_rival
    ld a,(spin_frames)
    or a
    ld b,16
    jr nz,.damage
    ld a,3
    call hurt_player
    ld b,4
.damage:
    ld a,(ix+3)
    sub b
    jr nc,.set
    xor a
.set:
    ld (ix+3),a
    ret

; Push immediately away from contact, then let the AI recover its line smoothly.
knock_rival:
    ld l,(ix+6)
    ld h,(ix+7)
    ld de,(player_x)
    or a
    sbc hl,de
    ld (push_dx),hl
    ld l,(ix+8)
    ld h,(ix+9)
    ld de,(player_y)
    or a
    sbc hl,de
    ld (push_dy),hl
    ld de,(push_dx)
    ld a,d
    or e
    or h
    or l
    jr z,.coincident
    call kick_component
    ld (push_dy),hl
    ld hl,(push_dx)
    call kick_component
    ld (push_dx),hl
    jr .apply
.coincident:
    ld a,(ix+1)
    call node_pointer
    inc hl
    inc hl
    ld a,(hl)
    ld (rival_heading),a
    call get_direction
    ld a,e
    neg
    ld d,a
    ld e,4
    call mul_signed
    call rival_lane_sign
    ld (push_dx),hl
    ld a,(rival_heading)
    call get_direction
    ld e,4
    call mul_signed
    call rival_lane_sign
    ld (push_dy),hl
.apply:
    ld hl,(push_dx)
    ld (ix+11),l
    ld (ix+12),h
    ld e,(ix+6)
    ld d,(ix+7)
    add hl,de
    ld (ix+6),l
    ld (ix+7),h
    ld hl,(push_dy)
    ld (ix+13),l
    ld (ix+14),h
    ld e,(ix+8)
    ld d,(ix+9)
    add hl,de
    ld (ix+8),l
    ld (ix+9),h
    ret
kick_component:
    ld a,h
    or l
    ret z
    bit 7,h
    ld hl,512
    ret z
    ld hl,-512
    ret
update_rank:
    ld a,1
    ld (rank),a
    ld ix,rival1_progress
    call rank_rival
    ld ix,rival2_progress
rank_rival:
    ld a,(ix+3)
    or a
    ret z
    call rival_finish_pointer
    ld a,(hl)
    or a
    jr z,.running
    ld b,a
    ld a,(player_finish)
    or a
    jr z,.ahead
    cp b
    jr c,.behind
    jr z,.behind
    jr .ahead
.behind:
    ret
.running:
    ld a,(player_started)
    cp (ix+15)
    jr c,.ahead
    ret nz
    ld a,(lap)
    cp (ix+2)
    jr c,.ahead
    ret nz
    ld a,(section)
    cp (ix+1)
    ret nc
.ahead:
    ld hl,rank
    inc (hl)
    ret
