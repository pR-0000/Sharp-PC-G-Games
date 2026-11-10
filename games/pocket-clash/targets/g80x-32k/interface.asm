; G80X four-row menus and standings. Shared HUD/number routines above.
title_screen:
    ld hl,frame_buffer
    ld de,frame_buffer+1
    ld bc,CLASH_FRAME_BYTES-1
    ld (hl),0
    ldir
    ld a,14
    ld (zoom_n),a
    xor a
    ld (sprite_mirror),a
    ld hl,100
    ld (draw_x),hl
    ld hl,0
    ld (draw_y),hl
    ld a,(selected)
    ld b,a
    add a,a
    add a,b
    add a,a
    call draw_sprite
    call upload_frame
    ld hl,title_text
    ld de,0
    call pcg_puts
    ld hl,choose_text
    ld de,$0100
    call pcg_puts
    ld a,(selected)
    call character_name
    ld de,$0109
    call pcg_puts
    ld a,(selected)
    add a,a
    ld e,a
    ld d,0
    ld hl,profile_directory
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld de,$0200
    call pcg_puts
    ld hl,start_text
    ld de,$0300
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
    ld de,$0300
    jp pcg_puts
standings_screen:
    call pcg_clear
    ld a,1
    ld (rank_row),a
.row:
    ld a,(rank_row)
    dec a
    ld e,a
    ld d,0
    ld hl,ranking
    add hl,de
    ld a,(hl)
    ld (rank_id),a
    ld b,a
    ld a,(rank_row)
    dec a
    ld d,a
    ld e,0
    ld a,(selected)
    cp b
    ld a,' '
    jr nz,.marker
    ld a,'>'
.marker:
    call pcg_putc
    inc e
    ld a,(rank_row)
    add a,'0'
    call pcg_putc
    ld a,(rank_id)
    call character_name
    ld e,3
    call pcg_puts
    ld hl,points_text
    ld e,9
    call pcg_puts
    ld a,(rank_id)
    ld c,a
    ld b,0
    ld hl,points
    add hl,bc
    ld a,(hl)
    ld e,13
    call number_three
    ld hl,ko_text
    ld e,18
    call pcg_puts
    ld a,(rank_id)
    ld c,a
    ld b,0
    ld hl,knockouts
    add hl,bc
    ld a,(hl)
    ld e,21
    call number_three
    ld hl,rank_row
    inc (hl)
    ld a,(hl)
    cp 5
    jp c,.row
    ret
profile_directory: dw nova_text,volt_text,rok_text,lynx_text
points_text: db "PTS",0
ko_text: db "KO",0
title_text: db "POCKET CLASH",0
choose_text: db "< > HERO:",0
    IF BUILD_LANG_EN
nova_text: db "NOVA: BLADE DASH",0
volt_text: db "VOLT: ENERGY ORB",0
rok_text: db "ROK: HEAVY STRIKE",0
lynx_text: db "LYNX: AIR COMBAT",0
start_text: db "ENTER:CUP D:DEMO M:HELP",0
pause_text: db "PAUSED",0
help_1: db "ARROWS SPACE Z/X:ATTACK",0
help_2: db "DOWN:GUARD DOWN+SP:DROP",0
help_3: db "P:PAUSE TAB:PHOTO D:AUTO",0
help_4: db "2 JUMPS R:NEW Q:QUIT",0
    ELSE
nova_text: db "NOVA: RUEE LAME",0
volt_text: db "VOLT: ORBE ENERGIE",0
rok_text: db "ROK: COUP PUISSANT",0
lynx_text: db "LYNX: COMBAT AERIEN",0
start_text: db "ENTER:JEU D:DEMO M:AIDE",0
pause_text: db "PAUSE",0
help_1: db "FLECHES ESPACE Z/X:COUPS",0
help_2: db "BAS:GARDE BAS+ESP:CHUTE",0
help_3: db "P:PAUSE TAB:PHOTO D:AUTO",0
help_4: db "2 SAUTS R:REJOUER Q:FIN",0
    ENDIF
