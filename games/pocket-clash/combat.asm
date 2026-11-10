; Attacks, shields and percentage-dependent launch speed.
attack_input:
    ld a,(ix+FATTACK)
    or a
    ret nz
    ld a,(pressed_buttons)
    and BSPECIAL
    jr nz,.special
    ld a,(ix+FCOOL)
    or a
    ret nz
    ld a,(pressed_buttons)
    and BATTACK
    ret z
    ld (ix+FATTACK),12
    ld (ix+FCOOL),18
    ld (ix+FTYPE),0
    ld (ix+FHIT),0
    ret
.special:
    ld a,(ix+FSPECIAL)
    or a
    ret nz
    ld a,(ix+FGROUND)
    or a
    jr nz,.launch
    ld a,(ix+FAIR)
    or a
    ret nz
    ld (ix+FAIR),1
    ld (ix+FVY),-80
.launch:
    ld (ix+FSPECIAL),50
    ld (ix+FCOOL),22
    ld (ix+FATTACK),18
    ld (ix+FTYPE),1
    ld (ix+FHIT),0
    ld a,(ix+FCHAR)
    cp 1
    jr z,.orb
    cp 2
    jr z,.heavy
    cp 3
    jr z,.acrobat
    ld a,96
    ld (ix+FINVUL),6
    jr .dash
.heavy:
    ld a,(ix+FGROUND)
    or a
    ret nz
    ld (ix+FVY),-80
    ret
.acrobat:
    ld (ix+FVY),-88
    ld a,48
.dash:
    ld b,a
    ld a,(ix+FFACE)
    or a
    ld a,b
    jr z,.velocity
    neg
.velocity:
    ld (ix+FVX),a
    ret
.orb:
    ld (ix+FTYPE),2
    jp spawn_orb

melee_hit:
    ld a,(ix+FSTOCK)
    or a
    ret z
    ld a,(ix+FHIT)
    or a
    ret nz
    ld a,(ix+FTYPE)
    cp 2
    ret z
    ld b,10
    or a
    jr z,.window
    ld b,16
.window:
    ld a,(ix+FATTACK)
    cp b
    ret nc
    cp 5
    ret c
    ld a,(iy+FINVUL)
    or a
    ret nz
    ld l,(iy+FY)
    ld h,(iy+FY+1)
    call fixed_to_int
    push hl
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    pop de
    or a
    sbc hl,de
    bit 7,h
    jr z,.height
    xor a
    sub l
    ld l,a
.height:
    ld a,l
    cp 18
    ret nc
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    call fixed_to_int
    push hl
    ld l,(iy+FX)
    ld h,(iy+FX+1)
    call fixed_to_int
    pop de
    or a
    sbc hl,de
    ld a,(ix+FFACE)
    ld (hit_direction),a
    bit 7,h
    jr z,.right
    or a
    ret z
    xor a
    sub l
    ld l,a
    jr .range
.right:
    or a
    ret nz
.range:
    push hl
    ld e,(ix+FCHAR)
    ld d,0
    ld hl,attack_reach
    add hl,de
    ld b,(hl)
    ld a,(ix+FTYPE)
    ld (hit_special),a
    or a
    jr z,.normal_range
    ld a,b
    add a,8
    ld b,a
.normal_range:
    pop hl
    ld a,l
    cp b
    ret nc
    ld hl,attack_damage
    add hl,de
    ld a,(hl)
    ld b,a
    ld a,(ix+FTYPE)
    or a
    ld a,b
    jr z,.damage
    add a,4
.damage:
    ld (hit_damage),a
    ld (ix+FHIT),1
    jp apply_hit

; IX=attacker, IY=victim, shared damage/direction. Shields consume stamina.
apply_hit:
    ld a,(iy+FINVUL)
    or a
    ret nz
    ld a,(iy+FSTOCK)
    or a
    ret z
    ld a,(iy+FGUARD)
    or a
    jr z,.hurt
    ld a,(iy+FENERGY)
    sub 8
    jr c,.break
    ld (iy+FENERGY),a
    ld (iy+FSTUN),2
    ld a,12
    jp .push
.break:
    ld (iy+FENERGY),0
    ld (iy+FGUARD),0
    ld (iy+FSTUN),18
