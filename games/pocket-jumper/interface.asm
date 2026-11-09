; FR/EN: bilingual interface, native digits in the right-hand HUD.
title_screen:
    call pcg_clear
    ld de,0
    ld hl,title_text
    call pcg_puts
    ld de,0x100
    ld hl,subtitle
    call pcg_puts
    ld de,0x200
    ld hl,start_text
    call pcg_puts
    ld de,0x300
    ld hl,title_help
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
    call message
    ld de,0x200
    ld hl,restart_text
    call pcg_puts
    ld hl,(score)
    ld de,0x314
    jp decimal4
hud:
    ld hl,(score)
    ld de,0x14
    call decimal4
    ld hl,coin_icon
    ld de,0x114
    call pcg_glyph
    inc e
    ld a,(coins)
    ld l,a
    ld h,0
    ld bc,10
    call decimal_place
    ld a,l
    add a,48
    call pcg_putc
    ld hl,heart_icon
    ld de,0x214
    call pcg_glyph
    inc e
    ld a,(lives)
    add a,48
    call pcg_putc
    ld hl,stage_text
    ld de,0x314
    jp pcg_puts
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
title_text: db 'POCKET JUMPER',0
    IF BUILD_LANG_EN
subtitle: db 'PIXEL PLATFORM ADVENTURE',0
start_text: db 'ENTER:PLAY M:HELP',0
title_help: db 'SPACE:JUMP  Z/X:< >',0
help_1: db 'HOLD LEFT/RIGHT + SPACE',0
help_2: db 'UP:JUMP  Z/X:LEFT/RIGHT',0
help_3: db 'COINS, BLOCKS AND STOMPS',0
help_4: db 'P:PAUSE R:RESTART Q:QUIT',0
pause_text: db 'PAUSED - P TO RESUME',0
over_text: db 'GAME OVER',0
win_text: db 'FLAG REACHED!',0
restart_text: db 'ENTER:RESTART Q:QUIT',0
stage_text: db 'L 01',0
    ELSE
subtitle: db 'AVENTURE DE PLATEFORMES',0
start_text: db 'ENTER:JOUER M:AIDE',0
title_help: db 'ESPACE:SAUT  Z/X:< >',0
help_1: db 'FLECHES + ESPACE: SAUT',0
help_2: db 'HAUT:SAUT Z/X:GAU/DROITE',0
help_3: db 'PIECES, BLOCS ET ENNEMIS',0
help_4: db 'P:PAUSE R:REJOUER Q:FIN',0
pause_text: db 'PAUSE - P POUR REPRENDRE',0
over_text: db 'PARTIE TERMINEE',0
win_text: db 'DRAPEAU ATTEINT !',0
restart_text: db 'ENTER:REJOUER Q:FIN',0
stage_text: db 'N 01',0
    ENDIF
