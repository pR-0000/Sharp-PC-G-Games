; Software column blitter; seven useful bits on G80X, eight on G850.
draw_game:
    xor a
    ld hl,screen_buffer
    ld (hl),a
    ld de,screen_buffer+1
    ld bc,PCG_FRAME_BYTES-1
    ldir
    ld hl,screen_buffer+DIVIDER_X
    ld bc,PCG_ROW_COLUMNS
    ld d,PCG_LCD_ROWS
.divider:
    ld (hl),PCG_GLYPH_MASK
    add hl,bc
    dec d
    jr nz,.divider
    xor a
    ld (scan_index),a
.alien:
    ld a,(scan_index)
    ld e,a
    ld d,0
    ld hl,aliens
    add hl,de
    ld a,(hl)
    or a
    jr z,.next
    call alien_coordinates
    ld a,(scan_index)
    cp 8
    ld hl,glyph_alien_a
    ld bc,ALIEN_WIDTH
    jr c,.animated
    ld hl,glyph_crab_a
.animated:
    ld a,(formation_x)
    and 1
    jr z,.paint
    add hl,bc
.paint:
    ld b,ALIEN_WIDTH
    call draw_sprite
.next:
    ld hl,scan_index
    inc (hl)
    ld a,(hl)
    cp 16
    jr c,.alien
    xor a
    ld (scan_index),a
.shield:
    ld a,(scan_index)
    ld e,a
    ld d,0
    ld hl,shields
    add hl,de
    ld a,(hl)
    or a
    jr z,.next_shield
    ld hl,glyph_shield_3
    cp 3
    jr z,.shield_glyph
    ld hl,glyph_shield_2
    cp 2
    jr z,.shield_glyph
    ld hl,glyph_shield_1
.shield_glyph:
    push hl
    ld hl,shield_positions
    add hl,de
    ld e,(hl)
    ld d,SHIELD_Y
    pop hl
    ld b,ALIEN_WIDTH
    call draw_sprite
.next_shield:
    ld hl,scan_index
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.shield
    ld a,(shot_y)
    cp 255
    jr z,.bombs
    ld d,a
    ld a,(shot_x)
    ld e,a
    ld hl,glyph_shot
    ld b,1
    call draw_sprite
.bombs:
    ld ix,bombs
    ld b,3
.bomb:
    push bc
    ld a,(ix+1)
    cp 255
    jr z,.next_bomb
    ld d,a
    ld e,(ix+0)
    ld hl,glyph_bomb
    ld b,1
    call draw_sprite
.next_bomb:
    inc ix
    inc ix
    pop bc
    djnz .bomb
    ld a,(grace)
    and 2
    jr nz,.explosion
    ld a,(player_x)
    ld e,a
    ld d,SHIP_Y
    ld hl,glyph_ship
    ld b,ALIEN_WIDTH
    call draw_sprite
.explosion:
    ld a,(explosion_timer)
    or a
    jr z,.display
    ld a,(explosion_x)
    sub 3
    jr nc,.left
    xor a
.left:
    ld e,a
    ld a,(explosion_y)
    ld d,a
    ld hl,glyph_explosion
    ld b,ALIEN_WIDTH
    call draw_sprite
.display:
    ld hl,screen_buffer
    ld de,0
.row:
    ld b,PCG_ROW_COLUMNS
    call pcg_pattern
    ld bc,PCG_ROW_COLUMNS
    add hl,bc
    inc d
    ld a,d
    cp PCG_LCD_ROWS
    jr c,.row
    call draw_hud
    ld a,(phase)
    cp 2
    jr nz,.pause
    ld hl,over_text
    ld de,$0102
    call pcg_puts
    ld hl,restart_text
    ld de,$0201
    jp pcg_puts
.pause:
    ld a,(paused)
    or a
    ret z
    ld hl,pause_text
    ld de,$0206
    jp pcg_puts

alien_coordinates:
    ld a,(scan_index)
    and 7
    ld c,a
    add a,a
    add a,a
    add a,a
    IF TARGET_G850
    add a,c
    add a,c
    add a,c
    add a,c                    ; 8c + 4c = 12c
    ELSE
    add a,c
    ENDIF
    ld c,a
    ld a,(formation_x)
    add a,c
    ld e,a
    ld a,(formation_y)
    ld d,a
    ld a,(scan_index)
    cp 8
    ret c
    ld a,d
    add a,ALIEN_ROW_STEP
    ld d,a
    ret

