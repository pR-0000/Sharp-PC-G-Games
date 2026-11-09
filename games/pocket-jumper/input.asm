; FR : lecture simultanee direction + saut ; sorties matrice remises a zero.
; EN: simultaneous movement/jump state; leave both matrix strobes cleared.
; Matrix layout: g800 io.c / depend.c, MACHINE_E200 (G801/G805).
; https://ver0.sakura.ne.jp/pc/g800src.0.11.4.tgz
; Port 10h active-high: row 2 Z/X, row 3 SPACE/UP, row 4 LEFT/RIGHT.
; Preserve the caller's interrupt state across the short matrix scan.
JUMP_LEFT   EQU 1
JUMP_RIGHT  EQU 2
JUMP_BUTTON EQU 4
sample_controls:
    push bc
    push de
    push hl
    ld a,i
    push af
    di
    xor a
    out (PCG801_PORT_KEYS_HIGH),a
    out (PCG801_PORT_KEYS_LOW),a
    ld a,4
    call matrix_row
    and 3
    ld (keys_zx),a
    ld c,0
    bit 0,a
    jr z,controls_x
    ld c,JUMP_LEFT | JUMP_BUTTON
controls_x:
    bit 1,a
    jr z,controls_space
    ld a,c
    or JUMP_RIGHT | JUMP_BUTTON
    ld c,a
controls_space:
    ld a,8
    call matrix_row
    and 0xa0                 ; SPACE bit 5, UP bit 7
    jr z,controls_arrows
    set 2,c
controls_arrows:
    ld a,16
    call matrix_row
    and 3
    or c
    ld c,a
    xor a
    out (PCG801_PORT_KEYS_LOW),a
    out (PCG801_PORT_KEYS_HIGH),a
    pop af
    jp po,controls_interrupt_restored
    ei
controls_interrupt_restored:
    ld a,(last_buttons)
    cpl
    and c
    and JUMP_BUTTON
    ld a,c
    ld (input_buttons),a
    ld (last_buttons),a
    jr z,controls_done
    ld a,(keys_zx)
    cp 1
    jr nz,controls_launch_right
    ld a,-32
    ld (velocity_x),a
    jr controls_jump
controls_launch_right:
    cp 2
    jr nz,controls_jump
    ld a,32
    ld (velocity_x),a
controls_jump:
    call request_jump
controls_done:
    pop hl
    pop de
    pop bc
    ret
matrix_row:
    out (PCG801_PORT_KEYS_LOW),a
    ld b,10                  ; allow old strobe to decay (>26 T on E200)
matrix_settle:
    djnz matrix_settle
    in a,(PCG801_PORT_KEYS)
    ret
