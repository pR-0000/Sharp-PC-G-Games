; FR: niveau modulaire G805; carte fixe compacte G801 Lite.
; EN: modular G805 level; compact fixed map for G801 Lite.
load_level:
    IF BUILD_LITE
    ld hl,map_packed
    ld de,world
    ld b,128
.unpack:
    ld a,(hl)
    and 15
    ld (de),a
    inc de
    ld a,(hl)
    rrca
    rrca
    rrca
    rrca
    and 15
    ld (de),a
    inc de
    inc hl
    djnz .unpack
    ret
    ELSE
    ld a,1
    ld hl,world
    ld (hl),a
    ld de,world+1
    ld bc,255
    ldir
    ld a,(level_seed)
    ld (random_state),a
    ld hl,chunk_positions
    ld a,4
    ld (chunks_left),a
.chunk:
    ld e,(hl)
    inc hl
    ld d,(hl)
    inc hl
    push hl
    push de
    call level_random
    call level_random
    and 3
    ld b,a
    add a,a
    add a,b
    add a,a
    add a,a
    add a,b
    add a,b                    ; kind * 14
    ld c,a
    ld b,0
    ld hl,chunk_shapes
    add hl,bc
    pop ix
    ld a,7
    ld (level_rows),a
.row:
    ld c,(hl)
    inc hl
    ld b,(hl)
    inc hl
    ld a,7
    ld (level_columns),a
.cell:
    xor a
    rrc c
    jr nc,.floor
    inc a
.floor:
    rrc b
    jr nc,.store
    ld a,2
.store:
    ld (ix+0),a
    inc ix
    ld a,(level_columns)
    dec a
    ld (level_columns),a
    jr nz,.cell
    ld de,9
    add ix,de
    ld a,(level_rows)
    dec a
    ld (level_rows),a
    jr nz,.row
    pop hl
    ld a,(chunks_left)
    dec a
    ld (chunks_left),a
    jr nz,.chunk
    ld hl,level_items
.item:
    ld a,(hl)
    inc hl
    cp 255
    ret z
    ld e,(hl)
    inc hl
    push hl
    call map_address
    ld (hl),e
    pop hl
    jr .item
    ENDIF

    IF !BUILD_LITE
level_random:
    ld a,(random_state)
    srl a
    jr nc,.store
    xor $B8
.store:
    ld (random_state),a
    ret

another_level:
    ld a,(entropy)
    ld b,a
    ld a,(level_seed)
    xor b
    or a
    jr nz,.seed
    inc a
.seed:
    ld (random_state),a
    call level_random
    ld (level_seed),a
    ld (campaign_seed),a
    jp main_new
    ENDIF
