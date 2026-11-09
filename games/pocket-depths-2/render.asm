; FR: rasterisation dans 480 octets. EN: rasterisation into 480 bytes.
render:
    ld hl,frame_buffer
    ld de,frame_buffer+1
    ld bc,479
    ld (hl),0
    ldir
    xor a
    ld (ray_index),a
render_ray:
    ld a,(ray_index)
    ld e,a
    ld d,0
    ld hl,ray_offsets
    add hl,de
    ld a,(angle)
    add a,(hl)
    call cast_ray
    ld a,(ray_index)
    ld e,a
    ld d,0
    ld hl,ray_cosines
    add hl,de
    ld a,(hl)
    ld hl,(hit_distance)
    call mul_hi
    ld a,h
    or l
    jr nz,render_nonzero
    inc hl
render_nonzero:
    push hl
    ld a,(ray_index)
    add a,a
    ld e,a
    ld d,0
    ld hl,depth_buffer
    add hl,de
    pop de
    ld (hl),e
    inc hl
    ld (hl),d
    ex de,hl
    call project_height
    ld (wall_height),a
    ld b,a
    ld a,28
    sub b
    srl a
    ld (wall_top),a
    add a,b
    ld (draw_bottom),a
    ld a,(ray_index)
    ld b,a
    add a,a
    add a,b
    ld (draw_x),a
    ld a,(wall_top)
    ld (draw_y),a
wall_scan:
    ld a,(draw_y)
    ld b,a
    ld a,(draw_bottom)
    cp b
    jr z,wall_done
    ld a,(hit_tile)
    cp 2
    jr z,wall_door
    ; Perspective outlines and world-anchored brick joints.
    ld a,(wall_top)
    cp b
    jr z,wall_dark
    ld a,(draw_bottom)
    dec a
    cp b
    jr z,wall_dark
    ld a,b
    cp 13
    jr z,wall_dark
    ld a,(hit_u)
    and 127
    cp 14
    jr c,wall_dark
    ld a,(hit_side)
    or a
    jr z,wall_next
    ld a,b
    ld c,a
    ld a,(ray_index)
    xor c
    and 1
    jr z,wall_dark
    jr wall_next
wall_door:
    ; Full frame, paired panels and centre handle, not a striped wall.
    ld a,(wall_top)
    cp b
    jr z,wall_dark
    ld a,(draw_bottom)
    dec a
    cp b
    jr z,wall_dark
    ld a,(hit_u)
    cp 16
    jr c,wall_dark
    cp 240
    jr nc,wall_dark
    sub 120
    cp 16
    jr c,wall_dark
    cp 44
    jr nc,wall_next
    ld a,b
    cp 13
    jr nz,wall_next
wall_dark:
    ld a,(draw_x)
    ld c,a
    ld a,(draw_y)
    ld b,a
    call plot
wall_next:
    ld hl,draw_y
    inc (hl)
    jp wall_scan
wall_done:
    ; The 3 pixels of one ray have identical wall coverage. Duplicate the
    ; finished column by bands, instead of plotting every wall point 3x.
    ld a,(draw_x)
    ld e,a
    ld d,0
    ld hl,frame_buffer
    add hl,de
    ld b,4
    ld de,118
wall_clone:
    ld a,(hl)
    inc hl
    ld (hl),a
    inc hl
    ld (hl),a
    add hl,de
    djnz wall_clone
    ld hl,ray_index
    inc (hl)
    ld a,(hl)
    cp 40
    jp nz,render_ray
    call render_actors
    ; Minimal weapon silhouette and reticle, without covering native HUD.
    ld bc,0x0d3b
    call plot
    ld bc,0x0d3d
    call plot
    ld bc,0x0c3c
    call plot
    ld bc,0x0e3c
    call plot
    ld b,24
weapon_loop:
    push bc
    ld c,58
    call plot
    pop bc
    push bc
    ld c,62
    call plot
    pop bc
    inc b
    ld a,b
    cp 28
    jr nz,weapon_loop
    ld hl,frame_buffer
    ld de,0
    ld b,120
