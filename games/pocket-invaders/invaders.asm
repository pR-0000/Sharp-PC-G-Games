; POCKET INVADERS - G80X 90x28 / G850 108x48; right native-font panel.
; FR/EN: PC-G801/G805/G850, IOCS communs, aucun acces aux ports LCD.
; Common IOCS only; no LCD ports. MIT, (c) 2026 P.RAIMBAULT.
    INCLUDE "game_platform.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 0
    ENDIF
    IF TARGET_G850
    INCLUDE "targets/g850/config.inc"
    ELSE
    INCLUDE "targets/g80x/config.inc"
    ENDIF
FORMATION_LIMIT EQU PLAY_WIDTH-ALIEN_WIDTH-7*ALIEN_SPACING
FORMATION_START_X EQU FORMATION_LIMIT/2
PLAYER_LIMIT EQU PLAY_WIDTH-SHIP_WIDTH
    ORG $0100

entry:
    push bc
    push de
    push hl
    push ix
    push iy
    xor a
    ld (phase),a
    ld (last_key),a
    ld (paused),a
    ld hl,$ACE1
    ld (random_state),hl
    call title_screen
main_loop:
    call pcg_key_scan
    ld (held_key),a
    IF TARGET_G850
    call invaders_controls
    ENDIF
    ld c,a
    ld a,(last_key)
    cp c
    ld a,c
    ld (last_key),a
    jr z,.tick
    cp PCG_KEY_Q
    jp z,quit
    cp PCG_KEY_BREAK
    jp z,quit
    cp PCG_KEY_OFF
    jp z,quit
    or a
    call nz,handle_key
.tick:
    ld a,(phase)
    cp 1
    jr nz,.idle
    ld a,(paused)
    or a
    jr nz,.idle
    IF TARGET_G850
    ld a,(photo_frozen)
    or a
    jr nz,.idle
    ENDIF
    call world_step
    call draw_game
    ; Base pacing ~27 ms at 4 MHz, plus game/render/IOCS work.
    ; Real-device cadence remains to be measured; no interrupt takeover.
    ld bc,FRAME_DELAY
.wait:
    dec bc
    ld a,b
    or c
    jr nz,.wait
    jp main_loop
.idle:
    call random_next
    jp main_loop
quit:
    pop iy
    pop ix
    pop hl
    pop de
    pop bc
    ret

handle_key:
    ld b,a
    ld a,(phase)
    cp 4
    jr nz,.normal
    ld a,(help_previous)
    ld (phase),a
    cp 1
    jp z,draw_game
    jp title_screen
.normal:
    ld a,b
    cp PCG_KEY_M
    jr nz,.restart
    ld a,(phase)
    ld (help_previous),a
    ld a,4
    ld (phase),a
    jp help_screen
.restart:
    cp PCG_KEY_R
    jp z,new_game
    ld c,a
    ld a,(phase)
    cp 1
    ld a,c
    jr z,.playing
    cp PCG_KEY_RETURN
    jp z,new_game
    cp PCG_KEY_SPACE
    jp z,new_game
    ret
.playing:
    IF TARGET_G850
    cp PCG_KEY_TAB
    jr nz,.pause_key
    ld a,(photo_frozen)
    xor 1
    ld (photo_frozen),a
    ret
.pause_key:
    ENDIF
    cp PCG_KEY_P
    jr nz,.auto
    ld a,(paused)
    xor 1
    ld (paused),a
    jp draw_game
.auto:
    cp PCG_KEY_F
    ret nz
    ld a,(auto_fire)
    xor 1
    ld (auto_fire),a
    ret

new_game:
    call pcg_clear
    xor a
    IF TARGET_G850
    ld (photo_frozen),a
    ENDIF
    ld (paused),a
    ld (auto_fire),a
    ld (grace),a
    ld (tick_count),a
    ld (score),a
    ld (score+1),a
    ld a,1
    ld (phase),a
    ld (wave),a
    ld a,3
    ld (lives),a
    ld a,PLAYER_LIMIT/2
    ld (player_x),a
    call reset_wave
    jp draw_game
reset_wave:
    ld a,1
    ld hl,aliens
    ld b,16
