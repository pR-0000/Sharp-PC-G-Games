; Three independent circuits, persistent cup totals and ordered race results.
; Configuration lives outside the per-race state cleared by new_game.
load_track:
    ld a,(track_index)
    add a,a
    ld l,a
    ld h,0
    ld de,rival_scales
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld (rival_step_scale),de
    ld a,(track_index)
    add a,a
    add a,a
    add a,a
    ld l,a
    ld h,0
    ld de,track_table
    add hl,de
    push hl
    pop ix
    ld l,(ix+4)
    ld h,(ix+5)
    ld de,path_nodes
    ld bc,512
    ldir
    ld l,(ix+6)
    ld h,(ix+7)
    ld de,skyline
    ld bc,144
    ldir
    ld l,(ix+0)
    ld h,(ix+1)
    ld de,texture_map
    call unpack_track
    ld l,(ix+2)
    ld h,(ix+3)
    ld de,road_map
unpack_track:
    ld a,(hl)
    inc hl
    or a
    ret z
    jp m,.match
    ld c,a
    ld b,0
    ldir
    jr unpack_track
.match:
    and 127
    add a,3
    ld (unpack_count),a
    ld c,(hl)
    inc hl
    ld b,(hl)
    inc hl
    push hl
    ld h,d
    ld l,e
    or a
    sbc hl,bc
    ld a,(unpack_count)
    ld c,a
    ld b,0
    ldir
    pop hl
    jr unpack_track

start_session:
    ; A: 0 cup, 1 single race, 2 demonstration. Cup always starts on track 0.
    ld (session_mode),a
    ld b,a
    xor a
    ld (cup_round),a
    ld (cup_points),a
    ld (cup_points+1),a
    ld (cup_points+2),a
    ld a,b
    or a
    ld a,0
    jr z,.track
    ld a,(menu_track)
.track:
    ld (track_index),a
    ld a,b
    cp 2
    ld a,0
    jr nz,.go
    inc a
.go:
    jp begin_race

finish_race:
    ld a,(race_awarded)
    or a
    ret nz
    ld a,1
    ld (race_awarded),a
    call block_screen_enter
    ld a,(energy)
    or a
    ld hl,0
    jr z,.player_key
    ld a,(lap)
    ld h,a
    ld a,(player_started)
    or a
    jr nz,.player_lap_ready
    dec h
.player_lap_ready:
    ld a,(section)
    ld l,a
    ld a,(player_finish)
    call finished_key
.player_key:
    ld (racer_keys),hl
    ld a,(rival1_energy)
    or a
    ld hl,0
    jr z,.rival1_key
    ld a,(rival1_lap)
    ld h,a
    ld a,(rival1_started)
    or a
    jr nz,.rival1_lap_ready
    dec h
.rival1_lap_ready:
    ld a,(rival1_progress+1)
    ld l,a
    ld a,(rival1_finish)
    call finished_key
.rival1_key:
    ld (racer_keys+2),hl
    ld a,(rival2_energy)
    or a
    ld hl,0
    jr z,.rival2_key
    ld a,(rival2_lap)
    ld h,a
    ld a,(rival2_started)
    or a
    jr nz,.rival2_lap_ready
    dec h
.rival2_lap_ready:
    ld a,(rival2_progress+1)
    ld l,a
    ld a,(rival2_finish)
    call finished_key
.rival2_key:
    ld (racer_keys+4),hl
    xor a
    ld (score_index),a
.pilot:
    ld a,(score_index)
    call position_for_key
    ld a,(score_index)
    ld e,a
    ld d,0
    ld hl,race_places
    add hl,de
    ld (hl),c
    ld hl,racer_keys
    add hl,de
    add hl,de
    ld a,(hl)
    inc hl
    or (hl)
    ld b,0
    jr z,.no_points
    ld a,c
    dec a
    ld l,a
    ld h,0
    ld de,points_table
    add hl,de
    ld b,(hl)
.no_points:
    ld a,(score_index)
    ld e,a
    ld d,0
    ld hl,race_points
    add hl,de
    ld (hl),b
    ld a,(session_mode)
    or a
    jr nz,.skip_total
    ld hl,cup_points
    add hl,de
    ld a,(hl)
    add a,b
    ld (hl),a
.skip_total:
    ld hl,score_index
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.pilot
    ld a,(race_places)
    ld (rank),a
    ret
finished_key:
    or a
    ret z
    ld b,a
    ld a,4
    sub b
    ld l,a
    ld h,255
    ret

; A pilot index -> C rank. Equal progress favours the lower index.
position_for_key:
    ld (key_index),a
    add a,a
    ld l,a
    ld h,0
    ld de,racer_keys
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld (target_key),de
    ld ix,racer_keys
    ld c,1
    ld b,0
.compare:
    ld hl,(target_key)
    ld e,(ix+0)
    ld d,(ix+1)
    or a
    sbc hl,de
    jr c,.ahead
    jr nz,.next
    ld a,(key_index)
    cp b
    jr c,.next
    jr z,.next
.ahead:
    inc c
.next:
    inc ix
    inc ix
    inc b
    ld a,b
    cp 3
    jr c,.compare
    ret

advance_result:
    call block_screen_enter
    ld a,(session_mode)
    or a
    jr z,.cup
    xor a
    ld (phase),a
    ld (demo_mode),a
    ld (photo_mode),a
    ret
.cup:
    ld a,(cup_round)
    cp 2
    jr nc,.standings
    inc a
    ld (cup_round),a
    ld (track_index),a
    xor a
    jp begin_race
.standings:
    ; Tied totals use the last race's finishing order as the tiebreak.
    ld a,(cup_points)
    ld b,a
    ld a,(race_places)
    call cup_key
    ld (racer_keys),hl
    ld a,(cup_points+1)
    ld b,a
    ld a,(race_places+1)
    call cup_key
    ld (racer_keys+2),hl
    ld a,(cup_points+2)
    ld b,a
    ld a,(race_places+2)
    call cup_key
    ld (racer_keys+4),hl
    xor a
    ld (score_index),a
.place:
    ld a,(score_index)
    call position_for_key
    ld a,(score_index)
    ld l,a
    ld h,0
    ld de,cup_places
    add hl,de
    ld (hl),c
    ld hl,score_index
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.place
    ld a,6
    ld (phase),a
    ret
cup_key:
    ld c,a
    ld a,b
    add a,a
    add a,a
    ld b,a
    ld a,4
    sub c
    add a,b
    ld l,a
    ld h,0
    ret
points_table: db 10,7,5

; Menu key edges: directions choose a mode and a single/demo circuit.
menu_navigation:
    ld a,(pressed)
    bit 2,a
    jr z,.no_up
    ld a,(menu_choice)
    dec a
    cp 255
    jr nz,.up_set
    ld a,2
.up_set:
    ld (menu_choice),a
.no_up:
    ld a,(pressed)
    bit 3,a
    jr z,.no_down
    ld a,(menu_choice)
    inc a
    cp 3
    jr c,.down_set
    xor a
.down_set:
    ld (menu_choice),a
.no_down:
    ld a,(pressed)
    bit 0,a
    jr z,.no_left
    ld a,(menu_track)
    dec a
    cp 255
    jr nz,.left_set
    ld a,2
.left_set:
    ld (menu_track),a
.no_left:
    ld a,(pressed)
    bit 1,a
    ret z
    ld a,(menu_track)
    inc a
    cp 3
    jr c,.right_set
    xor a
.right_set:
    ld (menu_track),a
    ret