blit_loop:
    call pcg_pattern
    ld a,d
    inc a
    cp 4
    jr z,blit_done
    ld d,a
    push de
    ld de,120
    add hl,de
    pop de
    jr blit_loop
blit_done:
    jp hud

; B=y, C=x. All callers clip. Preserves IX/IY only.
plot:
    ld a,c
    cp 120
    ret nc
    ld a,b
    cp 28
    ret nc
    ld hl,frame_buffer
    ld de,120
plot_band:
    cp 7
    jr c,plot_bit
    sub 7
    add hl,de
    jr plot_band
plot_bit:
    ld e,c
    ld d,0
    add hl,de
    push hl
    ld e,a
    ld hl,pixel_bits
    add hl,de
    ld a,(hl)
    pop hl
    or (hl)
    ld (hl),a
    ret

; Opaque sprite background: white eyes/inner gaps remain readable.
erase:
    ld a,c
    cp 120
    ret nc
    ld a,b
    cp 28
    ret nc
    ld hl,frame_buffer
    ld de,120
erase_band:
    cp 7
    jr c,erase_bit
    sub 7
    add hl,de
    jr erase_band
erase_bit:
    ld e,c
    ld d,0
    add hl,de
    push hl
    ld e,a
    ld hl,pixel_bits
    add hl,de
    ld a,(hl)
    cpl
    pop hl
    and (hl)
    ld (hl),a
    ret

render_actors:
    ; All nine monsters/items sorted together, far to near.
    ld ix,actors
    ld iy,actor_depths
    ld b,9
    ld c,0
actor_prepare:
    push bc
    call actor_transform
    ld hl,(view_forward)
    ld (iy+0),l
    ld (iy+1),h
    pop bc
    ld hl,actor_order
    ld e,c
    ld d,0
    add hl,de
    ld (hl),c
    ld de,3
    add ix,de
    inc iy
    inc iy
    inc c
    djnz actor_prepare
    ld b,9
sort_pass:
    push bc
    ld hl,actor_order
    ld b,8
sort_pair:
    push bc
    push hl
    ld a,(hl)
    call actor_depth
    push de
    pop bc
    pop hl
    inc hl
    push hl
    ld a,(hl)
    call actor_depth
    ex de,hl
    or a
    sbc hl,bc
    pop hl
    jr c,sort_ordered
    ld a,(hl)
    dec hl
    ld c,(hl)
    ld (hl),a
    inc hl
    ld (hl),c
sort_ordered:
    pop bc
    djnz sort_pair
    pop bc
    djnz sort_pass
    xor a
    ld (draw_kind),a
actor_draw_next:
    ld a,(draw_kind)
    ld e,a
    ld d,0
    ld hl,actor_order
    add hl,de
    ld a,(hl)
    ld b,a
    add a,a
    add a,b
    ld e,a
    ld ix,actors
    add ix,de
    ld a,b
    cp 3
    jr nc,actor_object
    xor a
    ld (billboard_kind),a
    ld hl,monster_sprite
    ld (billboard_source),hl
    ld a,(ix+2)
    or a
    call nz,draw_actor
    jr actor_draw_skip
actor_object:
    ld b,(ix+0)
    ld c,(ix+1)
    call tile_at
    cp (ix+2)
    jr nz,actor_draw_skip
    sub 3
    add a,a
    ld e,a
    ld d,0
    ld hl,object_sprites
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld (billboard_source),de
    ld a,1
    ld (billboard_kind),a
    call draw_actor
actor_draw_skip:
    ld hl,draw_kind
    inc (hl)
    ld a,(hl)
    cp 9
    jr nz,actor_draw_next
    ret
actor_depth:
    add a,a
    ld e,a
    ld d,0
    ld hl,actor_depths
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ret

