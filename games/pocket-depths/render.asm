; FR: 40 rayons, bandes de trois colonnes, occlusion des sprites.
; EN: forty rays, three-pixel strips, sprite depth clipping.
render:
    ld hl,frames
    inc (hl)
    jr nz,.counted
    inc hl
    inc (hl)
.counted:
    call update_player_index
    xor a
    ld hl,screen_buffer
    ld (hl),a
    ld de,screen_buffer+1
    ld bc,PCG_FRAME_BYTES-1
    ldir
    IF !BUILD_LITE
    ld hl,floor_background
    ld de,screen_buffer+VIEW_WIDTH*2
    ld bc,VIEW_WIDTH*(VIEW_ROWS-2)
    ldir
    ENDIF
    xor a
    ld (current_ray),a
.ray:
    ld a,(current_ray)
    cp HALF_RAYS
    jr nc,.right
    ld b,a
    ld a,HALF_RAYS-1
    sub b
    jr .directory
.right:
    sub HALF_RAYS
.directory:
    add a,a
    ld c,a
    ld b,0
    ld hl,ray_directory
    add hl,bc
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
.walk:
    ld a,(hl)
    cp 255
    jr z,.horizon
    ld c,a
    ld b,0
    inc hl
    ld a,(hl)
    ld (ray_visual),a
    inc hl
    push hl
    call ray_offset
    ld a,(player_index)
    add a,b
    call map_get
    ld (hit_kind),a
    call is_solid
    pop hl
    or a
    jr z,.walk
    ld a,(ray_visual)
    and 63
    jr .depth
.horizon:
    xor a
    ld (hit_kind),a
    ld a,63
.depth:
    ld b,a
    ld a,(current_ray)
    ld c,a
    ld a,b
    ld b,0
    ld hl,ray_depths
    add hl,bc
    ld (hl),a
    ld l,a
    ld h,0
    add hl,hl
    IF TARGET_G850
    push hl
    ENDIF
    add hl,hl
    add hl,hl
    IF TARGET_G850
    pop de
    add hl,de
    ENDIF
    ld de,wall_profiles
    add hl,de
    ld (profile_pointer),hl
    ld a,(hit_kind)
    or a
    jr z,.next_ray
    call paint_wall
.next_ray:
    ld hl,current_ray
    inc (hl)
    ld a,(hl)
    cp RAY_COUNT
    jp c,.ray

    ld a,7
    ld (entity_depth),a
.entity_layer:
    ld hl,objects
.object:
    ld d,(hl)
    inc hl
    ld a,d
    cp 255
    jr z,.monsters
    ld e,(hl)
    inc hl
    push hl
    ld a,e
    rlca
    rlca
    rlca
    rlca
    or d
    call map_get
    cp VIEW_ROWS
    jr c,.skip_object
    cp 9
    jr nc,.skip_object
    sub 2
    ld (sprite_kind),a
    call render_entity
.skip_object:
    pop hl
    jr .object
.monsters:
    ld ix,enemies
    ld a,4
    ld (actor_count),a
.monster:
    ld a,(ix+3)
    or a
    jr z,.next_monster
    ld d,(ix+0)
    ld e,(ix+1)
    ld a,(ix+2)
    ld (sprite_kind),a
    call render_entity
    ld a,(ix+4)
    or a
    jr z,.next_monster
    ld a,(sprite_visible)
    or a
    jr z,.next_monster
    ld a,(sprite_center)
    push af
    call depth_at_x
    ld b,a
    ld a,(sprite_depth)
    cp b
    pop de
    jr nc,.next_monster
    ld c,d
    ld b,0
    ld hl,screen_buffer
    add hl,bc
    ld a,(hl)
    or $17
    ld (hl),a
