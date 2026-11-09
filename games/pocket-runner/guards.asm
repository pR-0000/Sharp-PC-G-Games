; FR: distances par BFS inverse, avec les memes regles que le joueur.
; EN: reverse BFS distances, using the same movement rules as the player.
; The LCD already holds the image: reuse its RAM buffer as 2x240-byte
; work arrays, then rebuild it before the next upload. No extra AI RAM.
build_distances:
    ld hl,ai_dist
    ld de,ai_dist+1
    ld bc,239
    ld (hl),255
    ldir
    xor a
    ld (bfs_head),a
    ld a,1
    ld (bfs_tail),a
    ld a,(player_pos)
    ld (ai_queue),a
    ld l,a
    ld h,0
    ld de,ai_dist
    add hl,de
    ld (hl),0
bfs_next:
    ld a,(bfs_tail)
    ld b,a
    ld a,(bfs_head)
    cp b
    ret z
    ld l,a
    ld h,0
    ld de,ai_queue
    add hl,de
    ld a,(hl)
    ld (bfs_to),a
    ld hl,bfs_head
    inc (hl)
    xor a
    ld (bfs_dir),a
bfs_neighbor:
    ld a,(bfs_dir)
    ld c,a
    ld a,(bfs_to)
    call neighbor
    jr nc,bfs_skip
    ld (bfs_from),a
    ld l,a
    ld h,0
    ld de,ai_dist
    add hl,de
    ld a,(hl)
    cp 255
    jr nz,bfs_skip
    ld a,(bfs_dir)
    xor 1
    ld c,a
    ld a,(bfs_from)
    call can_move
    jr nc,bfs_skip
    ld a,(bfs_to)
    ld l,a
    ld h,0
    ld de,ai_dist
    add hl,de
    ld a,(hl)
    inc a
    ld c,a
    ld a,(bfs_from)
    ld l,a
    ld h,0
    add hl,de
    ld (hl),c
    ld a,(bfs_tail)
    ld l,a
    ld h,0
    ld de,ai_queue
    add hl,de
    ld a,(bfs_from)
    ld (hl),a
    ld hl,bfs_tail
    inc (hl)
bfs_skip:
    ld hl,bfs_dir
    inc (hl)
    ld a,(hl)
    cp 4
    jr nz,bfs_neighbor
    jp bfs_next

guards_step:
    ld ix,guards
    ld b,3
guard_next:
    push bc
    ld a,(ix+1)
    or a
    jr z,guard_free
    dec (ix+1)
    jp nz,guard_done
    ld a,(ix+0)
    ld c,2
    call neighbor
    jr nc,guard_wait
    ld (guard_target),a
    call guard_cell_free
    jr nc,guard_wait
    ld a,(guard_target)
    call tile
    cp 1
    jr z,guard_wait
    cp 2
    jr z,guard_wait
    ld a,(guard_target)
    ld (ix+0),a
    jr guard_done
guard_wait:
    ld (ix+1),1
    jr guard_done
guard_free:
    ld a,(ix+0)
    call supported
    jr c,guard_choose
    ld a,(ix+0)
    ld c,3
    call can_move
    jr nc,guard_done
    call guard_cell_free
    jr nc,guard_done
    ld (ix+0),a
    jr guard_check_hole
guard_choose:
    ld a,(ix+0)
    ld (guard_target),a
    ld l,a
    ld h,0
    ld de,ai_dist
    add hl,de
    ld a,(hl)
    ld (guard_best),a
    xor a
    ld (guard_dir),a
guard_try:
    ld a,(guard_dir)
    ld c,a
    ld a,(ix+0)
    call can_move
    jr nc,guard_skip
    call guard_cell_free
    jr nc,guard_skip
    ld b,a
    ld l,a
    ld h,0
    ld de,ai_dist
    add hl,de
    ld a,(guard_best)
    cp (hl)
    jr c,guard_skip
    jr z,guard_skip
    ld a,(hl)
    ld (guard_best),a
    ld a,b
    ld (guard_target),a
guard_skip:
    ld hl,guard_dir
    inc (hl)
    ld a,(hl)
    cp 4
    jr nz,guard_try
    ld a,(guard_target)
    ld (ix+0),a
guard_check_hole:
    ld a,(ix+0)
    call hole_at
    jr nc,guard_done
    ld (ix+1),TRAP_TIME
guard_done:
    ld de,3
    add ix,de
    pop bc
    dec b
    jp nz,guard_next
    ret

; Avoid merging guards into one cell; BFS ignores temporary occupancy,
; but actual movement waits or chooses another route. IX preserved.
guard_cell_free:
    push bc
    push de
    push iy
    ld e,a
    ld iy,guards
    ld b,3
guard_cell_test:
    cp (iy+0)
    jr nz,guard_cell_next
    cp (ix+0)
    jr nz,guard_cell_blocked
guard_cell_next:
    ld de,3
    add iy,de
    djnz guard_cell_test
    scf
    jr guard_cell_return
guard_cell_blocked:
    or a
guard_cell_return:
    pop iy
    pop de
    pop bc
    ret

; A blocked spawn must not merge two guards. Search that spawn's row.
respawn_guard:
    push bc
    ld a,(ix+2)
    ld b,a
respawn_column:
    cp 20
    jr c,respawn_row
    sub 20
    jr respawn_column
respawn_row:
    ld c,a
    ld a,b
    sub c
    ld (spawn_row),a
    ld a,(ix+2)
    ld b,20
respawn_search:
    ld (spawn_try),a
    call tile
    cp 1
    jr z,respawn_next
    cp 2
    jr z,respawn_next
    ld a,(spawn_try)
    call guard_cell_free
    jr c,respawn_found
respawn_next:
    ld a,(spawn_try)
    inc a
    ld c,a
    ld a,(spawn_row)
    add a,20
    cp c
    ld a,c
    jr nz,respawn_continue
    ld a,(spawn_row)
respawn_continue:
    djnz respawn_search
    ; Valid levels have at most three guards in a row of >=16 free cells.
respawn_found:
    ld (ix+0),a
    ld (ix+1),0
    pop bc
    ret
