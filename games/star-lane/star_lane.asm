; STAR LANE - PC-G801, 24 x 4, custom 5 x 7 pixel glyphs.
; Copyright (c) 2026 P.RAIMBAULT. MIT licence.
; Assemble with SjASMPlus via ../../tools/build.py.
; MON -> USER<see build manifest> -> R -> upload -> G100.
; Up/Down or W/S (Z also up), P pause, R restart, Q/BREAK quit.
; All RAM, including buffers, is emitted into the BIN/HEX reservation.

    INCLUDE "sharp_pc_g801.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 1
    ENDIF
    ORG PCG_USER_ORIGIN

PHASE_TITLE EQU 0
PHASE_PLAY  EQU 1
PHASE_OVER  EQU 2
TILE_ROCK   EQU 1
TILE_STAR   EQU 2
PLAYER_COL  EQU 2
STEP_POLLS  EQU 48               ; tune after testing the physical G801
SPAWN_STEPS EQU 3
HIT_GRACE   EQU 8                ; invulnerable world steps after a hit

entry:
    push ix
    push iy
    xor a
    ld (phase),a
    ld (last_key),a
    ld hl,0xACE1
    ld (random_state),hl
    call show_title
main_loop:
    call pcg_key_scan
    ld c,a
    ld a,(last_key)
    cp c
    ld a,c
    ld (last_key),a
    jr z,.tick
    or a
    jr z,.tick
    cp PCG_KEY_Q
    jp z,exit_game
    cp PCG_KEY_BREAK
    jp z,exit_game
    cp PCG_KEY_OFF
    jp z,exit_game
    call handle_key
.tick:
    ld a,(phase)
    cp PHASE_PLAY
    jr nz,.idle
    ld a,(paused)
    or a
    jr nz,.idle
    ld hl,poll_count
    dec (hl)
    jr nz,main_loop
    ld (hl),STEP_POLLS
    call world_step
    call draw_game
    jr main_loop
.idle:
    call random_next            ; mix key polling time into next game
    jr main_loop

handle_key:                     ; A = fresh key edge
    ld b,a
    ld a,(phase)
    cp PHASE_PLAY
    ld a,b
    jr z,.playing
    cp PCG_KEY_RETURN
    jp z,new_game
    cp PCG_KEY_SPACE
    jp z,new_game
    cp PCG_KEY_R
    jp z,new_game
    ret
.playing:
    cp PCG_KEY_R
    jp z,new_game
    cp PCG_KEY_P
    jr z,.pause
    ld c,a
    ld a,(paused)
    or a
    ret nz
    ld a,c
    cp PCG_KEY_UP
    jr z,.up
    cp PCG_KEY_W
    jr z,.up
    cp PCG_KEY_Z
    jr z,.up
    cp PCG_KEY_DOWN
    jr z,.down
    cp PCG_KEY_S
    ret nz
.down:
    ld a,(player_lane)
    cp 2
    ret z
    inc a
    jr .move
.up:
    ld a,(player_lane)
    or a
    ret z
    dec a
.move:
    ld (player_lane),a
    call collision
    jp draw_game
.pause:
    ld a,(paused)
    xor 1
    ld (paused),a
    jp draw_game

new_game:
    xor a
    ld (paused),a
    ld (invulnerable),a
    ld (score),a
    ld (score+1),a
    ld hl,tiles
    ld (hl),a
    ld de,tiles+1
    ld bc,71
    ldir
    ld a,PHASE_PLAY
    ld (phase),a
    ld a,1
    ld (player_lane),a
    ld (spawn_count),a           ; first asteroid after one step
    ld a,3
    ld (lives),a
    ld a,STEP_POLLS
    ld (poll_count),a
    jp draw_game

world_step:
    ld a,(invulnerable)
    or a
    jr z,.shift
    dec a
    ld (invulnerable),a
.shift:
    ld hl,tiles+1
    ld de,tiles
    ld b,3
.lane:
    push bc
    ld bc,23
    ldir                        ; left shift; source is one byte ahead
    xor a
    ld (de),a
    inc hl
    inc de
    pop bc
    djnz .lane
    ld hl,spawn_count
    dec (hl)
    jr nz,.scoring
    ld (hl),SPAWN_STEPS
    call random_lane
    ld (spawn_lane),a
    call lane_address
    ld de,23
    add hl,de
    ld (hl),TILE_ROCK
    call random_next
    and 3
    jr nz,.scoring
    ld a,(spawn_lane)
    inc a
    cp 3
    jr c,.star
    xor a
.star:
    call lane_address
    ld de,23
    add hl,de
    ld (hl),TILE_STAR
.scoring:
    ld de,1
    call add_score
    jp collision

lane_address:                   ; A = 0..2 -> HL = tiles + A*24
    ld hl,tiles
    or a
    ret z
    ld de,24
.next:
    add hl,de
    dec a
    jr nz,.next
    ret

collision:
    ld a,(player_lane)
    call lane_address
    inc hl
    inc hl
    ld a,(hl)
    or a
    ret z
    ld (hl),0
    cp TILE_STAR
    jr z,.star
    ld a,(invulnerable)
    or a
    ret nz
    ld a,HIT_GRACE
    ld (invulnerable),a
    ld hl,lives
    dec (hl)
    ret nz
    ld a,PHASE_OVER
    ld (phase),a
    ret
