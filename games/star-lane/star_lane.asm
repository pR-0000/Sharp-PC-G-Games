; STAR LANE - shared G801/G805/G850 lane shooter.
; Copyright (c) 2026 P.RAIMBAULT. MIT licence.
; Assemble with SjASMPlus via ../../tools/build.py.
; MON -> USER<see build manifest> -> R -> upload -> G100.
; Up/Down or W/S (Z also up), P pause, R restart, Q/BREAK quit.
; All RAM, including buffers, is emitted into the BIN/HEX reservation.

    INCLUDE "game_platform.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 1
    ENDIF
    ORG PCG_USER_ORIGIN

PHASE_TITLE EQU 0
PHASE_PLAY  EQU 1
PHASE_OVER  EQU 2
TILE_ROCK   EQU 1
TILE_STAR   EQU 2
TILE_PIRATE EQU 3
TILE_HURT   EQU 4
TILE_BOLT   EQU 5
TILE_CELL   EQU 6
LANES EQU PCG_LCD_ROWS-1
STEP_POLLS EQU 48*(1+TARGET_G850)
PLAYER_COL  EQU 2
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
    ld a,(step_delay)
    ld (hl),a
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
    cp PCG_KEY_TAB
    jr z,.photo
    ld c,a
    ld a,(paused)
    or a
    ret nz
    ld a,c
    cp PCG_KEY_SPACE
    jp z,fire
    cp PCG_KEY_F
    jr z,.auto
    cp PCG_KEY_X
    jr z,.shield
    cp PCG_KEY_TAB
    jr z,.photo
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
    cp LANES-1
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
.auto:
    ld a,(autofire)
    xor 1
    ld (autofire),a
    ret
.shield:
    ld a,(shield_time)
    or a
    ret nz
    ld hl,charges
    ld a,(hl)
    or a
    ret z
    dec (hl)
    ld a,6
    ld (shield_time),a
    jp draw_game
.photo:
    ld a,(photo)
    xor 1
    ld (photo),a
    ld (paused),a
    jp draw_game
.pause:
    xor a
    ld (photo),a
    ld a,(paused)
    xor 1
    ld (paused),a
    jp draw_game

new_game:
    xor a
    ld (paused),a
    ld (invulnerable),a
    ld (autofire),a
    ld (photo),a
    ld (shield_time),a
    ld (sector_steps),a
    ld (wave_count),a
    ld (score),a
    ld (score+1),a
    ld hl,tiles
    ld (hl),a
    ld de,tiles+1
    ld bc,LANES*24-1
    ldir
    ld a,PHASE_PLAY
    ld (phase),a
    ld a,LANES/2
    ld (player_lane),a
    ld (spawn_count),a           ; first asteroid after one step
    ld a,3
    ld (lives),a
    ld (charges),a
    ld a,1
    ld (sector),a
    ld (combo),a
    ld a,255
    ld (shot_x),a
    ld a,STEP_POLLS
    ld (poll_count),a
    ld (step_delay),a
    jp draw_game

world_step:
    ld hl,shield_time
    ld a,(hl)
    or a
    jr z,.sector
    dec (hl)
.sector:
    ld hl,sector_steps
    inc (hl)
    ld a,(hl)
    and 63
    jr nz,.grace
    ld a,(sector)
    cp 9
    jr nc,.grace
    inc a
    ld (sector),a
    ld hl,step_delay
    ld a,(hl)
    sub 3*(1+TARGET_G850)
    ld (hl),a
.grace:
    ld a,(invulnerable)
    or a
    jr z,.shift
    dec a
    ld (invulnerable),a
.shift:
    ld hl,tiles+1
    ld de,tiles
    ld b,LANES
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
    call spawn_wave
.scoring:
    call pirate_fire
    ld a,(autofire)
    or a
    call nz,fire
    call advance_shot
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
    cp TILE_CELL
    jr z,.cell
    ld a,(shield_time)
    or a
    jr nz,.shield_hit
    ld a,(invulnerable)
    or a
    ret nz
    ld a,1
    ld (combo),a
    ld a,HIT_GRACE
    ld (invulnerable),a
    ld hl,lives
    dec (hl)
    ret nz
    ld a,PHASE_OVER
    ld (phase),a
    ret
.shield_hit:
    ld de,10
    jp add_score
.cell:
    ld hl,charges
    ld a,(hl)
    cp 3
    ret nc
    inc (hl)
    ret
.star:
    ld a,(combo)
    ld b,a
    ld de,0
.combo:
    ld hl,25
    add hl,de
    ex de,hl
    djnz .combo
    ld hl,combo
    ld a,(hl)
    cp 4
    jr nc,.reward
    inc (hl)
.reward:
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
    cp LANES
    ret c
    sub LANES
    jr .mod3

draw_game:
    ld de,0
    ld hl,hud
    call pcg_puts
    call draw_score
    ld a,(sector)
    add a,'0'
    ld de,8
    call pcg_putc
    ld a,(combo)
    add a,'0'
    ld de,12
    call pcg_putc
    ld a,(charges)
    add a,'0'
    ld de,17
    call pcg_putc
    ld de,21
    ld hl,glyph_heart
    call pcg_glyph
    ld de,23
    ld a,(lives)
    add a,'0'
    call pcg_putc
    ld hl,tiles
    ld de,frame_buffer+PCG_ROW_COLUMNS
    ld a,LANES
    ld (draw_rows),a