.aliens:
    ld (hl),a
    inc hl
    djnz .aliens
    ld (formation_dir),a
    ld a,16
    ld (remaining),a
    ld a,FORMATION_START_X
    ld (formation_x),a
    ld a,FORMATION_START_Y
    ld (formation_y),a
    ld a,5
    ld (move_timer),a
    ld a,14
    ld (bomb_timer),a
    ld a,255
    ld (shot_y),a
    ld (bombs+1),a
    ld (bombs+3),a
    ld (bombs+5),a
    xor a
    ld (fire_timer),a
    ld (explosion_timer),a
    ld a,3
    ld (shields),a
    ld (shields+1),a
    ld (shields+2),a
    ret
next_wave:
    ld a,(wave)
    cp 99
    jr nc,.reset
    inc a
    ld (wave),a
.reset:
    jp reset_wave

world_step:
    ld hl,tick_count
    inc (hl)
    ld a,(grace)
    or a
    jr z,.explosion
    dec a
    ld (grace),a
.explosion:
    ld a,(explosion_timer)
    or a
    jr z,.move
    dec a
    ld (explosion_timer),a
.move:
    IF TARGET_G850
    ld a,(input_buttons)
    and 3
    cp 1
    jr z,.left
    cp 2
    jr nz,.fire
    ELSE
    ld a,(held_key)
    cp PCG_KEY_LEFT
    jr z,.left
    cp PCG_KEY_A
    jr z,.left
    cp PCG_KEY_RIGHT
    jr z,.right
    cp PCG_KEY_D
    jr nz,.fire
.right:
    ENDIF
    ld a,(player_x)
    cp PLAYER_LIMIT
    jr nc,.fire
    inc a
    jr .store
.left:
    ld a,(player_x)
    or a
    jr z,.fire
    dec a
.store:
    ld (player_x),a
.fire:
    call fire_player
    call step_shot
    ld a,(remaining)
    or a
    jp z,next_wave
    call move_formation
    ld a,(phase)
    cp 1
    ret nz
    call step_bombs
    ld a,(phase)
    cp 1
    ret nz
    ld hl,bomb_timer
    dec (hl)
    ret nz
    ld a,(wave)
    cp 9
    jr c,.rate
    ld a,8
.rate:
    ld b,a
    ld a,19
    sub b
    ld (hl),a
    jp launch_bomb

fire_player:
    ld a,(fire_timer)
    or a
    jr z,.ready
    dec a
    ld (fire_timer),a
    ret
.ready:
    ld a,(shot_y)
    cp 255
    ret nz
    ld a,(auto_fire)
    or a
    jr nz,.shoot
    IF TARGET_G850
    ld a,(input_buttons)
    and 4
    ret z
    ELSE
    ld a,(held_key)
    cp PCG_KEY_SPACE
    jr z,.shoot
    cp PCG_KEY_RETURN
    ret nz
    ENDIF
.shoot:
    ld a,(player_x)
    add a,SHIP_WIDTH/2
    ld (shot_x),a
    ld a,SHIP_Y-1
    ld (shot_y),a
    ld a,5
    ld (fire_timer),a
    ret

step_shot:
    ld a,(shot_y)
    cp 255
    ret z
    ld b,2
.pixel:
    push bc
    ld a,(shot_y)
    dec a
    ld (shot_y),a
    cp 255                      ; y=0 is drawable; stop on underflow
    jr z,.stop
    ld (probe_y),a
    ld a,(shot_x)
    ld (probe_x),a
    call shield_collision
    or a
    jr nz,.stop
    call find_alien
    or a
    jr z,.next
    ld (hl),0
    ld hl,remaining
    dec (hl)
    ld a,(probe_x)
    ld (explosion_x),a
    ld a,(probe_y)
    ld (explosion_y),a
    ld a,3
    ld (explosion_timer),a
    call add_score
.stop:
    ld a,255
    ld (shot_y),a
    pop bc
    ret
.next:
    pop bc
    djnz .pixel
    ret

; Probe inside a live alien; HL points at its live flag, A=1.
find_alien:
    ld a,(formation_x)
    ld b,a
    ld a,(probe_x)
    sub b
    jr c,.miss
    ld c,0
.column:
    cp ALIEN_SPACING
    jr c,.remainder
    sub ALIEN_SPACING
    inc c
    jr .column
