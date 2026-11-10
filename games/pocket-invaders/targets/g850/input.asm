; FR/EN: settled raw matrix for arrow/A-D plus SPACE/ENTER together.
invaders_controls:
    push af
    push bc
    ld a,i
    push af
    di
    xor a
    out (PCG_PORT_KEYS_HIGH),a
    out (PCG_PORT_KEYS_LOW),a
    ld a,2
    call invaders_matrix_row
    ld c,0
    bit 0,a
    jr z,.right
    set 0,c
.right:
    bit 2,a
    jr z,.space
    set 1,c
.space:
    ld a,8
    call invaders_matrix_row
    bit 5,a
    jr z,.arrows
    set 2,c
.arrows:
    ld a,16
    call invaders_matrix_row
    bit 7,a
    jr z,.merge
    set 2,c
.merge:
    and 3
    or c
    ld (input_buttons),a
    xor a
    out (PCG_PORT_KEYS_LOW),a
    out (PCG_PORT_KEYS_HIGH),a
    pop af
    jp po,.restore
    ei
.restore:
    pop bc
    pop af
    ret
invaders_matrix_row:
    out (PCG_PORT_KEYS_LOW),a
    ld b,12
.settle:
    djnz .settle
    in a,(PCG_PORT_KEYS)
    ret
