; FR/EN: native Sharp digits, no tiny custom numeric font.
title_screen:
    call pcg_clear
    ld de,0
    ld hl,title_text
    call pcg_puts
    ld a,(track_index)
    or a
    ld hl,track_name_0
    jr z,title_track
    ld hl,track_name_1
title_track:
    ld de,0x100
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
    call pcg_clear
    ld de,0
    ld hl,finish_text
    call pcg_puts
    ld de,0x100
    ld hl,position_text
    call pcg_puts
    ld de,0x10a
    call place_digits
    ld de,0x200
    ld hl,time_text
    call pcg_puts
    ld de,0x214
    ld hl,(race_ticks)
    call decimal4
    ld de,0x300
    ld hl,restart_text
    jp pcg_puts
hud:
    ld de,0x14
    IF BUILD_LANG_EN
    ld a,'L'
    ELSE
    ld a,'T'
    ENDIF
    call pcg_putc
    inc e
    ld a,(cars+7)
    inc a
    cp 4
    jr c,hud_lap
    ld a,3
hud_lap:
    add a,48
    call pcg_putc
    inc e
    call slash_three
    ld de,0x114
    IF BUILD_LANG_EN
    ld a,'S'
    ELSE
    ld a,'V'
    ENDIF
    ld b,a
    ld a,(auto_throttle)
    or a
    ld a,b
    jr z,hud_speed_label
    ld a,'A'
hud_speed_label:
    call pcg_putc
    inc e
    ld a,(cars+5)
    add a,a
    ld l,a
    add a,a
    add a,a
    add a,l
    ld l,a
    ld h,0
    ld bc,100
    call decimal_place
    ld bc,10
    call decimal_place
    ld a,l
    add a,48
    call pcg_putc
    ld de,0x214
    ld a,'P'
    call pcg_putc
    inc e
    call place_digits
    ld de,0x314
    ld hl,(race_ticks)
    jp decimal4
place_digits:
    ld a,(race_rank)
    add a,48
    call pcg_putc
    inc e
slash_three:
    ld a,'/'
    call pcg_putc
    inc e
    ld a,'3'
    jp pcg_putc
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
title_text: db 'POCKET RALLY',0
    IF BUILD_LANG_EN
track_name_0: db 'COAST LOOP',0
track_name_1: db 'HARBOUR CHICANE',0
start_text: db 'ENTER:RACE N:TRACK',0
title_help: db 'M:HELP Q:QUIT',0
help_1: db 'LEFT/RIGHT:STEER',0
help_2: db 'UP/SPACE:GAS DOWN:BRAKE',0
help_3: db 'F:AUTO P:PAUSE R:RETRY',0
help_4: db '3 LAPS N:TRACK Q:QUIT',0
pause_text: db 'PAUSED - P TO RESUME',0
finish_text: db 'FINISH!',0
position_text: db 'POSITION',0
time_text: db 'TIME (GAME UNITS)',0
restart_text: db 'ENTER:RESTART Q:QUIT',0
    ELSE
track_name_0: db 'BOUCLE COTIERE',0
track_name_1: db 'CHICANE DU PORT',0
start_text: db 'ENTER:COURSE N:CIRCUIT',0
title_help: db 'M:AIDE Q:FIN',0
help_1: db 'GAUCHE/DROITE:TOURNER',0
help_2: db 'HAUT/ESP:GAZ BAS:FREIN',0
help_3: db 'F:AUTO P:PAUSE R:DEPART',0
help_4: db '3 TOURS N:PISTE Q:FIN',0
pause_text: db 'PAUSE - P POUR REPRENDRE',0
finish_text: db 'ARRIVEE !',0
position_text: db 'POSITION',0
time_text: db 'TEMPS (UNITES DE JEU)',0
restart_text: db 'ENTER:REJOUER Q:FIN',0
    ENDIF
