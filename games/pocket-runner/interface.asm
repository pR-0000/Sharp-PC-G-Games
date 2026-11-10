; FR/EN: bilingual labels, native ROM digits / chiffres natifs ROM.
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
    IF TARGET_G850
    call pcg_puts
    ld de,0x500
    ld hl,photo_help
    ENDIF
    jp pcg_puts
    IF TARGET_G850
photo_help:
    IF BUILD_LANG_EN
    db "F: PHOTO FREEZE",0
    ELSE
    db "F: FIGER POUR PHOTO",0
    ENDIF
    ENDIF
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
    IF TARGET_G850
    INCLUDE "targets/g850/hud.asm"
    ELSE
hud:
    ld hl,(score)
    ld de,0x14
    call decimal4
    ld a,(exit_active)
    or a
    jr z,hud_gold
    ld hl,exit_text
    ld de,0x114
    call pcg_puts
    jr hud_lives
hud_gold:
    ld hl,patterns+25
    ld de,0x114
    call pcg_glyph
    inc e
    ld a,(gold_left)
    add a,48
    call pcg_putc
hud_lives:
    ld hl,patterns+50
    ld de,0x214
    call pcg_glyph
    inc e
    ld a,(lives)
    add a,48
    call pcg_putc
    ld de,0x314
    IF BUILD_LANG_EN
    ld a,'L'
    ELSE
    ld a,'N'
    ENDIF
    call pcg_putc
    inc e
    ld a,32
    call pcg_putc
    inc e
    ld a,'0'
    call pcg_putc
    inc e
    ld a,(level_index)
    add a,49
    jp pcg_putc
    ENDIF
; HL 0..9999 -> four ROM digits at DE.
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
title_text: db 'POCKET RUNNER',0
    IF BUILD_LANG_EN
subtitle: db 'GOLD, LADDERS AND TRAPS',0
start_text: db 'ENTER:PLAY  M:HELP',0
title_help: db 'Z/X:DIG  P:PAUSE Q:QUIT',0
help_1: db 'ARROWS: WALK AND CLIMB',0
help_2: db 'Z/X: DIG LEFT / RIGHT',0
help_3: db 'ALL GOLD -> EXIT LADDER',0
help_4: db 'P:PAUSE R:RETRY Q:QUIT',0
pause_text: db 'PAUSED - P TO RESUME',0
over_text: db 'GAME OVER',0
win_text: db 'THREE VAULTS CLEARED!',0
restart_text: db 'ENTER:RESTART Q:QUIT',0
exit_text: db 'EXIT',0
    ELSE
subtitle: db 'OR, ECHELLES ET PIEGES',0
start_text: db 'ENTER:JOUER  M:AIDE',0
title_help: db 'Z/X:CREUSE P:PAUSE Q:FIN',0
help_1: db 'FLECHES: MARCHER/GRIMPER',0
help_2: db 'Z/X:CREUSER GAUCHE/DROIT',0
help_3: db 'TOUT L OR -> ECHELLE FIN',0
help_4: db 'P:PAUSE R:REESSAI Q:FIN',0
pause_text: db 'PAUSE - P POUR REPRENDRE',0
over_text: db 'PARTIE TERMINEE',0
win_text: db 'LES TROIS COFFRES VIDES!',0
restart_text: db 'ENTER:REJOUER Q:FIN',0
exit_text: db 'SORT',0
    ENDIF