.next_monster:
    ld de,5
    add ix,de
    ld hl,actor_count
    dec (hl)
    jr nz,.monster
    ld hl,entity_depth
    dec (hl)
    jp nz,.entity_layer

    ; Reticle at logical (60,12), weapon at the bottom centre.
    ld hl,screen_buffer+VIEW_WIDTH*(1+TARGET_G850)+VIEW_WIDTH/2
    ld a,(hl)
    or $70
    ld (hl),a
    dec hl
    ld a,(hl)
    or $20
    ld (hl),a
    inc hl
    inc hl
    ld a,(hl)
    or $20
    ld (hl),a
    ld a,(hurt_flash)
    or a
    call nz,invert_buffer
    call blit_buffer
    call draw_hud
    ld a,(hurt_flash)
    or a
    ret z
    xor a
    ld (hurt_flash),a
    call hide_heart
    call damage_wait
    call invert_buffer
    call blit_buffer
    call draw_hud
    call damage_wait
    call hide_heart
    call damage_wait
    ld hl,heart_glyph
    ld de,HUD_ROW*256
    jp pcg_glyph

; FR: deux clignotements du coeur, chiffres des PV toujours lisibles.
; EN: two heart blinks; health digits remain visible. No LCD commands.
hide_heart:
    ld a,' '
    ld de,HUD_ROW*256
    jp pcg_putc

damage_wait:
    push bc
    ld bc,18000*(1+TARGET_G850)                 ; ~117 ms at 4 MHz; hardware timing pending
.flash_wait:
    dec bc
    ld a,b
    or c
    jr nz,.flash_wait
    pop bc
    ret

invert_buffer:
    ld hl,screen_buffer
    ld bc,PCG_FRAME_BYTES
.loop:
    ld a,(hl)
    xor PCG_GLYPH_MASK
    ld (hl),a
    inc hl
    dec bc
    ld a,b
    or c
    jr nz,.loop
    ret

blit_buffer:
    ld hl,screen_buffer
    ld de,0
.display_row:
    ld b,VIEW_WIDTH
    call pcg_pattern
    ld bc,VIEW_WIDTH
    add hl,bc
    inc d
    ld a,d
    cp VIEW_ROWS
    jr c,.display_row
    ret

; C=forward*8+unsigned lateral -> B=signed map offset.
; Arithmetic replaces a 512-byte orientation/mirror table.
ray_offset:
    ld a,c
    and 7
    ld d,a
    ld a,(current_ray)
    cp HALF_RAYS
    jr nc,.positive
    xor a
    sub d
    ld d,a
.positive:
    ld a,c
    and $38
    add a,a
    ld e,a
    ld a,(direction)
    and 1
    jr nz,.odd
    ld a,d
    sub e
    jr .base
.odd:
    ld a,d
    rlca
    rlca
    rlca
    rlca
    and $F0
    ld b,a
    ld a,c
    srl a
    srl a
    srl a
    add a,b
.base:
    ld b,a
    ld a,(direction)
    and 2
    ret z
    xor a
    sub b
    ld b,a
    ret

paint_wall:
    ld a,(current_ray)
    ld b,a
    add a,a
    add a,b
    ld e,a
    ld d,0
    ld hl,screen_buffer
    add hl,de
    ld (write_pointer),hl
    ld a,VIEW_ROWS
    ld (row_count),a
.row:
    ld hl,(profile_pointer)
    ld b,(hl)                   ; opaque fill mask
    inc hl
    ld c,(hl)                   ; outlines and horizontal joints
    inc hl
    ld (profile_pointer),hl
    ld a,b
    cpl
    ld d,a                      ; preserve background outside wall
    ld a,(ray_visual)
    and $80
    ld a,c
    jr z,.left_ready
    ld a,b
.left_ready:
    ld e,a
    ld a,(hit_kind)
    cp 2
    jr z,.pillar
    cp 3
    jr z,.door
    cp 9
    jr z,.door
    jr .left
.pillar:
    ld e,b
    jr .left
.door:
    ; Continuous lintel/sill: strip the brick joints from C. Compare the
    ; adjacent seven-bit rows so the frame has no false horizontal seams.
    ld a,b
    add a,a
    cpl
    and b
    ld e,a
    ld a,(row_count)
    cp VIEW_ROWS
    jr z,.door_top
    ld hl,(profile_pointer)
    dec hl
    dec hl
    dec hl
    dec hl
    bit PCG_GLYPH_HEIGHT-1,(hl)
    jr z,.door_top
    res 0,e
