; Signed Q12.4 positions, Q4.4 velocities and one-way platform collision.
fighter_step:
    ld a,(ix+FSTOCK)
    or a
    ret z
    ld a,(ix+FCOOL)
    or a
    jr z,.timer_FCOOL
    dec (ix+FCOOL)
.timer_FCOOL:
    ld a,(ix+FSTUN)
    or a
    jr z,.timer_FSTUN
    dec (ix+FSTUN)
.timer_FSTUN:
    ld a,(ix+FINVUL)
    or a
    jr z,.timer_FINVUL
    dec (ix+FINVUL)
.timer_FINVUL:
    ld a,(ix+FSPECIAL)
    or a
    jr z,.timer_FSPECIAL
    dec (ix+FSPECIAL)
.timer_FSPECIAL:
    ld a,(ix+FDROP)
    or a
    jr z,.timer_FDROP
    dec (ix+FDROP)
.timer_FDROP:
    ld a,(ix+FATTACK)
    or a
    jr z,.timer_FATTACK
    dec (ix+FATTACK)
.timer_FATTACK:
    call end_dash
    ld a,(ix+FLAST)
    cpl
    and (ix+FBUTTON)
    ld (pressed_buttons),a
    ld a,(ix+FBUTTON)
    ld (ix+FLAST),a
    ld (ix+FGUARD),0
    ld a,(ix+FSTUN)
    or a
    jr nz,.motion
    call horizontal_input
    call guard_input
    ld a,(pressed_buttons)
    and BJUMP
    call nz,jump_input
    ld a,(ix+FGUARD)
    or a
    jr nz,.motion
    call attack_input
.motion:
    ld a,(ix+FVX)
    call velocity_word
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    add hl,de
    ld (ix+FX),l
    ld (ix+FX+1),h
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    ld de,16
    add hl,de
    ld (old_feet),hl
    ld a,(ix+FVY)
    add a,5
    cp 85
    jr c,.gravity
    bit 7,a
    jr nz,.gravity
    ld a,80
.gravity:
    ld (ix+FVY),a
    call velocity_word
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    add hl,de
    ld (ix+FY),l
    ld (ix+FY+1),h
    ld (ix+FGROUND),0
    call land_on_platform
    call check_ringout
    ret

horizontal_input:
    ld a,(ix+FBUTTON)
    and BLEFT|BRIGHT
    cp BLEFT
    jr z,.left
    cp BRIGHT
    jr z,.right
    ld a,(ix+FVX)
    or a
    ret z
    bit 7,a
    jr nz,.drag_left
    dec a
    ld (ix+FVX),a
    ret
.drag_left:
    inc a
    ld (ix+FVX),a
    ret
.left:
    ld (ix+FFACE),1
    ld e,(ix+FCHAR)
    ld d,0
    ld hl,speeds
    add hl,de
    ld a,(hl)
    neg
    ld b,a
    ld a,(ix+FVX)
    bit 7,a
    jr z,.left_accel
    cp b
    ret c
    ret z
.left_accel:
    sub 6
    ld (ix+FVX),a
    ret
.right:
    ld (ix+FFACE),0
    ld e,(ix+FCHAR)
    ld d,0
    ld hl,speeds
    add hl,de
    ld b,(hl)
    ld a,(ix+FVX)
    bit 7,a
    jr nz,.right_accel
    cp b
    ret nc
.right_accel:
    add a,6
    ld (ix+FVX),a
    ret

guard_input:
    ld a,(ix+FBUTTON)
    and BDOWN
    jr z,.recover
    ld a,(ix+FGROUND)
    or a
    jr z,.fall
    ld a,(ix+FATTACK)
    or a
    ret nz
    ld a,(ix+FENERGY)
    or a
    jr z,.broken
    dec (ix+FENERGY)
    ld (ix+FGUARD),1
    ld (ix+FVX),0
    ret
.broken:
    ld (ix+FSTUN),18
    ret
.fall:
    ld a,(ix+FVY)
    bit 7,a
    ret nz
    cp 64
    ret nc
    ld (ix+FVY),64
    ret
.recover:
    ld a,(frame_count)
    and 1
    ret nz
    ld a,(ix+FENERGY)
    cp 48
    ret nc
    inc (ix+FENERGY)
    ret
jump_input:
    ld a,(ix+FGROUND)
    or a
    jr z,.jump
    ld a,(ix+FBUTTON)
    and BDOWN
    jr z,.jump
    ld (ix+FDROP),4
    ld (ix+FVY),16
    ld (ix+FGROUND),0
    ld (ix+FGUARD),0
    ld (ix+FJUMPS),1
    ret
.jump:
    ld a,(ix+FJUMPS)
    or a
    ret z
    dec (ix+FJUMPS)
    ld e,(ix+FCHAR)
    ld d,0
    ld hl,jumps
    add hl,de
    ld a,(hl)
    neg
    ld (ix+FVY),a
    ld (ix+FGROUND),0
    ld (ix+FGUARD),0
    ret

land_on_platform:
    ld a,(ix+FVY)
    bit 7,a
    ret nz
    ld a,(ix+FDROP)
    or a
    ret nz
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    ld de,16
    add hl,de
    ld (next_feet),hl
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    call fixed_to_int
    ld (fighter_left),hl
    ld hl,platforms
    ld b,4
.loop:
    push bc
    push hl
    ld c,(hl)
    inc hl
    ld b,(hl)
    inc hl
    ld e,(hl)
    ld d,0
    ld hl,(old_feet)
    or a
    sbc hl,de
    jr z,.cross
    jr nc,.next
.cross:
    ld hl,(next_feet)
    or a
    sbc hl,de
    jr c,.next
    ld hl,(fighter_left)
    ld a,h
    or a
    jr nz,.next
    ld a,l
    cp b
    jr nc,.next
    add a,16
    cp c
    jr c,.next
    jr z,.next
    ld h,0
    ld l,e
    ld de,16
    or a
    sbc hl,de
    call int_to_fixed
    ld (ix+FY),l
    ld (ix+FY+1),h
    ld (ix+FVY),0
    ld (ix+FGROUND),1
    ld (ix+FJUMPS),2
    ld (ix+FAIR),0
    pop hl
    pop bc
    ret
.next:
    pop hl
    inc hl
    inc hl
    inc hl
    pop bc
    djnz .loop
    ret
check_ringout:
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    call fixed_to_int
    ld de,24
    add hl,de
    ld de,288
    or a
    sbc hl,de
    jr nc,.ko
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    ld de,48
    add hl,de
    ld de,176
    or a
    sbc hl,de
    ret c
.ko:
    dec (ix+FSTOCK)
    ld e,(iy+FCHAR)
    ld d,0
    ld hl,knockouts
    add hl,de
    inc (hl)
    ld a,(ix+FSTOCK)
    or a
    ret z
    ld a,(actor_index)
    call respawn_actor
    ld (ix+FINVUL),40
    ret

; Nova's dash is a burst, not permanent maximum launch velocity.
end_dash:
    ld a,(ix+FCHAR)
    or a
    ret nz
    ld a,(ix+FTYPE)
    cp 1
    ret nz
    ld a,(ix+FATTACK)
    cp 7
    ret nz
    ld a,(ix+FSTUN)
    or a
    ret nz
    ld a,(ix+FVX)
    bit 7,a
    ld a,36
    jr z,.store
    neg
.store:
    ld (ix+FVX),a
    ret
