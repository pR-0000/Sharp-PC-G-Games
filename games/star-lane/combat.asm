; FR: tirs, pirates et vagues. EN: shots, pirates and waves.
fire:
    ld a,(shot_x)
    cp 24
    ret c
    ld a,PLAYER_COL+1
    ld (shot_x),a
    ld a,(player_lane)
    ld (shot_lane),a
    ret

advance_shot:
    ld a,(shot_x)
    cp 24
    ret nc
    ld b,3                     ; catches crossings after the world scroll
.loop:
    push bc
    ld a,(shot_lane)
    call lane_address
    ld a,(shot_x)
    ld c,a
    ld b,0
    add hl,bc
    ld a,(hl)
    or a
    jr z,.move
    cp TILE_STAR
    jr z,.move
    cp TILE_CELL
    jr z,.move
    cp TILE_PIRATE
    jr z,.wound
    ld (hl),0
    ld de,10
    cp TILE_HURT
    jr nz,.reward
    ld de,50
.reward:
    call add_score
    jr .done
.wound:
    ld (hl),TILE_HURT
.done:
    ld a,255
    ld (shot_x),a
    pop bc
    ret
.move:
    pop bc
    djnz .advance
    ret
.advance:
    ld hl,shot_x
    inc (hl)
    ld a,(hl)
    cp 24
    jr c,.loop
    ret

spawn_wave:
    call random_lane
    ld (spawn_lane),a
    call lane_address
    ld de,23
    add hl,de
    ld hl,wave_count
    inc (hl)
    ld a,(hl)
    and 3
    ld c,TILE_ROCK
    jr nz,.kind
    ld c,TILE_PIRATE
.kind:
    ld a,(spawn_lane)
    call lane_address
    ld de,23
    add hl,de
    ld (hl),c
    ; Sector three onward: an extra obstacle, always one lane kept open.
    ld a,(sector)
    cp 3
    jr c,.bonus
    ld a,(wave_count)
    and 1
    jr nz,.bonus
    ld a,(spawn_lane)
    call next_lane
    call lane_address
    ld de,23
    add hl,de
    ld (hl),TILE_ROCK
.bonus:
    ld a,(spawn_lane)
    or a
    jr nz,.dec
    ld a,LANES
.dec:
    dec a
    call lane_address
    ld de,23
    add hl,de
    ld a,(wave_count)
    and 7
    ld (hl),TILE_STAR
    ret nz
    ld (hl),TILE_CELL
    ret

next_lane:
    inc a
    cp LANES
    ret c
    xor a
    ret

pirate_fire:
    ld a,(sector_steps)
    and 7
    ret nz
    ld hl,tiles+1
    ld b,LANES
.lane:
    push bc
    ld b,23
.cell:
    ld a,(hl)
    cp TILE_PIRATE
    jr z,.shoot
    cp TILE_HURT
    jr nz,.next
.shoot:
    dec hl
    ld a,(hl)
    or a
    jr nz,.occupied
    ld (hl),TILE_BOLT
.occupied:
    inc hl
.next:
    inc hl
    djnz .cell
    inc hl
    pop bc
    djnz .lane
    ret
