; FR/EN: ROM characters for all text and numbers / texte et chiffres ROM.
title:
    call pcg_clear
    ld de,0
    ld hl,title_text
    call pcg_puts
    ld de,0x100
    ld hl,engine_text
    call pcg_puts
    ld de,0x200
    ld hl,goal_text
    call pcg_puts
    ld de,0x300
    ld hl,start_text
    jp pcg_puts
help_screen:
    call pcg_clear
    ld de,0
    ld hl,help_1
    call pcg_puts
    ld de,0x100
    ld hl,help_2
    call pcg_puts
    ld de,0x200
    ld hl,help_3
    call pcg_puts
    ld de,0x300
    ld hl,help_4
    jp pcg_puts
message:
    push hl
    call pcg_clear
    pop hl
    ld de,0x100
    jp pcg_puts
result_screen:
    ld a,(phase)
    cp 4
    ld hl,defeat_text
    jr nz,result_message
    ld hl,win_text
result_message:
    call message
    ld de,0x300
    ld hl,restart_text
    jp pcg_puts
hud:
    ; Black graphics replaced by opaque, readable native HUD characters.
    ld de,0x300
    ld hl,heart_icon
    call pcg_glyph
    inc e
    ld a,(health)
    call decimal3
    ld de,0x304
    ld a,32
    call pcg_putc
    ld a,(angle)
    add a,32
    rlca
    rlca
    and 3
    ld e,a
    ld d,0
    IF BUILD_LANG_EN
    ld hl,compass_en
    ELSE
    ld hl,compass_fr
    ENDIF
    add hl,de
    ld a,(hl)
    ld de,0x305
    call pcg_putc
    ld de,0x312
    ld a,(key_owned)
    or a
    ld a,32
    jr z,hud_key_empty
    ld hl,key_icon
    call pcg_glyph
    jr hud_ammo
hud_key_empty:
    call pcg_putc
hud_ammo:
    ld de,0x314
    ld hl,ammo_icon
    call pcg_glyph
    inc e
    ld a,(ammo)
    jp decimal3
decimal3:
    ld b,48
decimal_hundreds:
    cp 100
    jr c,decimal_hundreds_done
    sub 100
    inc b
    jr decimal_hundreds
decimal_hundreds_done:
    push af
    ld a,b
    call pcg_putc
    inc e
    pop af
    ld b,48
decimal_tens:
    cp 10
    jr c,decimal_tens_done
    sub 10
    inc b
    jr decimal_tens
decimal_tens_done:
    push af
    ld a,b
    call pcg_putc
    inc e
    pop af
    add a,48
    jp pcg_putc
hurt_flash:
    ld b,2
hurt_loop:
    ld de,0x300
    ld a,32
    call pcg_putc
    call flash_delay
    ld hl,heart_icon
    call pcg_glyph
    call flash_delay
    djnz hurt_loop
    ret
flash_delay:
    push bc
    ld bc,10000
flash_delay_loop:
    dec bc
    ld a,b
    or c
    jr nz,flash_delay_loop
    pop bc
    ret
title_text: db 'POCKET DEPTHS 2',0
engine_text: db 'DDA 3D / 32 DIRECTIONS',0
    IF BUILD_LANG_EN
goal_text: db 'FIND KEY, REACH EXIT',0
start_text: db 'ENTER:PLAY  Q:QUIT',0
help_1: db 'ARROWS: WALK / TURN',0
help_2: db ', ;: STRAFE  SPACE:FIRE',0
help_3: db 'E:DOOR M:HELP P:PAUSE',0
help_4: db 'KEY -> EXIT  Q:QUIT',0
pause_text: db 'PAUSED - PRESS A KEY',0
win_text: db 'ESCAPED! WELL DONE.',0
defeat_text: db 'YOU FELL IN THE DEPTHS.',0
restart_text: db 'ENTER:RESTART  Q:QUIT',0
    ELSE
goal_text: db 'TROUVEZ CLE ET SORTIE',0
start_text: db 'ENTER:JOUER  Q:QUITTER',0
help_1: db 'FLECHES: AVANCE / TOURNE',0
help_2: db ', ;: PAS COTE ESPACE:TIR',0
help_3: db 'E:PORTE M:AIDE P:PAUSE',0
help_4: db 'CLE -> SORTIE Q:QUITTER',0
pause_text: db 'PAUSE - APPUYER TOUCHE',0
win_text: db 'SORTIE! BIEN JOUE.',0
defeat_text: db 'PERDU DANS LES ABIMES.',0
restart_text: db 'ENTER:REJOUER Q:QUITTER',0
    ENDIF
