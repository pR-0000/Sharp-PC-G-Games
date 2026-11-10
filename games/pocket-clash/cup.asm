; Three-round round robin. Other two entrants play a simulated fixture.
start_cup:
    xor a
    ld (round_index),a
    ld hl,points
    ld (hl),0
    ld de,points+1
    ld bc,19
    ldir
start_round:
    xor a
    ld hl,fighters
    ld (hl),a
    ld de,fighters+1
    ld bc,75
    ldir
    ld (paused),a
    ld (photo_mode),a
    ld (frame_count),a
    ld (impact_time),a
    ld (hit_pause),a
    ld (camera_ready),a
    ld (confirm_ready),a
    ld a,(round_index)
    ld b,a
    ld hl,platform_initials
    ld de,12
    or a
    jr z,.copy
.offset:
    add hl,de
    djnz .offset
.copy:
    ld de,platforms
    ld bc,12
    ldir
    ld a,(selected)
    ld (fighters+FCHAR),a
    ld b,a
    ld a,(round_index)
    inc a
    add a,b
    and 3
    ld (fighters+FSIZE+FCHAR),a
    xor a
.init:
    push af
    call setup_pair
    ld (ix+FSTOCK),2
    ld (ix+FENERGY),48
    pop af
    push af
    call respawn_actor
    pop af
    inc a
    cp 2
    jr c,.init
    ld a,16
    ld (zoom_n),a
    ld a,60
    ld (countdown),a
    ld hl,1800
    ld (round_frames),hl
    ld a,1
    ld (phase),a
    call update_camera
    jp draw_game
respawn_actor:
    ; A=0/1; IX still points at this actor.
    ld (ix+FFACE),a
    ld hl,78*16
    or a
    jr z,.x
    ld hl,130*16
.x:
    ld (ix+FX),l
    ld (ix+FX+1),h
    ld a,(platforms+2)
    sub 16
    ld l,a
    ld h,0
    call int_to_fixed
    ld (ix+FY),l
    ld (ix+FY+1),h
    ld (ix+FVX),0
    ld (ix+FVY),0
    ld (ix+FDAMAGE),0
    ld (ix+FJUMPS),2
    ld (ix+FGROUND),1
    ld (ix+FATTACK),0
    ld (ix+FSTUN),0
    ld (ix+FAIR),0
    ld (ix+FGUARD),0
    ld (ix+FHIT),0
    ld (ix+FTYPE),0
    ld (ix+FLAST),0
    ret

finish_round:
    ld a,(fighters+FSIZE+FSTOCK)
    ld b,a
    ld a,(fighters+FSTOCK)
    cp b
    jr c,.lose
    jr nz,.win
    ld a,(fighters+FSIZE+FDAMAGE)
    ld b,a
    ld a,(fighters+FDAMAGE)
    cp b
    jr c,.win
    jr nz,.lose
    ld a,2
    ld (result_kind),a
    ld a,(selected)
    ld c,1
    call add_points
    ld a,(fighters+FSIZE+FCHAR)
    ld c,1
    call add_points
    jr .others
.win:
    xor a
    ld (result_kind),a
    ld a,(selected)
    jr .award
.lose:
    ld a,1
    ld (result_kind),a
    ld a,(fighters+FSIZE+FCHAR)
.award:
    ld c,3
    call add_points
.others:
    call other_fixture
    call sort_ranking
    xor a
    ld (confirm_ready),a
    ld a,(round_index)
    cp 2
    ld a,2
    jr c,.phase
    inc a
.phase:
    ld (phase),a
    jp standings_screen
add_points:
    ld e,a
    ld d,0
    ld hl,points
    add hl,de
    ld a,(hl)
    add a,c
    ld (hl),a
    ret
other_fixture:
    ld a,255
    ld (sort_left),a
    ld b,0
.find:
    ld a,(selected)
    cp b
    jr z,.next
    ld a,(fighters+FSIZE+FCHAR)
    cp b
    jr z,.next
    ld a,(sort_left)
    cp 255
    ld a,b
    jr nz,.right
    ld (sort_left),a
    jr .next
.right:
    ld (sort_right),a
.next:
    inc b
    ld a,b
    cp 4
    jr c,.find
    call random_next
    and 1
    ld a,(sort_left)
    jr z,.winner
    ld a,(sort_right)
.winner:
    push af
    ld c,3
    call add_points
    pop af
    ld e,a
    ld d,0
    ld hl,knockouts
    add hl,de
    inc (hl)
    inc (hl)
    ret
sort_ranking:
    ld hl,ranking
    ld b,4
    xor a
.init:
    ld (hl),a
    inc a
    inc hl
    djnz .init
    ld a,3
    ld (sort_i),a
.pass:
    xor a
    ld (sort_j),a
.pair:
    ld a,(sort_j)
    ld e,a
    ld d,0
    ld hl,ranking
    add hl,de
    ld a,(hl)
    ld (sort_left),a
    inc hl
    ld a,(hl)
    ld (sort_right),a
    call compare_ranks
    jr nc,.keep
    ld a,(sort_j)
    ld e,a
    ld d,0
    ld hl,ranking
    add hl,de
    ld a,(sort_right)
    ld (hl),a
    inc hl
    ld a,(sort_left)
    ld (hl),a
.keep:
    ld hl,sort_j
    inc (hl)
    ld a,(hl)
    cp 3
    jr c,.pair
    ld hl,sort_i
    dec (hl)
    jr nz,.pass
    ret
; Carry iff the right entrant must move ahead of the left.
compare_ranks:
    ld a,(sort_left)
    ld e,a
    ld d,0
    ld hl,points
    add hl,de
    ld b,(hl)
    ld a,(sort_right)
    ld e,a
    ld hl,points
    add hl,de
    ld a,b
    cp (hl)
    ret nz
    ld a,(sort_left)
    ld e,a
    ld hl,knockouts
    add hl,de
    ld b,(hl)
    ld a,(sort_right)
    ld e,a
    ld hl,knockouts
    add hl,de
    ld a,b
    cp (hl)
    ret nz
    ld a,(sort_left)
    add a,a
    ld e,a
    ld hl,damage_scores
    add hl,de
    ld c,(hl)
    inc hl
    ld b,(hl)
    ld a,(sort_right)
    add a,a
    ld e,a
    ld hl,damage_scores
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld h,b
    ld l,c
    or a
    sbc hl,de
    ret