.door_top:
    ld a,b
    srl a
    cpl
    and b
    or e
    ld c,a
    ld a,(row_count)
    cp 1
    jr z,.door_bottom
    ld hl,(profile_pointer)
    bit 0,(hl)
    jr z,.door_bottom
    res PCG_GLYPH_HEIGHT-1,c
.door_bottom:
    ld e,c
    ld a,(ray_visual)
    and $C0
    jr z,.left
    ld e,b                      ; vertical jamb or central leaf separation
.left:
    ld hl,(write_pointer)
    ld a,(hl)
    and d
    or e
    ld (hl),a
    inc hl
    ld e,c
    ld a,(hit_kind)
    cp 3
    jr z,.door_handle
    cp 9
    jr z,.door_handle
    ld a,b
    and $22
    or c
    ld e,a
    jr .middle
.door_handle:
    ld a,(ray_visual)
    and $40
    jr z,.middle
    ld a,(row_count)
    cp VIEW_ROWS-2
    jr nz,.middle
    ld a,b
    and 3                       ; handle next to the centre join, y=14..15
    or c
    ld e,a
.middle:
    ld a,(hl)
    and d
    or e
    ld (hl),a
    inc hl
    ld a,(hl)
    and d
    or c
    ld (hl),a
    ld hl,(write_pointer)
    ld de,VIEW_WIDTH
    add hl,de
    ld (write_pointer),hl
    ld hl,row_count
    dec (hl)
    jp nz,.row
    ret

; Sprite already selected, D/E world position. Draw only this depth layer.
render_entity:
    xor a
    ld (sprite_visible),a
    call relative_position
    ld a,(entity_depth)
    cp e
    ret nz
    ld a,e
    add a,a
    add a,a
    add a,a
    ld (sprite_depth),a
    call project_x
    cp VIEW_WIDTH
    ret nc
    ld (sprite_center),a
    ld a,e
    dec a
    jr z,.scale_zero
    dec a
    jr z,.scale_one
    cp 3
    jr c,.scale_two
    ld c,3
    jr .select
.scale_zero:
    ld c,0
    jr .select
.scale_one:
    ld c,1
    jr .select
.scale_two:
    ld c,2
.select:
    ld a,(sprite_kind)
    add a,a
    add a,a
    add a,c
    add a,a
    ld c,a
    ld b,0
    ld hl,sprite_directory
    add hl,bc
    ld e,(hl)
    inc hl
    ld d,(hl)
    ex de,hl
    ld a,(hl)
    inc hl
    ld (sprite_width),a
    srl a
    ld b,a
    ld a,(sprite_center)
    sub b
    ld (sprite_left),a
    ld a,(hl)
    inc hl
    ld de,screen_buffer
    or a
    jr z,.first_band
.band_offset:
    ex de,hl
    ld bc,VIEW_WIDTH
    add hl,bc
    ex de,hl
    dec a
    jr nz,.band_offset
.first_band:
    ld (sprite_row),de
    ld a,(hl)
    inc hl
    ld (row_count),a
    ld (sprite_source),hl
.row:
    ld a,(sprite_width)
    ld (sprite_columns),a
    ld a,(sprite_left)
    ld (sprite_x),a
.column:
    ld hl,(sprite_source)
    ld d,(hl)                   ; mask
    inc hl
    ld e,(hl)                   ; ink
    inc hl
    ld (sprite_source),hl
    ld a,(sprite_x)
    cp VIEW_WIDTH
    jr nc,.skip
    push de
    call depth_at_x
    ld b,a
    ld a,(sprite_depth)
    cp b
    pop de
    jr nc,.skip
    ld a,(sprite_x)
    ld c,a
    ld b,0
    ld hl,(sprite_row)
    add hl,bc
    ld a,d
    cpl
    and (hl)
    or e
    ld (hl),a
    ld a,e
    or a
    jr z,.skip
    ld a,1
    ld (sprite_visible),a
.skip:
    ld hl,sprite_x
    inc (hl)
    ld hl,sprite_columns
    dec (hl)
    jr nz,.column
    ld hl,(sprite_row)
    ld de,VIEW_WIDTH
    add hl,de
    ld (sprite_row),hl
    ld hl,row_count
    dec (hl)
    jr nz,.row
    ret
