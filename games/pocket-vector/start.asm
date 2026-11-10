; Empty-track orbit (7), grid arrival (9), countdown (8), then shared GO.
; Presentation does not advance physical positions, AI or laps.
begin_race:
    call new_game
begin_start:
    ld a,7
    ld (phase),a
    ld a,1
    ld (pause_previous),a
    xor a
    ld (start_timer),a
    ld (countdown_stage),a
    ld (go_frames),a
    ld a,(heading)
    ld (intro_angle),a
    xor a
    call node_pointer
    ld a,(hl)
    ld (intro_center_x+1),a
    xor a
    ld (intro_center_x),a
    inc hl
    ld a,(hl)
    ld (intro_center_y+1),a
    xor a
    ld (intro_center_y),a
    ret
begin_arrival:
    ld a,9
    ld (phase),a
    xor a
    ld (start_timer),a
    ret
begin_countdown:
    ld a,8
    ld (phase),a
    xor a
    ld (start_timer),a
    ld (countdown_stage),a
    ret
start_tick:
    ld a,(phase)
    cp 7
    jr nz,.countdown
    ld a,(intro_angle)
    add a,2
    and 63
    ld (intro_angle),a
    ld hl,start_timer
    inc (hl)
    ld a,(hl)
    cp INTRO_FRAMES
    ret c
    jp begin_arrival
.countdown:
    cp 9
    jr z,.arrival
    cp 8
    ret nz
    ld hl,start_timer
    inc (hl)
    ld a,(hl)
    cp COUNTDOWN_FRAMES
    ret c
    ld (hl),0
    ld hl,countdown_stage
    inc (hl)
    ld a,(hl)
    cp 3
    ret c
    ld a,1
    ld (phase),a
    ld a,GO_FRAMES
    ld (go_frames),a
    ret
.arrival:
    ld hl,start_timer
    inc (hl)
    ld a,(hl)
    cp ARRIVAL_FRAMES
    ret c
    jp begin_countdown

; Vertical screen offset only; world positions stay fixed until GO.
arrival_offset:
    call view_phase
    cp 9
    ld a,0
    ret nz
    ld a,(start_timer)
    ld b,a
    ld a,ARRIVAL_FRAMES
    sub b
    ld b,a
    add a,a
    add a,b
    ret

; Return the presentation phase even while a photo/pause is active.
view_phase:
    ld a,(phase)
    cp 2
    ret nz
    ld a,(pause_previous)
    ret
