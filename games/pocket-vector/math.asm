; Original Z80 fixed-point helpers. D signed, E unsigned -> HL signed product.
mul_signed:
    bit 7,d
    jp z,mul_unsigned
    ld a,d
    neg
    ld d,a
    call mul_unsigned
neg_hl:
    xor a
    sub l
    ld l,a
    sbc a,a
    sub h
    ld h,a
    ret
mul_unsigned:
    ld a,d
    ld d,0
    ld hl,0
    ld b,8
.loop:
    add hl,hl
    sla a
    jr nc,.skip
    add hl,de
.skip:
    djnz .loop
    ret
; D signed, E signed -> HL signed product.
mul_both_signed:
    bit 7,e
    jp z,mul_signed
    ld a,e
    neg
    ld e,a
    ld a,d
    neg
    ld d,a
    jp mul_signed
shift_hl_3:
    ld b,3
    jr shift_hl
shift_hl_5:
    ld b,5
    jr shift_hl
shift_hl_7:
    ld b,7
shift_hl:
    sra h
    rr l
    djnz shift_hl
    ret
; Unsigned HL / C (1..255), quotient HL. Remainder A, BC/DE destroyed.
divide_hl_c:
    xor a
    ld b,16
.loop:
    add hl,hl
    rla
    cp c
    jr c,.skip
    sub c
    inc l
.skip:
    djnz .loop
    ret
; A node 0..127 -> HL record [x,y,heading,pad].
node_pointer:
    and 127
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    ld de,path_nodes
    add hl,de
    ret
; A heading 0..63 -> D=cos, E=sin, signed Q0.7.
get_direction:
    and 63
    add a,a
    ld l,a
    ld h,0
    ld de,direction_table
    add hl,de
    ld d,(hl)
    inc hl
    ld e,(hl)
    ret