draw_actor:
    call actor_transform
    call actor_in_front
    ret nc
    ld hl,(view_forward)
    call project_height
    cp 3
    ret c
    ld b,a
    ld a,(billboard_kind)
    or a
    ld a,b
    jr z,sprite_monster_size
    srl a
    cp 3
    ret c
sprite_monster_size:
    ld (wall_height),a
    ld c,a
    ld a,28
    sub b
    srl a
    add a,b
    sub c
    ld (wall_top),a
    ld hl,(view_side)
    ld a,h
    and 128
    ld (transform_sign),a
    call abs_hl
    ld bc,(view_forward)
    ; Six fractional quotient bits -> horizontal position at pixel scale.
    ld de,0x0600
ratio_loop:
    add hl,hl
    or a
    sbc hl,bc
    jr nc,ratio_accept
    add hl,bc
    or a
    jr ratio_shift
ratio_accept:
    scf
ratio_shift:
    rl e
    dec d
    jr nz,ratio_loop
    ld l,e
    ld h,0
    ld d,0
    add hl,hl
    add hl,hl
    add hl,hl
    add hl,hl
    ; ratio*15/16 = lateral/forward *60 screen pixels.
    or a
    sbc hl,de
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    srl h
    rr l
    ld a,(transform_sign)
    or a
    ld a,l
    jr z,actor_right
    neg
actor_right:
    add a,60
    ld (sprite_x),a
    ld a,(wall_height)
    srl a
    inc a
    ld (sprite_width),a
    srl a
    ld b,a
    ld a,(sprite_x)
    sub b
    ld (sprite_left),a
    ; Build y->source-bit once per billboard, using an integer error
    ; accumulator. Avoid a 16-bit division for every output pixel.
    ld a,(wall_height)
    ld d,a
    ld b,a
    ld c,1
    ld hl,sprite_row_masks
    xor a
sprite_scale_row:
    ld (hl),c
    inc hl
    add a,7
sprite_scale_step:
    cp d
    jr c,sprite_scale_next
    sub d
    sla c
    jr sprite_scale_step
sprite_scale_next:
    djnz sprite_scale_row
    xor a
    ld (sprite_column),a
sprite_column_loop:
    ld a,(sprite_column)
    ld b,a
    ld a,(sprite_left)
    add a,b
    ld (draw_x),a
    cp 120
    jp nc,sprite_column_next
    ; Occlusion: a sprite column must be in front of its wall ray.
    ld l,a
    ld h,0
    ld bc,3
    call divide16
    add hl,hl
    ld de,depth_buffer
    add hl,de
    ld e,(hl)
    inc hl
    ld d,(hl)
    ld hl,(view_forward)
    or a
    sbc hl,de
    jp nc,sprite_column_next
    ; Nearest-neighbour source column = column*7 / projected width.
    ld a,(sprite_column)
    ld l,a
    ld h,0
    add hl,hl
    add hl,hl
    add hl,hl
    ld e,a
    ld d,0
    or a
    sbc hl,de
    ld a,(sprite_width)
    ld c,a
    ld b,0
    call divide16
    ld de,(billboard_source)
    add hl,de
    ld a,(hl)
    ld (sprite_bits),a
    xor a
    ld (sprite_row),a
sprite_row_loop:
    ld a,(sprite_row)
    ld e,a
    ld d,0
    ld hl,sprite_row_masks
    add hl,de
    ld a,(sprite_bits)
    and (hl)
    push af
    ld a,(sprite_row)
    ld b,a
    ld a,(wall_top)
    add a,b
    ld b,a
    ld a,(draw_x)
    ld c,a
    pop af
    jr z,sprite_white
    call plot
    jr sprite_row_next
sprite_white:
    call erase
sprite_row_next:
    ld hl,sprite_row
    inc (hl)
    ld a,(wall_height)
    cp (hl)
    jr nz,sprite_row_loop
sprite_column_next:
    ld hl,sprite_column
    inc (hl)
    ld a,(sprite_width)
    cp (hl)
    jp nz,sprite_column_loop
    ret
