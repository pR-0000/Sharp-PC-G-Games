; Full-width playfield, single-row native HUD and six-row menus.
title_screen:
    call pcg_clear
    ld de,0x0005
    ld hl,title_text
    call pcg_puts
    ld de,0x0100
    ld hl,subtitle
    call pcg_puts
    ld de,0x0200
    ld hl,start_text
    call pcg_puts
    ld de,0x0300
    ld hl,demo_text
    call pcg_puts
    ld de,0x0400
    ld hl,photo_text
    call pcg_puts
    ld de,0x0500
    ld hl,title_help
    jp pcg_puts
help_screen:
    call pcg_clear
    ld de,0
    ld hl,help_1
    call pcg_puts
    inc d
    ld hl,help_2
    call pcg_puts
    inc d
    ld hl,help_3
    call pcg_puts
    inc d
    ld hl,help_4
    call pcg_puts
    inc d
    ld hl,photo_text
    call pcg_puts
    inc d
    ld hl,demo_text
    jp pcg_puts
message:
    push hl
    call pcg_clear
    pop hl
    ld de,0x0200
    jp pcg_puts
result_screen:
    call message
    ld hl,(score)
    ld de,0x030A
    call decimal4
    ld de,0x0500
    ld hl,restart_text
    jp pcg_puts
hud:
    ld hl,(score)
    ld de,0
    call decimal4
    ld hl,heart_icon
    ld de,6
    call pcg_glyph
    inc e
    ld a,(lives)
    add a,'0'
    call pcg_putc
    ld hl,coin_icon
    ld de,10
    call pcg_glyph
    inc e
    ld a,(coins)
    ld l,a
    ld h,0
    ld bc,10
    call decimal_place
    ld a,l
    add a,'0'
    call pcg_putc
    ld hl,stage_text
    ld de,16
    call pcg_puts
    ld a,(demo_mode)
    or a
    ld a,' '
    jr z,.indicator
    ld a,'D'
.indicator:
    ld de,23
    jp pcg_putc
    INCLUDE "../../interface_numbers.asm"
title_text: db 'POCKET JUMPER',0
    IF BUILD_LANG_EN
subtitle: db 'CLOUD ROAD - PC-G850',0
start_text: db 'ENTER:PLAY  M:HELP',0
title_help: db 'ARROWS + SPACE:JUMP',0
demo_text: db 'D:DEMO / MANUAL',0
photo_text: db 'F:PHOTO FREEZE / RESUME',0
help_1: db 'HOLD LEFT/RIGHT + SPACE',0
help_2: db 'UP:JUMP  Z/X:LEFT/RIGHT',0
help_3: db 'COINS, BLOCKS AND STOMPS',0
help_4: db 'P:PAUSE R:RESTART Q:QUIT',0
pause_text: db 'PAUSED - P TO RESUME',0
over_text: db 'GAME OVER',0
win_text: db 'FLAG REACHED!',0
restart_text: db 'ENTER:RESTART Q:QUIT',0
stage_text: db 'L01',0
    ELSE
subtitle: db 'ROUTE DES NUAGES - G850',0
start_text: db 'ENTER:JOUER  M:AIDE',0
title_help: db 'FLECHES + ESPACE:SAUT',0
demo_text: db 'D:DEMO / MANUEL',0
photo_text: db 'F:PHOTO FIGER/REPRENDRE',0
help_1: db 'FLECHES + ESPACE: SAUT',0
help_2: db 'HAUT:SAUT Z/X:GAU/DROITE',0
help_3: db 'PIECES, BLOCS ET ENNEMIS',0
help_4: db 'P:PAUSE R:REJOUER Q:FIN',0
pause_text: db 'PAUSE - P POUR REPRENDRE',0
over_text: db 'PARTIE TERMINEE',0
win_text: db 'DRAPEAU ATTEINT !',0
restart_text: db 'ENTER:REJOUER Q:FIN',0
stage_text: db 'N01',0
    ENDIF
