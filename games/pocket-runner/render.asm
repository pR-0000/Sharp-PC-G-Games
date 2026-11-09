; FR/EN: 20x4 visible cells, 20x12 world, four-column native HUD.
draw_game:
    ld a,(player_pos)
    ld b,0
camera_divide:
    cp 20
    jr c,camera_follow
    sub 20
    inc b
    jr camera_divide
camera_follow:
    ld a,b
    or a
    jr z,camera_store
    dec a
    cp 9
    jr c,camera_store
    ld a,8
camera_store:
    ld (camera_y),a
    ld b,a
    add a,a
    add a,a
    add a,b
    add a,a
    add a,a
    ld (draw_cell),a
    ld hl,frame_buffer
    ld de,frame_buffer+1
    ld bc,479
    ld (hl),0
    ldir
    xor a
    ld (draw_row),a
    ld de,frame_buffer
map_row:
    ld a,20
    ld (draw_column),a
map_cell:
    push de
    ld a,(draw_cell)
    call tile
    call pattern_address
    pop de
    ld bc,5
    ldir
    ld hl,draw_cell
    inc (hl)
    ld hl,draw_column
    dec (hl)
    jr nz,map_cell
    ex de,hl
    ld de,20
    add hl,de
    ex de,hl
    ld hl,draw_row
    inc (hl)
    ld a,(hl)
    cp 4
    jr nz,map_row
    ld a,(gold_flags)
    ld b,a
    ld iy,gold_positions
    ld c,8
draw_gold:
    push bc
    bit 0,b
    jr z,draw_gold_next
    ld a,5
    call pattern_address
    ld a,(iy+0)
    call overlay
draw_gold_next:
    inc iy
    pop bc
    srl b
    dec c
    jr nz,draw_gold
    ld ix,guards
    ld b,3
draw_guard:
    push bc
    ld a,(ix+1)
    or a
    ld a,8
    jr z,draw_guard_pattern
    inc a
draw_guard_pattern:
    call pattern_address
    ld a,(ix+0)
    call stamp
    ld de,3
    add ix,de
    pop bc
    djnz draw_guard
    ld a,(player_pos)
    call tile
    cp 4
    ld a,11
    jr z,draw_player_pattern
    ld a,(player_frame)
    add a,6
draw_player_pattern:
    call pattern_address
    ld a,(player_pos)
    call stamp
    ld hl,frame_buffer
    ld de,0
    ld b,120
upload:
    call pcg_pattern
    inc d
    ld a,d
    cp 4
    jp z,hud
    push de
    ld de,120
    add hl,de
    pop de
    jr upload
pattern_address:
    ld e,a
    ld d,0
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,de
    ld de,patterns
    add hl,de
    ret
stamp:
    ld (stamp_source),hl
    push af
    xor a
    ld (stamp_mode),a
    pop af
    jr stamp_common
overlay:
    ld (stamp_source),hl
    push af
    ld a,1
    ld (stamp_mode),a
    pop af
stamp_common:
    ld b,0
stamp_divide:
    cp 20
    jr c,stamp_position
    sub 20
    inc b
    jr stamp_divide
stamp_position:
    ld c,a
    ld a,(camera_y)
    ld e,a
    ld a,b
    sub e
    ret c
    cp 4
    ret nc
    add a,a
    ld e,a
    ld d,0
    ld hl,screen_rows
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld l,c
    ld h,0
    add hl,hl
    add hl,hl
    ld b,0
    add hl,bc
    add hl,de
    ex de,hl
    ld hl,(stamp_source)
    ld b,5
stamp_column:
    ld a,(stamp_mode)
    or a
    ld a,(hl)
    jr z,stamp_write
    ld c,a
    ld a,(de)
    or c
stamp_write:
    ld (de),a
    inc de
    inc hl
    djnz stamp_column
    ret
