; Raw multi-key matrix, G850 >=130 T settling. No IRQ mode/mask changes.
; Keys: left/right/up/down/space/X/P/Q -> bits 0..7.
; Aux: ENTER/D/R/F/M -> bits 0..4. ON/BREAK also exits.
poll_keyboard:
    IF !TARGET_G850
    ld a,i
    push af
    di
    ENDIF
    ld a,(keys)
    ld (previous_keys),a
    ld a,(aux_keys)
    ld (previous_aux),a
    xor a
    ld (keys),a
    ld (aux_keys),a
    out (PCG_PORT_KEYS_HIGH),a
    call key_settle
    ld a,8
    call read_key_group
    ld b,a
    ld c,0
    bit 7,b
    jr z,.no_up
    set 2,c
.no_up:
    bit 6,b
    jr z,.no_down
    set 3,c
.no_down:
    bit 5,b
    jr z,.no_space
    set 4,c
.no_space:
    ld a,c
    ld (keys),a
    ld a,16
    call read_key_group
    ld b,a
    and 3
    ld c,a
    ld a,(keys)
    or c
    ld (keys),a
    bit 7,b
    jr z,.no_enter
    ld a,1
    ld (aux_keys),a
.no_enter:
    ld a,4
    call read_key_group
    ld b,a
    and 2
    rlca
    rlca
    rlca
    rlca
    ld c,a
    ld a,(keys)
    or c
    ld (keys),a
    bit 6,b
    jr z,.no_help
    ld a,(aux_keys)
    or 16
    ld (aux_keys),a
.no_help:
    ld a,2
    call read_key_group
    ld b,a
    and 4
    rrca
    ld c,a
    ld a,(aux_keys)
    or c
    ld (aux_keys),a
    bit 3,b
    jr z,.no_photo
    ld a,(aux_keys)
    or 8
    ld (aux_keys),a
.no_photo:
    ld a,1
    call read_key_group
    ld b,a
    and 2
    rrca
    rrca
    ld c,a
    ld a,(keys)
    or c
    ld (keys),a
    bit 4,b
    jr z,.no_restart
    ld a,(aux_keys)
    or 4
    ld (aux_keys),a
.no_restart:
    ld a,128
    call read_key_group
    bit 0,a
    jr z,.no_pause
    ld a,(keys)
    or 64
    ld (keys),a
.no_pause:
    in a,(0x1F)
    and 128
    ld c,a
    ld a,(keys)
    or c
    ld (keys),a
    ld c,a
    ld a,(previous_keys)
    cpl
    and c
    ld (pressed),a
    ld a,(aux_keys)
    ld c,a
    ld a,(previous_aux)
    cpl
    and c
    ld (aux_pressed),a
    xor a
    out (PCG_PORT_KEYS_LOW),a
    IF !TARGET_G850
    out (PCG_PORT_KEYS_HIGH),a
    pop af
    jp po,.interrupts_restored
    ei
.interrupts_restored:
    ENDIF
    ret
read_key_group:
    out (PCG_PORT_KEYS_LOW),a
    call key_settle
    in a,(PCG_PORT_KEYS)
    ret
key_settle:
    ; CALL+RET+11 DJNZ iterations exceed 150 T even without I/O wait states.
    push bc
    ld b,12
.wait:
    djnz .wait
    pop bc
    ret

; Static screens poll at roughly 7 ms intervals at 8 MHz. Three released
; samples re-arm ENTER; a held key or a brief contact bounce cannot skip
; the next result/menu. Racing and presentation retain their normal cadence.
menu_poll_delay:
    call static_screen
    ret nz
    ld bc,2048
.wait:
    dec bc
    ld a,b
    or c
    jr nz,.wait
    ret
static_screen:
    ld a,(phase)
    or a
    ret z
    cp 3
    ret z
    cp 4
    ret z
    cp 6
    ret
block_screen_enter:
    xor a
    ld (confirm_release),a
    ret
filter_screen_enter:
    call static_screen
    ret nz
    ld a,(aux_keys)
    bit 0,a
    ld a,(confirm_release)
    jr z,.released
    cp 3
    ret nc
    call block_screen_enter
    ld hl,aux_pressed
    res 0,(hl)
    ret
.released:
    cp 3
    ret nc
    inc a
    ld (confirm_release),a
    ret
