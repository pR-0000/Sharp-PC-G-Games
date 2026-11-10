; FR/EN interface; numeric HUD characters come from the Sharp ROM font.
title_screen:
    call pcg_clear
    ld hl,title_text
    ld de,$0005
    call pcg_puts
    ld hl,mission_text
    ld de,$0100
    call pcg_puts
    ld hl,start_text
    ld de,$0200
    call pcg_puts
    ld hl,quit_text
    ld de,HUD_ROW*256
    jp pcg_puts

help_screen:
    call pcg_clear
    ld hl,help_1
    ld de,0
    call pcg_puts
    ld hl,help_2
    ld de,$0100
    call pcg_puts
    ld hl,help_3
    ld de,$0200
    call pcg_puts
    ld hl,help_4
    ld de,HUD_ROW*256
    call pcg_puts
    ld a,(key_owned)
    add a,'0'
    ld de,$0305
    call pcg_putc
    ld a,(switches)
    ld b,a
    and 1
    bit 1,b
    jr z,.beacons
    inc a
.beacons:
    add a,'0'
    ld de,$0309
    jp pcg_putc

result_screen:
    call pcg_clear
    ld a,(phase)
    cp 4
    ld hl,defeat_text
    jr nz,.title
    ld hl,victory_text
    ld a,(deck)
    cp 3
    jr c,.title
    ld hl,campaign_text
.title:
    ld de,$0104
    call pcg_puts
    ld hl,restart_text
    ld de,$0200
    call pcg_puts
    ld hl,quit_text
    ld de,HUD_ROW*256
    jp pcg_puts

draw_hud:
    ld hl,status_labels
    ld de,HUD_ROW*256+6
    call pcg_puts
    ld a,'B'
    ld de,HUD_ROW*256+17
    call pcg_putc
    ld a,(guarding)
    or a
    ld a,' '
    jr z,.guard_icon
    ld a,'X'
.guard_icon:
    ld de,HUD_ROW*256+16
    call pcg_putc
    ld a,(deck)
    add a,'0'
    ld de,HUD_ROW*256+7
    call pcg_putc
    ld a,(key_owned)
    add a,'0'
    ld de,HUD_ROW*256+9
    call pcg_putc
    ld a,(switches)
    ld b,a
    and 1
    bit 1,b
    jr z,.count
    inc a
.count:
    add a,'0'
    ld de,HUD_ROW*256+18
    call pcg_putc
    ld a,(direction)
    ld c,a
    ld b,0
    ld hl,compass_text
    add hl,bc
    ld a,(hl)
    ld de,HUD_ROW*256+5
    call pcg_putc
    ; Clear only the HUD corners, keeping the centre perspective/weapon.
    ld a,' '
    ld de,HUD_ROW*256
    ld b,4
    call hud_spaces
    ld de,HUD_ROW*256+20
    ld b,4
    call hud_spaces
    ld hl,heart_glyph
    ld de,HUD_ROW*256
    call pcg_glyph
    inc e
    ld a,(health)
    call number_three
    ld hl,bullet_glyph
    ld de,HUD_ROW*256+20
    call pcg_glyph
    inc e
    ld a,(ammo)
    call number_three
    ld a,(weapon)
    or a
    ld hl,weapon_knife
    jr z,.weapon
    dec a
    ld hl,weapon_pistol
    jr z,.weapon
    ld hl,weapon_shotgun
.weapon:
    ld de,HUD_ROW*256+11
    ld b,10
    jp pcg_pattern

hud_spaces:
    push af
    push bc
.loop:
    call pcg_putc
    inc e
    djnz .loop
    pop bc
    pop af
    ret

; A=0..255, DE=cell. Standard 5x7 ROM digits, three positions.
number_three:
    ld b,'0'-1
.hundreds:
    inc b
    sub 100
    jr nc,.hundreds
    add a,100
    ld c,a
    ld a,b
    call pcg_putc
    inc e
    ld a,c
    ld b,'0'-1
.tens:
    inc b
    sub 10
    jr nc,.tens
    add a,10
    ld c,a
    ld a,b
    call pcg_putc
    inc e
    ld a,c
    add a,'0'
    jp pcg_putc

    IF BUILD_LANG_EN
status_labels: db "D1K0",0
    ELSE
status_labels: db "E1C0",0
    ENDIF

    IF BUILD_LITE
title_text: db "DEPTHS LITE",0
    ELSE
title_text: db "POCKET DEPTHS",0
    ENDIF
    IF BUILD_LANG_EN
mission_text: db "2 BEACONS + KEY -> EXIT",0
start_text: db "ENTER:3 FLOORS M:HELP",0
    IF BUILD_LITE
quit_text: db "Q / BREAK: QUIT",0
    ELSE
quit_text: db "N: NEW LEVEL   Q: QUIT",0
    ENDIF
help_1: db "ARROWS: MOVE / TURN",0
help_2: db ",/;: STRAFE   E: DOOR",0
help_3: db "1/2/3: WEAPON SPACE:FIRE",0
help_4: db "KEY: 0 B:0/2 X:GUARD",0
defeat_text: db "YOU DIED",0
victory_text: db "EXIT REACHED!",0
restart_text: db "ENTER:NEXT R:RESTART",0
campaign_text: db "BASE SECURED!",0
compass_text: db "NESW"
    ELSE
mission_text: db "2 BALISES+CLE -> SORTIE",0
start_text: db "ENTREE:3 ETAGES M:AIDE",0
    IF BUILD_LITE
quit_text: db "Q / BREAK: QUITTER",0
    ELSE
quit_text: db "N: NIVEAU  Q: QUITTER",0
    ENDIF
help_1: db "FLECHES: AVANCE / TOURNE",0
help_2: db ",/;: PAS COTE  E: PORTE",0
help_3: db "1/2/3: ARME ESPACE:TIR",0
help_4: db "CLE: 0 B:0/2 X:GARDE",0
defeat_text: db "DEFAITE",0
victory_text: db "SORTIE ATTEINTE!",0
restart_text: db "ENTREE:SUITE R:REJOUER",0
campaign_text: db "BASE SECURISEE!",0
compass_text: db "NESO"
    ENDIF