; HL->column glyph, D=pixel y, E=pixel x, B=width. Clips right/bottom.
draw_sprite:
    ld (draw_source),hl
    ld a,d
    cp PLAY_HEIGHT
    ret nc
    ld a,e
    cp PLAY_WIDTH
    ret nc
    ld (draw_x),a
    ld a,PLAY_WIDTH
    sub e
    cp b
    jr nc,.width
    ld b,a
.width:
    ld a,b
    or a
    ret z
    ld (draw_width),a
    ld hl,screen_buffer
    ld bc,PCG_ROW_COLUMNS
    ld a,d
    ld d,0
.divide:
    cp PCG_GLYPH_HEIGHT
    jr c,.row
    sub PCG_GLYPH_HEIGHT
    add hl,bc
    inc d
    jr .divide
.row:
    ld (draw_shift),a
    ld a,d
    ld (draw_row),a
    ld a,(draw_x)
    ld e,a
    ld d,0
    add hl,de
    ld (draw_destination),hl
.column:
    ld hl,(draw_source)
    ld a,(hl)
    and $7F
    ld l,a
    ld h,0
    ld a,(draw_shift)
    ld b,a
    or a
    jr z,.shifted
.shift:
    add hl,hl
    djnz .shift
.shifted:
    ld a,l
    and PCG_GLYPH_MASK
    ld c,a
    ld a,h
    IF !TARGET_G850
    add a,a
    bit 7,l
    jr z,.overflow
    inc a
    ENDIF
.overflow:
    ld (draw_overflow),a
    ld hl,(draw_destination)
    ld a,(hl)
    or c
    ld (hl),a
    ld a,(draw_row)
    cp PCG_LCD_ROWS-1
    jr nc,.advance
    ld de,PCG_ROW_COLUMNS
    add hl,de
    ld a,(draw_overflow)
    or (hl)
    ld (hl),a
.advance:
    ld hl,(draw_source)
    inc hl
    ld (draw_source),hl
    ld hl,(draw_destination)
    inc hl
    ld (draw_destination),hl
    ld hl,draw_width
    dec (hl)
    jr nz,.column
    ret

draw_hud:
    ld a,'S'
    ld de,HUD_COLUMN
    call pcg_putc
    ld hl,(score)
    ld de,HUD_COLUMN+1
    call number_four
    ld hl,wave_text
    ld de,$0100+HUD_COLUMN
    call pcg_puts
    ld a,(wave)
    ld de,$0100+HUD_COLUMN+1
    call number_two
    ld a,(auto_fire)
    or a
    jr z,.heart
    ld a,'A'
    ld de,$0117
    call pcg_putc
.heart:
    ld hl,glyph_heart
    ld de,$0200+HUD_COLUMN
    call pcg_glyph
    ld a,(grace)
    and 2
    jr z,.lives
    ld a,' '
    call pcg_putc
.lives:
    ld a,(lives)
    add a,'0'
    ld de,$0200+HUD_COLUMN+1
    call pcg_putc
    ld hl,glyph_alien_a
    ld de,$0300+HUD_COLUMN
    ld b,ALIEN_WIDTH
    call pcg_pattern
    ld a,(remaining)
    ld de,$0316
    jp number_two

number_two:
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

; HL=0..9999, DE=cell, normal ROM digits.
number_four:
    ld ix,decimal_places
    ld b,4
.digit:
    push bc
    ld c,(ix+0)
    ld b,(ix+1)
    ld a,'0'-1
.subtract:
    inc a
    or a
    sbc hl,bc
    jr nc,.subtract
    add hl,bc
    call pcg_putc
    inc e
    inc ix
    inc ix
    pop bc
    djnz .digit
    ret

title_screen:
    call pcg_clear
    ld hl,title_text
    ld de,5
    call pcg_puts
    ld hl,glyph_alien_a
    ld de,$0108
    ld b,ALIEN_WIDTH
    call pcg_pattern
    ld hl,glyph_crab_a
    ld de,$010D
    call pcg_pattern
    ld hl,start_text
    ld de,$0201
    call pcg_puts
    ld hl,record_text
    ld de,$0300
    call pcg_puts
    ld hl,(best_score)
    ld de,$0307
    jp number_four
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
    IF TARGET_G850
    call pcg_puts
    ld hl,photo_help
    ld de,0x0500
    ENDIF
    jp pcg_puts
    IF TARGET_G850
photo_help:
    IF BUILD_LANG_EN
    db "TAB: PHOTO FREEZE",0
    ELSE
    db "TAB: FIGER POUR PHOTO",0
    ENDIF
    ENDIF