.hurt:
    ld a,(hit_damage)
    ld c,a
    ld e,(ix+FCHAR)
    ld d,0
    ld hl,damage_scores
    add hl,de
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld b,0
    add hl,bc
    ex de,hl
    ld (hl),d
    dec hl
    ld (hl),e
    ld a,(hit_damage)
    add a,(iy+FDAMAGE)
    cp 200
    jr c,.percent
    ld a,199
.percent:
    ld (iy+FDAMAGE),a
    ld b,a
    srl a
    srl a
    srl a
    srl a
    srl a
    add a,8
    ld c,a
    ld a,(iy+FSTUN)
    cp c
    jr nc,.stun
    ld a,c
.stun:
    ld (iy+FSTUN),a
    ld (iy+FINVUL),10
    ld (iy+FATTACK),0
    ld (iy+FGUARD),0
    ld a,b
    srl a
    srl a
    add a,32
    neg
    ld (iy+FVY),a
    ld a,b
    srl a
    add a,32
    ld b,a
    ld a,(iy+FCHAR)
    cp 2
    jr nz,.light
    ld a,b
    sub 12
    ld b,a
.light:
    cp 3
    jr nz,.force
    ld a,b
    add a,8
    ld b,a
.force:
    ld a,(hit_special)
    or a
    ld a,b
    jr z,.limit
    add a,12
.limit:
    cp 113
    jr c,.push
    ld a,112
.push:
    ld b,a
    ld a,(hit_direction)
    or a
    ld a,b
    jr z,.velocity
    neg
.velocity:
    ld (iy+FVX),a
    ld a,2
    ld (hit_pause),a
    ld a,7
    ld (impact_time),a
    ld l,(iy+FX)
    ld h,(iy+FX+1)
    ld (impact_x),hl
    ld l,(iy+FY)
    ld h,(iy+FY+1)
    ld (impact_y),hl
    ret

spawn_orb:
    ld a,(actor_index)
    call orb_address
    push hl
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    ld de,8*16
    add hl,de
    ex de,hl
    pop hl
    ld (hl),e
    inc hl
    ld (hl),d
    inc hl
    push hl
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    ld de,4*16
    add hl,de
    ex de,hl
    pop hl
    ld (hl),e
    inc hl
    ld (hl),d
    inc hl
    ld a,(ix+FFACE)
    or a
    ld a,64
    jr z,.direction
    neg
.direction:
    ld (hl),a
    inc hl
    ld (hl),40
    ret
orb_address:
    ld hl,orbs
    or a
    ret z
    ld hl,orbs+6
    ret
update_orbs:
    xor a
    ld (orb_index),a
.loop:
    ld a,(orb_index)
    call setup_pair
    call orb_address
    ld (orb_pointer),hl
    ld de,5
    add hl,de
    ld a,(hl)
    or a
    jp z,.next
    dec (hl)
    dec hl
    ld a,(hl)
    call velocity_word
    ld hl,(orb_pointer)
    ld c,(hl)
    inc hl
    ld b,(hl)
    ex de,hl
    add hl,bc
    ex de,hl
    ld (hl),d
    dec hl
    ld (hl),e
    ld l,e
    ld h,d
    call fixed_to_int
    push hl
    ld l,(iy+FX)
    ld h,(iy+FX+1)
    call fixed_to_int
    pop de
    or a
    sbc hl,de
    bit 7,h
    jr z,.dx
    xor a
    sub l
    ld l,a
.dx:
    ld a,l
    cp 15
    jr nc,.next
    ld hl,(orb_pointer)
    inc hl
    inc hl
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    call fixed_to_int
    push hl
    ld l,(iy+FY)
    ld h,(iy+FY+1)
    call fixed_to_int
    pop de
    or a
    sbc hl,de
    bit 7,h
    jr z,.dy
    xor a
    sub l
    ld l,a
.dy:
    ld a,l
    cp 15
    jr nc,.next
    ld hl,(orb_pointer)
    ld de,4
    add hl,de
    ld a,(hl)
    rlca
    and 1
    ld (hit_direction),a
    xor a
    ld (hit_special),a
    ld a,12
    ld (hit_damage),a
    call apply_hit
    ld hl,(orb_pointer)
    ld de,5
    add hl,de
    ld (hl),0
.next:
    ld hl,orb_index
    inc (hl)
    ld a,(hl)
    cp 2
    jp c,.loop
    ret