.remainder:
    cp ALIEN_WIDTH
    jr nc,.miss
    ld a,c
    cp 8
    jr nc,.miss
    ld a,(formation_y)
    ld b,a
    ld a,(probe_y)
    sub b
    jr c,.miss
    cp ALIEN_ROW_STEP
    jr c,.row
    sub ALIEN_ROW_STEP
    ld b,a
    ld a,c
    add a,8
    ld c,a
    ld a,b
.row:
    cp ALIEN_HEIGHT
    jr nc,.miss
    ld b,0
    ld hl,aliens
    add hl,bc
    ld a,(hl)
    ret
.miss:
    xor a
    ret

move_formation:
    ld hl,move_timer
    dec (hl)
    ret nz
    ld a,(remaining)
    srl a
    srl a
    inc a
    ld (hl),a
    ld a,(formation_dir)
    ld b,a
    ld a,(formation_x)
    add a,b
    cp FORMATION_LIMIT+1
    jr nc,.bounce
    ld (formation_x),a
    ret
.bounce:
    ld a,b
    neg
    ld (formation_dir),a
    ld hl,formation_y
    inc (hl)
    ld a,(hl)
    add a,ALIEN_HEIGHT
    ld b,a
    ld hl,aliens+8
    ld c,8
.bottom:
    ld a,(hl)
    or a
    jr nz,.lowest
    inc hl
    dec c
    jr nz,.bottom
    ld a,b
    jr .check
.lowest:
    ld a,b
    add a,ALIEN_ROW_STEP
.check:
    cp SHIP_Y
    ret c
    jp game_over

launch_bomb:
    ld ix,bombs
    ld b,3
.slot:
    ld a,(ix+1)
    cp 255
    jr z,.choose
    inc ix
    inc ix
    djnz .slot
    ret
.choose:
    call random_next
    and 7
    ld c,a
    ld e,a
    ld d,0
    ld hl,aliens+8
    add hl,de
    ld a,(hl)
    or a
    ld b,ALIEN_ROW_STEP
    jr nz,.origin
    ld hl,aliens
    add hl,de
    ld a,(hl)
    or a
    ret z
    ld b,0
.origin:
    ld a,(formation_y)
    add a,b
    add a,ALIEN_HEIGHT
    ld (ix+1),a
    ld a,c
    add a,a
    add a,a
    IF TARGET_G850
    add a,c
    add a,c
    add a,a                    ; column * 12
    ELSE
    add a,a
    add a,c                    ; column * 9
    ENDIF
    ld b,a
    ld a,(formation_x)
    add a,b
    add a,ALIEN_WIDTH/2
    ld (ix+0),a
    ret

step_bombs:
    ld a,(tick_count)
    and 1
    ret nz
    ld ix,bombs
    ld b,3
.bomb:
    push bc
    ld a,(ix+1)
    cp 255
    jr z,.next
    inc a
    ld (ix+1),a
    cp PLAY_HEIGHT
    jr nc,.stop
    ld (probe_y),a
    ld a,(ix+0)
    ld (probe_x),a
    call shield_collision
    or a
    jr nz,.stop
    ld a,(probe_y)
    cp SHIP_Y
    jr c,.next
    ld a,(player_x)
    ld c,a
    ld a,(probe_x)
    sub c
    cp SHIP_WIDTH
    jr nc,.next
    ld a,(grace)
    or a
    jr nz,.stop
    ld a,40
    ld (grace),a
    ld hl,lives
    dec (hl)
    call z,game_over
.stop:
    ld (ix+1),255
.next:
    inc ix
    inc ix
    pop bc
    djnz .bomb
    ret

; All projectiles erode shields; dimensions come from the target profile.
shield_collision:
    ld a,(probe_y)
    sub SHIELD_Y
    cp SHIELD_HEIGHT
    jr nc,.miss
    ld hl,shields
    ld de,shield_positions
    ld b,3
.shield:
    ld a,(de)
    ld c,a
    ld a,(probe_x)
    sub c
    cp SHIELD_WIDTH
    jr nc,.next
    ld a,(hl)
    or a
    jr z,.miss
    dec (hl)
    ld a,1
    ret
.next:
    inc de
    inc hl
    djnz .shield
.miss:
    xor a
    ret

