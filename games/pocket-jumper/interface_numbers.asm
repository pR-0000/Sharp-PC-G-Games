decimal4:
    ld bc,1000
    call decimal_place
    ld bc,100
    call decimal_place
    ld bc,10
    call decimal_place
    ld a,l
    add a,48
    jp pcg_putc
decimal_place:
    ld a,47
decimal_subtract:
    inc a
    or a
    sbc hl,bc
    jr nc,decimal_subtract
    add hl,bc
    call pcg_putc
    inc e
    ret