.row:
    ld b,24
.cell:
    push bc
    ld a,(hl)
    inc hl
    push hl
    ld c,a
    ld b,0
    ld hl,glyph_tiles
    ; Native tiles are six columns, G80X tiles five.
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    IF TARGET_G850
    add hl,bc
    ENDIF
    ld bc,PCG_GLYPH_WIDTH
    ldir
    pop hl
    pop bc
    djnz .cell
    ld a,(draw_rows)
    dec a
    ld (draw_rows),a
    jr nz,.row
    ld a,(invulnerable)
    and 1
    jr nz,.shot
    ld a,(player_lane)
    ld c,PLAYER_COL
    call frame_address
    ld hl,glyph_ship
    ld a,(shield_time)
    or a
    jr z,.ship
    ld hl,glyph_shield
.ship:
    ld bc,PCG_GLYPH_WIDTH
    ldir
.shot:
    ld a,(shot_x)
    cp 24
    jr nc,.blit
    ld c,a
    ld a,(shot_lane)
    call frame_address
    ld hl,glyph_laser
    ld bc,PCG_GLYPH_WIDTH
    ldir
.blit:
    ld hl,frame_buffer+PCG_ROW_COLUMNS
    ld de,$0100
.blit_row:
    ld b,PCG_ROW_COLUMNS
    call pcg_pattern
    ld bc,PCG_ROW_COLUMNS
    add hl,bc
    inc d
    ld a,d
    cp PCG_LCD_ROWS
    jr c,.blit_row
    ld a,(phase)
    cp PHASE_OVER
    jr z,.over
    ld a,(photo)
    or a
    ret nz
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

; A=lane C=column -> DE=pixel band address.
frame_address:
    ld hl,frame_buffer+PCG_ROW_COLUMNS
    ld de,PCG_ROW_COLUMNS
    or a
    jr z,.column
.row:
    add hl,de
    dec a
    jr nz,.row
.column:
    ld b,0
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    add hl,bc
    IF TARGET_G850
    add hl,bc
    ENDIF
    ex de,hl
    ret

draw_score:
    ld hl,(score)
    ld ix,decimal_powers
    ld de,2                     ; score row 0
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

    INCLUDE "combat.asm"
    INCLUDE "../../lib/game_runtime.asm"

title_text:     db "STAR LANE",0
    IF BUILD_LANG_EN
instructions_1: db "SPACE:FIRE F:AUTO X:SHLD",0
instructions_2: db "ARROWS:MOVE STARS:COMBO",0
instructions_3: db "ENTER:PLAY P:PAUSE R:NEW",0
hud:            db "S 0000 L1  x1  SH3      ",0
pause_text:     db "PAUSED  P:RESUME",0
over_text:      db "GAME OVER  ENTER:RETRY",0
exit_text:      db "STAR LANE - END",0
    ELSE
instructions_1: db "ESPACE:TIR F:AUTO X:BOUC",0
instructions_2: db "FLECHES ETOILES:COMBO",0
instructions_3: db "ENTREE:JEU P:PAUSE R:RAZ",0
hud:            db "S 0000 N1  x1  BO3      ",0
pause_text:     db "PAUSE  P:REPRENDRE",0
over_text:      db "PERDU  ENTREE:REJOUER",0
exit_text:      db "STAR LANE - FIN",0
    ENDIF
decimal_powers: dw 1000,100,10,1

    IF TARGET_G850
glyph_tiles:
glyph_empty: db 0,0,0,0,0,0
glyph_rock: db $3C,$7E,$E7,$C3,$7E,$3C
glyph_star: db $24,$18,$7E,$18,$24,0
glyph_pirate: db $18,$3C,$7E,$DB,$A5,$66
glyph_hurt: db $18,$24,$5A,$81,$A5,$66
glyph_bolt: db 0,$18,$3C,$18,0,0
glyph_cell: db $3C,$42,$5A,$5A,$42,$3C
glyph_ship: db $24,$66,$FF,$7E,$3C,$18
glyph_shield: db $7E,$A5,$FF,$FE,$BD,$7E
glyph_laser: db 0,$18,$18,$18,$18,0
    ELSE
glyph_tiles:
glyph_empty: db 0,0,0,0,0
glyph_rock:  db $3E,$77,$63,$77,$3E
glyph_star:  db $2A,$1C,$7F,$1C,$2A
glyph_pirate: db $1C,$2A,$7F,$2A,$1C
glyph_hurt: db $1C,$22,$55,$22,$1C
glyph_bolt: db 0,$08,$1C,$08,0
glyph_cell: db $3E,$22,$3E,$22,$3E
glyph_ship: db $14,$3E,$7F,$1C,$08
glyph_shield: db $7F,$55,$7F,$5D,$7F
glyph_laser: db 0,$08,$08,$08,0
    ENDIF
glyph_heart: db $0E,$1F,$3E,$1F,$0E

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
autofire: db 0
photo: db 0
shield_time: db 0
charges: db 3
sector: db 1
sector_steps: db 0
step_delay: db STEP_POLLS
combo: db 1
wave_count: db 0
shot_x: db 255
shot_lane: db 0
draw_rows: db 0
pirate_count: db 0
tiles: ds LANES*24,0
frame_buffer: ds PCG_FRAME_BYTES,0
program_end:
    ASSERT program_end <= $17E3
