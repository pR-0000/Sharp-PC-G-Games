; Native Sharp font for names, percentages, menus and standings.
character_name:
    ld c,a
    ld b,0
    ld hl,character_names
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    ret
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

draw_stock_icons:
    ld hl,tiny_heart
    ld de,frame_buffer+PCG_GLYPH_WIDTH*8
    ld bc,3
    ldir
    ld hl,tiny_heart
    ld de,frame_buffer+PCG_GLYPH_WIDTH*22
    ld bc,3
    ldir
    ld a,(fighters+FSTOCK)
    ld de,frame_buffer+PCG_GLYPH_WIDTH*8+4
    call stock_digit
    ld a,(fighters+FSIZE+FSTOCK)
    ld de,frame_buffer+PCG_GLYPH_WIDTH*22+4
stock_digit:
    ld c,a
    add a,a
    add a,c
    ld c,a
    ld b,0
    ld hl,tiny_digits
    add hl,bc
    ld bc,3
    ldir
    ret

draw_hud:
    ld a,(fighters+FCHAR)
    call character_name
    ld de,0
    call pcg_puts
    ld a,(fighters+FDAMAGE)
    ld de,4
    call number_three
    ld a,'%'
    ld de,7
    call pcg_putc
    ld a,(round_index)
    add a,'1'
    ld de,10
    call pcg_putc
    inc e
    ld a,'/'
    call pcg_putc
    inc e
    ld a,'3'
    call pcg_putc
    ld a,(fighters+FSIZE+FCHAR)
    call character_name
    ld de,14
    call pcg_puts
    ld a,(fighters+FSIZE+FDAMAGE)
    ld de,18
    call number_three
    ld a,'%'
    ld de,21
    jp pcg_putc

    IF TARGET_G850
title_screen:
    ld hl,frame_buffer
    ld (hl),0
    ld de,frame_buffer+1
    ld bc,863
    ldir
    ld a,16
    ld (zoom_n),a
    xor a
    ld (sprite_mirror),a
    ld hl,118
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
    ld hl,cup_text
    ld de,$0300
    call pcg_puts
    ld hl,start_text
    ld de,$0400
    call pcg_puts
    ld hl,menu_help
    ld de,$0500
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
    call pcg_puts
    ld hl,help_5
    ld de,$0400
    call pcg_puts
    ld hl,help_6
    ld de,$0500
    jp pcg_puts
standings_screen:
    call pcg_clear
    ld a,(phase)
    cp 3
    jr z,.final
    ld a,(round_index)
    add a,'1'
    ld de,0
    call pcg_putc
    inc e
    ld a,'/'
    call pcg_putc
    inc e
    ld a,'3'
    call pcg_putc
    ld a,(result_kind)
    add a,a
    ld e,a
    ld d,0
    ld hl,result_directory
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld de,5
    call pcg_puts
    jr .table
.final:
    ld hl,final_text
    ld de,3
    call pcg_puts
.table:
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
    ld a,(selected)
    cp b
    ld a,' '
    jr nz,.marker
    ld a,'>'
.marker:
    ld e,0
    ld a,(rank_row)
    ld d,a
    ld a,(selected)
    cp b
    ld a,' '
    jr nz,.write_marker
    ld a,'>'
.write_marker:
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
    ld a,(phase)
    cp 3
    ld hl,next_text
    jr nz,.footer
    ld hl,end_text
.footer:
    ld de,$0500
    jp pcg_puts
profile_directory: dw nova_text,volt_text,rok_text,lynx_text
result_directory: dw win_text,lose_text,draw_text
points_text: db "PTS",0
ko_text: db "KO",0
title_text: db "POCKET CLASH",0
    IF BUILD_LANG_EN
choose_text: db "< > HERO:",0
nova_text: db "NOVA: BLADE DASH",0
volt_text: db "VOLT: ENERGY ORB",0
rok_text: db "ROK: HEAVY STRIKE",0
lynx_text: db "LYNX: AIR COMBAT",0
cup_text: db "3 ARENAS / 3 BATTLES",0
start_text: db "ENTER:CUP  D:DEMO",0
menu_help: db "M:HELP    Q:QUIT",0
pause_text: db "PAUSED",0
help_1: db "ARROWS:MOVE SPACE:JUMP",0
help_2: db "Z:ATTACK   X:SPECIAL",0
help_3: db "DOWN:GUARD OR FAST FALL",0
help_4: db "2 JUMPS + AIR SPECIAL",0
help_5: db "P:PAUSE TAB:PHOTO Q:QUIT",0
help_6: db "DOWN+SPACE:DROP ANY KEY",0
win_text: db "VICTORY",0
lose_text: db "DEFEAT",0
draw_text: db "DRAW",0
final_text: db "FINAL STANDINGS",0
next_text: db "ENTER:NEXT   Q:QUIT",0
end_text: db "ENTER:MENU R:NEW CUP",0
    ELSE
choose_text: db "< > HERO:",0
nova_text: db "NOVA: RUEE LAME",0
volt_text: db "VOLT: ORBE ENERGIE",0
rok_text: db "ROK: COUP PUISSANT",0
lynx_text: db "LYNX: COMBAT AERIEN",0
cup_text: db "3 ARENES / 3 COMBATS",0
start_text: db "ENTREE:COUPE D:DEMO",0
menu_help: db "M:AIDE    Q:QUITTER",0
pause_text: db "PAUSE",0
help_1: db "FLECHES / ESPACE:SAUT",0
help_2: db "Z:ATTAQUE   X:SPECIAL",0
help_3: db "BAS:GARDE / CHUTE RAPIDE",0
help_4: db "2 SAUTS + SPECIAL AERIEN",0
help_5: db "P:PAUSE TAB:PHOTO Q:FIN",0
help_6: db "BAS+ESPACE:TRAVERSE",0
win_text: db "VICTOIRE",0
lose_text: db "DEFAITE",0
draw_text: db "EGALITE",0
final_text: db "CLASSEMENT FINAL",0
next_text: db "ENTREE:SUITE Q:QUITTER",0
end_text: db "ENTREE:MENU R:REJOUER",0
    ENDIF
    ELSE
    INCLUDE "targets/g80x-32k/interface.asm"
    ENDIF
