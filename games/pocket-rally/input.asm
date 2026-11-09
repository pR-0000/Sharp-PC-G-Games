; FR/EN: simultaneous steering, throttle and brake; preserve IFF1.
sample_controls:
    ld a,i
    push af
    di
    xor a
    out (PCG801_PORT_KEYS_HIGH),a
    out (PCG801_PORT_KEYS_LOW),a
    ld c,0
    ld a,4
    call matrix_row
    and 1
    jr z,input_gas
    set 3,c
input_gas:
    ld a,8
    call matrix_row
    bit 6,a
    jr z,input_throttle
    set 3,c
input_throttle:
    and 0xa0
    jr z,input_turn
    set 2,c
input_turn:
    ld a,16
    call matrix_row
    and 3
    or c
    ld (buttons),a
    xor a
    out (PCG801_PORT_KEYS_LOW),a
    out (PCG801_PORT_KEYS_HIGH),a
    pop af
    ret po
    ei
    ret
matrix_row:
    out (PCG801_PORT_KEYS_LOW),a
    ld b,10
matrix_wait:
    djnz matrix_wait
    in a,(PCG801_PORT_KEYS)
    ret
