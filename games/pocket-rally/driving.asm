; FR/EN: Q12.4 positions, eight speeds, sixteen headings, surface limits.
player_controls:
    ld a,(frame_count)
    and 1
    jr nz,player_pedals
    ld a,(buttons)
    and 3
    cp 1
    jr z,player_left
    cp 2
    jr nz,player_pedals
    ld a,(ix+4)
    inc a
    jr player_angle
player_left:
    ld a,(ix+4)
    dec a
player_angle:
    and 15
    ld (ix+4),a
player_pedals:
    ld a,(buttons)
    bit 3,a
    jr z,player_gas
    ld a,(ix+5)
    sub 2
    jr nc,player_speed_store
    xor a
    jr player_speed_store
player_gas:
    ld a,(frame_count)
    and 3
    ret nz
    ld a,(buttons)
    and 4
    ld b,a
    ld a,(auto_throttle)
    or b
    ld a,(ix+5)
    jr z,player_coast
    cp 7
    ret nc
    inc a
    jr player_speed_store
player_coast:
    or a
    ret z
    dec a
player_speed_store:
    ld (ix+5),a
    ret
car_coords:
    ld l,(ix+0)
    ld h,(ix+1)
    call fixed_to_int
    ld a,l
    ld (car_x),a
    ld l,(ix+2)
    ld h,(ix+3)
    call fixed_to_int
    ld a,l
    ld (car_y),a
    ret
; B tile x, C tile y -> A tile ID. Immutable row-RLE, BC preserved.
tile_at:
    ld a,b
    cp 48
    jr nc,tile_wall
    ld a,c
    cp 32
    jr nc,tile_wall
    push bc
    add a,a
    ld e,a
    ld d,0
    ld hl,(active_map)
    call indexed_word
    ld c,b
tile_find_run:
    ld a,(hl)
    rrca
    rrca
    rrca
    rrca
    and 15
    inc a
    ld b,a
    ld a,c
    sub b
    jr c,tile_found
    ld c,a
    inc hl
    jr tile_find_run
tile_found:
    ld a,(hl)
    and 15
    pop bc
    ret
tile_wall:
    ld a,4
    ret
tile_solid:
    cp 4
    jr z,tile_solid_yes
    cp 9
    jr z,tile_solid_yes
    or a
    ret
tile_solid_yes:
    scf
    ret
car_surface:
    call car_coords
    ld a,(car_x)
    srl a
    srl a
    ld b,a
    ld a,(car_y)
    srl a
    srl a
    ld c,a
    jp tile_at
car_drive:
    call car_surface
    or a
    jr z,car_offroad
    cp 8
    jr nz,car_delta
car_offroad:
    ld a,(ix+5)
    cp 4
    jr c,car_delta
    ld (ix+5),3
car_delta:
    ld a,(ix+4)
    rlca
    rlca
    rlca
    rlca
    ld e,a
    ld a,(ix+5)
    add a,a
    add a,e
    ld e,a
    ld d,0
    ld hl,drive_table
    add hl,de
    ld a,(hl)
    ld (drive_dx),a
    inc hl
    ld a,(hl)
    ld (drive_dy),a
    ld l,(ix+0)
    ld h,(ix+1)
    ld a,(drive_dx)
    call signed_word
    add hl,de
    ld (candidate_x),hl
    ld l,(ix+2)
    ld h,(ix+3)
    ld (candidate_y),hl
    call car_clear
    jr nc,car_block_x
    ld hl,(candidate_x)
    ld (ix+0),l
    ld (ix+1),h
    jr car_move_y
car_block_x:
    ld (ix+5),0
car_move_y:
    ld l,(ix+0)
    ld h,(ix+1)
    ld (candidate_x),hl
    ld l,(ix+2)
    ld h,(ix+3)
    ld a,(drive_dy)
    call signed_word
    add hl,de
    ld (candidate_y),hl
    call car_clear
    jr nc,car_block_y
    ld hl,(candidate_y)
    ld (ix+2),l
    ld (ix+3),h
    ret
car_block_y:
    ld (ix+5),0
    ret
; Carry = clear body. Check all four corners of a five-pixel collision box.
car_clear:
    ld hl,(candidate_x)
    call fixed_to_int
    ld a,h
    or a
    jr nz,car_blocked
    ld a,l
    cp 2
    jr c,car_blocked
    cp 190
    jr nc,car_blocked
    ld (car_x),a
    ld hl,(candidate_y)
    call fixed_to_int
    ld a,h
    or a
    jr nz,car_blocked
    ld a,l
    cp 2
    jr c,car_blocked
    cp 126
    jr nc,car_blocked
    ld (car_y),a
    sub 2
    srl a
    srl a
    ld c,a
    ld a,(car_x)
    sub 2
    srl a
    srl a
    ld b,a
    call tile_at
    call tile_solid
    jr c,car_blocked
    ld a,(car_x)
    add a,2
    srl a
    srl a
    ld b,a
    call tile_at
    call tile_solid
    jr c,car_blocked
    ld a,(car_y)
    add a,2
    srl a
    srl a
    ld c,a
    call tile_at
    call tile_solid
    jr c,car_blocked
    ld a,(car_x)
    sub 2
    srl a
    srl a
    ld b,a
    call tile_at
    call tile_solid
    jr c,car_blocked
    scf
    ret
car_blocked:
    or a
    ret
; A = tile row, DE = 48-byte destination. Used only by the tilemapper.
decode_row:
    cp 32
    jr nc,decode_wall
    push de
    add a,a
    ld e,a
    ld d,0
    ld hl,(active_map)
    call indexed_word
    pop de
    ld c,48
decode_run:
    ld a,(hl)
    rrca
    rrca
    rrca
    rrca
    and 15
    inc a
    ld b,a
    ld a,(hl)
    and 15
decode_fill:
    ld (de),a
    inc de
    dec c
    djnz decode_fill
    ld a,c
    or a
    ret z
    inc hl
    jr decode_run
decode_wall:
    ld b,48
    ld a,4
decode_wall_fill:
    ld (de),a
    inc de
    djnz decode_wall_fill
    ret