.star:
    ld de,25
    jp add_score

add_score:                      ; unsigned +DE, clamp to 9999
    ld hl,(score)
    add hl,de
    ld de,10000
    or a
    sbc hl,de
    jr c,.restore
    ld hl,9999
    jr .save
.restore:
    add hl,de
.save:
    ld (score),hl
    ret

random_next:                    ; 16-bit Galois LFSR, nonzero seed
    ld hl,(random_state)
    srl h
    rr l
    jr nc,.save
    ld a,h
    xor 0xB4
    ld h,a
.save:
    ld (random_state),hl
    ld a,l
    ret

random_lane:
    call random_next
.mod3:
    cp 3
    ret c
    sub 3
    jr .mod3

draw_game:
    ld de,0
    ld hl,hud
    call pcg_puts
    call draw_score
    ld de,21
    ld hl,glyph_heart
    call pcg_glyph
    ld de,23
    ld a,(lives)
    add a,'0'
    call pcg_putc
    ld hl,tiles
    ld d,1
.row:
    push de
    ld de,row_buffer
    ld b,24
.cell:
    push bc
    ld a,(hl)
    inc hl
    push hl
    ld c,a
    add a,a
    add a,a
    add a,c                     ; A = tile * 5
    ld c,a
    ld b,0
    ld hl,glyph_tiles
    add hl,bc
    ld bc,5
    ldir
    pop hl
    pop bc
    djnz .cell
    pop de
    push hl
    ld hl,row_buffer
    ld e,0
    ld b,PCG_ROW_COLUMNS
    call pcg_pattern
    pop hl
    inc d
    ld a,d
    cp PCG_LCD_ROWS
    jr c,.row
    ld a,(invulnerable)
    and 1
    jr nz,.overlay              ; blink the ship while protected
    ld a,(player_lane)
    inc a
    ld d,a
    ld e,PLAYER_COL
    ld hl,glyph_ship
    call pcg_glyph
.overlay:
    ld a,(phase)
    cp PHASE_OVER
    jr z,.over
    ld a,(paused)
    or a
    ret z
    ld hl,pause_text
    ld de,0x0203
    jp pcg_puts
.over:
    ld hl,over_text
    ld de,0x0200
    jp pcg_puts

draw_score:
    ld hl,(score)
    ld ix,decimal_powers
    ld de,10                    ; row 0, col 10
    ld b,4
.digit:
    push bc
    ld c,(ix+0)
    ld b,(ix+1)
    inc ix
    inc ix
    ld a,'0'-1
.subtract:
    inc a
    or a                        ; clear carry without destroying A
    sbc hl,bc
    jr nc,.subtract
    add hl,bc
    call pcg_putc
    inc e
    pop bc
    djnz .digit
    ret

show_title:
    call pcg_clear
    ld hl,title_text
    ld de,0x0006
    call pcg_puts
    ld hl,instructions_1
    ld de,0x0100
    call pcg_puts
    ld hl,instructions_2
    ld de,0x0200
    call pcg_puts
    ld hl,instructions_3
    ld de,0x0300
    jp pcg_puts

exit_game:
    call pcg_clear
    ld hl,exit_text
    ld de,0
    call pcg_puts
    pop iy
    pop ix
    ret                         ; return to monitor, original stack

    INCLUDE "../../lib/pcg801_runtime.asm"

title_text:     db "STAR LANE",0
    IF BUILD_LANG_EN
instructions_1: db "UP/DN W/S:MOVE  Q:QUIT",0
instructions_2: db "DODGE ROCKS, CATCH STARS",0
instructions_3: db "ENTER:PLAY P:PAUSE R:NEW",0
hud:            db "STAR LANE 0000          ",0
pause_text:     db "PAUSED  P:RESUME",0
over_text:      db "GAME OVER  ENTER:RETRY",0
exit_text:      db "STAR LANE - END",0
    ELSE
instructions_1: db "HAUT/BAS W/S   Q:QUITTER",0
instructions_2: db "EVITER ROCHES ET ETOILES",0
instructions_3: db "ENTREE:JEU P:PAUSE R:RAZ",0
hud:            db "STAR LANE 0000          ",0
pause_text:     db "PAUSE  P:REPRENDRE",0
over_text:      db "PERDU  ENTREE:REJOUER",0
exit_text:      db "STAR LANE - FIN",0
    ENDIF
decimal_powers: dw 1000,100,10,1

glyph_tiles:
glyph_empty: db 0x00,0x00,0x00,0x00,0x00
glyph_rock:  db 0x3E,0x77,0x63,0x77,0x3E
glyph_star:  db 0x2A,0x1C,0x7F,0x1C,0x2A
glyph_ship:  db 0x14,0x3E,0x7F,0x1C,0x08
glyph_heart: db 0x0E,0x1F,0x3E,0x1F,0x0E

data_start:
phase:         db 0
last_key:      db 0
player_lane:   db 1
lives:         db 3
paused:        db 0
invulnerable:  db 0
poll_count:    db STEP_POLLS
spawn_count:   db 1
spawn_lane:    db 0
score:         dw 0
random_state:  dw 0xACE1
tiles:         ds 72,0
row_buffer:    ds PCG_ROW_COLUMNS,0
program_end:
    ASSERT program_end < 0x1000 ; leaves ample space below 8 KiB boundary
