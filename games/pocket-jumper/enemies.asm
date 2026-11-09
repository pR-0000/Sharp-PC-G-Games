; FR/EN: patrolling enemies, stomps and contact damage.
enemies_step:
    ld a,(frame_count)
    and 1
    ret nz
    ld ix,enemies
    ld b,4
enemy_move_next:
    push bc
    ld a,(ix+8)
    or a
    jr z,enemy_move_done
    ld l,(ix+0)
    ld h,(ix+1)
    ld a,(ix+7)
    cp 1
    jr nz,enemy_left
    inc hl
    ld e,(ix+5)
    ld d,(ix+6)
    or a
    sbc hl,de
    jr nc,enemy_reverse
    add hl,de
    jr enemy_probe
enemy_left:
    dec hl
    ld e,(ix+3)
    ld d,(ix+4)
    or a
    sbc hl,de
    jr c,enemy_reverse
    add hl,de
enemy_probe:
    ld (enemy_candidate),hl
    ld a,(ix+7)
    cp 1
    jr nz,enemy_front
    ld de,ENEMY_W-1
    add hl,de
enemy_front:
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld b,l
    ld a,(ix+2)
    add a,8
    srl a
    srl a
    srl a
    ld c,a
    call tile_at
    call is_solid
    jr nc,enemy_reverse
    ld hl,(enemy_candidate)
    ld (ix+0),l
    ld (ix+1),h
    jr enemy_move_done
enemy_reverse:
    ld a,(ix+7)
    neg
    ld (ix+7),a
enemy_move_done:
    ld de,9
    add ix,de
    pop bc
    djnz enemy_move_next
    ret
enemy_contact:
    ld hl,(player_x)
    call fixed_to_int
    ld (candidate_x),hl
    ld hl,(player_y)
    call fixed_to_int
    ld a,l
    ld (candidate_y),a
    ld ix,enemies
    ld b,4
enemy_contact_next:
    push bc
    ld a,(ix+8)
    or a
    jr z,enemy_contact_skip
    ld hl,(candidate_x)
    ld de,HERO_W-1
    add hl,de
    ld e,(ix+0)
    ld d,(ix+1)
    or a
    sbc hl,de
    jr c,enemy_contact_skip
    ex de,hl
    ld de,ENEMY_W-1
    add hl,de
    ld de,(candidate_x)
    or a
    sbc hl,de
    jr c,enemy_contact_skip
    ld a,(candidate_y)
    add a,HERO_H-1
    cp (ix+2)
    jr c,enemy_contact_skip
    ld a,(ix+2)
    add a,7
    ld c,a
    ld a,(candidate_y)
    cp c
    jr z,enemy_vertical_hit
    jr nc,enemy_contact_skip
enemy_vertical_hit:
    ld a,(velocity_y)
    bit 7,a
    jr nz,enemy_hurt
    ld a,(ix+2)
    add a,3
    ld c,a
    ld a,(previous_y)
    add a,HERO_H
    cp c
    jr nc,enemy_hurt
    ld (ix+8),0
    ld a,-36
    ld (velocity_y),a
    ld hl,100
    call add_score
    jr enemy_contact_skip
enemy_hurt:
    ld a,(grace)
    or a
    jr nz,enemy_contact_skip
    pop bc
    jp lose_life
enemy_contact_skip:
    ld de,9
    add ix,de
    pop bc
    djnz enemy_contact_next
    ret
