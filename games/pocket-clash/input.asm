; Simultaneous direction, jump and attacks. Preserve the caller's IFF1.
sample_controls:
    ld a,i
    push af
    di
    xor a
    out (PCG_PORT_KEYS_HIGH),a
    out (PCG_PORT_KEYS_LOW),a
    ld a,4
    call matrix_row
    and 3
    add a,a
    add a,a
    add a,a
    ld c,a                    ; Z=attack, X=special
    ld a,8
    call matrix_row
    ld b,a
    and $A0                  ; SPACE or UP
    jr z,.down
    set 2,c
.down:
    bit 6,b
    jr z,.arrows
    set 5,c
.arrows:
    ld a,16
    call matrix_row
    and 3
    or c
    ld c,a
    xor a
    out (PCG_PORT_KEYS_LOW),a
    out (PCG_PORT_KEYS_HIGH),a
    pop af
    jp po,.restored
    ei
.restored:
    ld (ix+FBUTTON),c
    ret
matrix_row:
    out (PCG_PORT_KEYS_LOW),a
    ld b,12
.wait:
    djnz .wait
    in a,(PCG_PORT_KEYS)
    ret

; IX=actor IY=target. AI has the same buttons and cooldowns as the player.
ai_controls:
    xor a
    ld (ai_buttons),a
    ld l,(iy+FX)
    ld h,(iy+FX+1)
    call fixed_to_int
    push hl
    ld l,(ix+FX)
    ld h,(ix+FX+1)
    call fixed_to_int
    ld (fighter_left),hl
    pop de
    ex de,hl
    or a
    sbc hl,de
    ld (ai_dx),hl
    ld l,(ix+FY)
    ld h,(ix+FY+1)
    call fixed_to_int
    ld (ai_y),hl
    ; Off the main deck: steer toward its centre and recover, not the foe.
    ld hl,(fighter_left)
    ld a,h
    or a
    jr nz,.left_edge
    ld a,l
    cp 52
    jr c,.left_edge
    cp 156
    jr nc,.right_edge
    jr .pursue
.left_edge:
    ld a,BRIGHT
    ld (ai_buttons),a
    jr .recover
.right_edge:
    ld a,BLEFT
    ld (ai_buttons),a
.recover:
    ld a,(ix+FGROUND)
    or a
    jr nz,.pursue
    ld a,(ai_y)
    cp 55
    jr c,.fight
    ld a,(ix+FVY)
    bit 7,a
    jr nz,.fight
    ld a,(frame_count)
    and 7
    jr nz,.fight
    ld a,(ix+FJUMPS)
    or a
    ld a,BJUMP
    jr nz,.recover_button
    ld a,(ix+FAIR)
    or a
    jr nz,.fight
    ld a,BSPECIAL
.recover_button:
    ld b,a
    ld a,(ai_buttons)
    or b
    ld (ai_buttons),a
    jr .fight
.pursue:
    ld hl,(ai_dx)
    ld a,h
    rlca
    and 1
    ld (ix+FFACE),a
    ld hl,(ai_dx)
    bit 7,h
    jr z,.right
    xor a
    sub l
    ld l,a
    ld a,BLEFT
    jr .distance
.right:
    ld a,BRIGHT
.distance:
    ld b,a
    ld a,l
    cp 19
    jr c,.vertical
    ld a,b
    ld (ai_buttons),a
.vertical:
    ld l,(iy+FY)
    ld h,(iy+FY+1)
    call fixed_to_int
    ld de,(ai_y)
    or a
    sbc hl,de
    bit 7,h
    jr z,.fight
    ld a,l
    cp 248
    jr nc,.fight
    ld a,(frame_count)
    and 15
    jr nz,.fight
    ld a,(ai_buttons)
    or BJUMP
    ld (ai_buttons),a
.fight:
    ld hl,(ai_dx)
    bit 7,h
    jr z,.close
    xor a
    sub l
    ld l,a
.close:
    ld a,l
    cp 29
    jr nc,.special
    ld a,(frame_count)
    and 15
    jr nz,.guard
    ld a,(ai_buttons)
    or BATTACK
    ld (ai_buttons),a
.guard:
    ld a,(iy+FATTACK)
    or a
    jr z,.special
    ld a,(round_index)
    or a
    jr z,.special
    ld a,(frame_count)
    and 3
    jr z,.special
    ld a,(ai_buttons)
    or BDOWN
    ld (ai_buttons),a
.special:
    ld a,(frame_count)
    and 63
    cp 24
    jr nz,.finish
    ld a,(ai_buttons)
    or BSPECIAL
    ld (ai_buttons),a
.finish:
    ld a,(ai_buttons)
    ld (ix+FBUTTON),a
    ret
