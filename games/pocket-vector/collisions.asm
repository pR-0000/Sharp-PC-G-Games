; FR/EN: local road-mask normals, ship contact normals and eight-direction units.
road_normal:
    ld bc,0x0200
    call road_neighbour
    ld (bounce_nx),a
    ld bc,0xFE00
    call road_neighbour
    ld b,a
    ld a,(bounce_nx)
    sub b
    ld (bounce_nx),a
    ld bc,2
    call road_neighbour
    ld (bounce_ny),a
    ld bc,254
    call road_neighbour
    ld b,a
    ld a,(bounce_ny)
    sub b
    ld (bounce_ny),a
    ld b,a
    ld a,(bounce_nx)
    or b
    jp nz,normalise_signs
    ; If the edge is beyond the probe radius, use the axes actually blocked.
    ld hl,(velocity_x)
    call word_sign
    neg
    ld (bounce_nx),a
    ld hl,(velocity_y)
    call word_sign
    neg
    ld (bounce_ny),a
    ld a,(blocked_axes)
    cp 1
    jr z,.x_only
    cp 2
    jp nz,normalise_signs
    xor a
    ld (bounce_nx),a
    jp normalise_signs
.x_only:
    xor a
    ld (bounce_ny),a
    jp normalise_signs
road_neighbour:                ; B/C signed x/y offsets, preserve BC, A=road 0/1
    push bc
    ld a,(player_x+1)
    add a,b
    ld (sample_x),a
    ld a,(player_y+1)
    add a,c
    ld (sample_y),a
    call sample_road
    pop bc
    ret z
    ld a,1
    ret

contact_normal:
    ld e,(ix+6)
    ld d,(ix+7)
    ld hl,(player_x)
    or a
    sbc hl,de
    call word_sign
    ld (bounce_nx),a
    call shift_hl_3
    ld a,l
    call absolute_a
    ld (bounce_ax),a
    ld e,(ix+8)
    ld d,(ix+9)
    ld hl,(player_y)
    or a
    sbc hl,de
    call word_sign
    ld (bounce_ny),a
    call shift_hl_3
    ld a,l
    call absolute_a
    ld (bounce_ay),a
    ld b,a
    ld a,(bounce_ax)
    or b
    jr z,.coincident
    ld a,b
    add a,a
    ld b,a
    ld a,(bounce_ax)
    cp b
    jr c,.test_y
    xor a
    ld (bounce_ny),a
    jp normalise_signs
.test_y:
    add a,a
    ld b,a
    ld a,(bounce_ay)
    cp b
    jr c,normalise_signs
    xor a
    ld (bounce_nx),a
    jp normalise_signs
.coincident:
    ld hl,(velocity_x)
    call word_sign
    neg
    ld (bounce_nx),a
    ld hl,(velocity_y)
    call word_sign
    neg
    ld (bounce_ny),a
normalise_signs:
    ld a,(bounce_nx)
    ld b,a
    ld a,(bounce_ny)
    or b
    jr nz,.nonzero
    inc a
    ld (bounce_nx),a
.nonzero:
    ld b,127
    ld a,(bounce_nx)
    or a
    jr z,.scale
    ld a,(bounce_ny)
    or a
    jr z,.scale
    ld b,90                    ; 127 / sqrt(2), avoiding an energetic corner kick
.scale:
    ld a,(bounce_nx)
    call scale_sign
    ld (bounce_nx),a
    ld a,(bounce_ny)
    call scale_sign
    ld (bounce_ny),a
    ret
scale_sign:
    or a
    ret z
    ld a,b
    ret p
    neg
    ret
word_sign:
    ld a,h
    or l
    ret z
    bit 7,h
    ld a,1
    ret z
    ld a,-1
    ret
absolute_a:
    or a
    ret p
    neg
    ret
