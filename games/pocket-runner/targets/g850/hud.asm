; FR/EN: native digits and small icons above the 140x40 playing field.
hud:
    ld hl,frame_buffer
    ld de,0
    ld b,144
    call pcg_pattern
    ld hl,(score)
    ld de,0
    call decimal4
    ld hl,patterns+10*7
    ld de,6
    ld b,7
    call pcg_pattern
    ld a,(lives)
    add a,'0'
    ld de,8
    call pcg_putc
    ld a,(exit_active)
    or a
    jr z,.gold
    ld hl,exit_text
    ld de,11
    call pcg_puts
    jr .level
.gold:
    ld hl,patterns+5*7
    ld de,11
    ld b,7
    call pcg_pattern
    ld de,13
    ld a,(gold_left)
    add a,'0'
    call pcg_putc
.level:
    ld de,18
    IF BUILD_LANG_EN
    ld a,'L'
    ELSE
    ld a,'N'
    ENDIF
    call pcg_putc
    inc e
    ld a,(level_index)
    add a,'1'
    jp pcg_putc