add_score:
    ld hl,(score)
    ld de,10
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
game_over:
    ld a,2
    ld (phase),a
    ld hl,(score)
    ld de,(best_score)
    or a
    sbc hl,de
    ret c
    add hl,de
    ld (best_score),hl
    ret
random_next:
    ld hl,(random_state)
    srl h
    rr l
    jr nc,.save
    ld a,h
    xor $B4
    ld h,a
.save:
    ld (random_state),hl
    ld a,l
    ret

    INCLUDE "render.asm"
    INCLUDE "game_runtime.asm"
    IF TARGET_G850
    INCLUDE "targets/g850/input.asm"
    ENDIF

    IF BUILD_LANG_EN
start_text: db "ENTER: PLAY  M: HELP",0
record_text: db "BEST       Q:QUIT",0
help_1: db "ARROWS / A D: MOVE",0
help_2: db "SPACE: FIRE  F: AUTOFIRE",0
help_3: db "P:PAUSE  R:RESTART",0
help_4: db "Q/BREAK:QUIT  M:BACK",0
over_text: db "GAME OVER",0
restart_text: db "R:RESTART Q:QUIT",0
wave_text: db "W",0
    ELSE
start_text: db "ENTER:JOUER  M:AIDE",0
record_text: db "RECORD     Q:QUITTER",0
help_1: db "FLECHES / A D: BOUGER",0
help_2: db "ESPACE:TIR  F:TIR AUTO",0
help_3: db "P:PAUSE  R:REJOUER",0
help_4: db "Q/BREAK:QUITTER  M:RETOUR",0
over_text: db "PARTIE TERMINEE",0
restart_text: db "R:REJOUER Q:FIN",0
wave_text: db "V",0
    ENDIF
title_text: db "POCKET INVADERS",0
score_text: db "SCORE",0
pause_text: db "PAUSE",0
auto_text: db "A",0
    IF TARGET_G850
    INCLUDE "targets/g850/graphics.asm"
    ELSE
glyph_alien_a: db $0C,$1E,$15,$1F,$15,$1E,$0C
glyph_alien_b: db $14,$0E,$15,$1F,$15,$0E,$14
glyph_crab_a: db $12,$0E,$1B,$0F,$1B,$0E,$12
glyph_crab_b: db $09,$0E,$1B,$0F,$1B,$0E,$09
glyph_ship: db $08,$0C,$0E,$0F,$0E,$0C,$08
glyph_shield_3: db $06,$07,$03,$01,$03,$07,$06
glyph_shield_2: db $04,$03,$01,$00,$03,$05,$02
glyph_shield_1: db $00,$02,$00,$00,$01,$00,$02
glyph_explosion: db $11,$0A,$04,$1F,$04,$0A,$11
glyph_bomb: db $05
glyph_shot: db $03
glyph_heart: db $06,$0F,$1E,$0F,$06
shield_positions: db 10,36,66
    ENDIF
decimal_places: dw 1000,100,10,1

data_start:
phase: db 0
help_previous: db 0
paused: db 0
last_key: db 0
held_key: db 0
auto_fire: db 0
score: dw 0
best_score: dw 0
wave: db 1
lives: db 3
player_x: db PLAYER_LIMIT/2
formation_x: db FORMATION_START_X
formation_y: db FORMATION_START_Y
formation_dir: db 1
move_timer: db 5
remaining: db 16
tick_count: db 0
fire_timer: db 0
bomb_timer: db 14
shot_x: db 0
shot_y: db 255
grace: db 0
probe_x: db 0
probe_y: db 0
explosion_x: db 0
explosion_y: db 0
explosion_timer: db 0
random_state: dw $ACE1
scan_index: db 0
actor_x: db 0
actor_y: db 0
draw_source: dw 0
draw_destination: dw 0
draw_width: db 0
draw_x: db 0
draw_row: db 0
draw_shift: db 0
draw_overflow: db 0
aliens: ds 16,1
shields: db 3,3,3
bombs: db 0,255,0,255,0,255
screen_buffer: ds PCG_FRAME_BYTES,0
    IF TARGET_G850
input_buttons: db 0
photo_frozen: db 0
frame_buffer EQU screen_buffer
    ENDIF
program_end:
    IF TARGET_G850
    ASSERT program_end <= 0x7000
    ELSE
    ASSERT program_end <= $17E3
    ENDIF
