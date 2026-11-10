; Q8.8 positions and DDA distances; angle wraps at 256 (E,S,W,N).
; FR: tous les pas du DDA sont calcules ici. EN: all DDA steps run here.
cast_ray:
    ld (ray_angle),a
    ld a,(player_x+1)
    ld (map_x),a
    ld a,(player_y+1)
    ld (map_y),a
    ld a,(player_x)
    ld e,a
    ld a,(ray_angle)
    add a,64
    call setup_axis
    ld (delta_x),bc
    ld (side_x),hl
    ld a,d
    ld (step_x),a
    ld a,(player_y)
    ld e,a
    ld a,(ray_angle)
    call setup_axis
    ld (delta_y),bc
    ld (side_y),hl
    ld a,d
    ld (step_y),a
    ld a,40
    ld (ray_budget),a
cast_loop:
    call dda_step
    ld a,(map_x)
    ld b,a
    ld a,(map_y)
    ld c,a
    call tile_at
    cp 1
    jr z,cast_hit
    cp 2
    jr z,cast_hit
    ld hl,ray_budget
    dec (hl)
    jr nz,cast_loop
    ld a,1
cast_hit:
    ld (hit_tile),a
    ; Texture position follows the intersected wall, not the screen column.
    ld a,(hit_side)
    or a
    ld a,(ray_angle)
    ld de,(player_y)
    jr z,cast_texture
    add a,64
    ld de,(player_x)
cast_texture:
    push de
    ld hl,(hit_distance)
    call signed_term
    pop de
    add hl,de
    ld a,l
    ld (hit_u),a
    ret

; E fractional origin, A sine phase. BC delta, HL initial side, D step.
setup_axis:
    ld c,a
    ld d,1
    bit 7,a
    jr z,setup_sign
    ld d,255
setup_sign:
    and 63
    bit 6,c
    jr z,setup_index
    neg
    add a,64
setup_index:
    or a
    jr z,axis_zero
    push de
    add a,a
    ld e,a
    ld d,0
    ld hl,delta_quarter
    add hl,de
    ld c,(hl)
    inc hl
    ld b,(hl)
    pop de
axis_distance:
    ld a,e
    bit 7,d
    jr nz,axis_fraction
    neg
    jr nz,axis_fraction
    ld h,b
    ld l,c
    ret
axis_fraction:
    push bc
    push de
    ld h,b
    ld l,c
    call mul_hi
    pop de
    pop bc
    ret
axis_zero:
    ld bc,0x7fff
    ld h,b
    ld l,c
    ret

; HL * A >> 8, unsigned 24-bit intermediate; no overflow truncation.
mul_hi:
    ex de,hl
    ld hl,0
    ld bc,0x0800
mul_loop:
    add hl,hl
    rl c
    add a,a
    jr nc,mul_next
    add hl,de
    jr nc,mul_next
    inc c
mul_next:
    djnz mul_loop
    ld l,h
    ld h,c
    ret

; One runtime grid crossing. Equal distances consistently choose Y.
dda_step:
    ld hl,(side_x)
    ld de,(side_y)
    or a
    sbc hl,de
    jr c,dda_x
    ld hl,(side_y)
    ld (hit_distance),hl
    ld de,(delta_y)
    call saturated_add
    ld (side_y),hl
    ld a,(step_y)
    ld hl,map_y
    add a,(hl)
    ld (hl),a
    ld a,1
    ld (hit_side),a
    ret
dda_x:
    ld hl,(side_x)
    ld (hit_distance),hl
    ld de,(delta_x)
    call saturated_add
    ld (side_x),hl
    ld a,(step_x)
    ld hl,map_x
    add a,(hl)
    ld (hl),a
    xor a
    ld (hit_side),a
    ret
saturated_add:
    add hl,de
    bit 7,h
    ret z
    ld hl,0x7fff
    ret

; Unsigned HL / BC -> HL quotient, DE remainder. BC !=0.
divide16:
    ld de,0
    ld a,16
divide_loop:
    add hl,hl
    rl e
    rl d
    ex de,hl
    or a
    sbc hl,bc
    jr nc,divide_accept
    add hl,bc
    ex de,hl
    jr divide_next
divide_accept:
    ex de,hl
    inc l
divide_next:
    dec a
    jr nz,divide_loop
    ret
abs_hl:
    bit 7,h
    ret z
neg_hl:
    xor a
    sub l
    ld l,a
    sbc a,a
    sub h
    ld h,a
    ret

; Actor -> signed camera-space forward/side in Q8.8. IX preserved.
actor_transform:
    ld h,(ix+0)
    ld l,128
    ld de,(player_x)
    or a
    sbc hl,de
    ld (actor_dx),hl
    ld h,(ix+1)
    ld l,128
    ld de,(player_y)
    or a
    sbc hl,de
    ld (actor_dy),hl
    ld hl,(actor_dx)
    ld a,(angle)
    add a,64
    call signed_term
    push hl
    ld hl,(actor_dy)
    ld a,(angle)
    call signed_term
    pop de
    add hl,de
    ld (view_forward),hl
    ld hl,(actor_dx)
    ld a,(angle)
    call signed_term
    push hl
    ld hl,(actor_dy)
    ld a,(angle)
    add a,64
    call signed_term
    pop de
    or a
    sbc hl,de
    ld (view_side),hl
    ret
signed_term:
    push hl
    call trig
    ld e,a
    pop hl
    ld a,h
    xor e
    and 128
    ld (transform_sign),a
    ld a,e
    or a
    jp p,term_positive
    neg
term_positive:
    add a,a
    push af
    call abs_hl
    pop af
    call mul_hi
    ld a,(transform_sign)
    or a
    ret z
    jp neg_hl
actor_in_front:
    ld hl,(view_forward)
    bit 7,h
    jr nz,actor_out
    ld de,32
    or a
    sbc hl,de
    jr c,actor_out
    ld hl,(view_side)
    call abs_hl
    ld de,(view_forward)
    or a
    sbc hl,de
    ret
actor_out:
    or a
    ret

; Exact segment direction (not camera angle). Q8.8 segment parameter.
; Floor division of reciprocals <=1/256 t; both end cells are tested.
line_of_sight:
    ld a,(player_x+1)
    ld (map_x),a
    ld a,(player_y+1)
    ld (map_y),a
    ld hl,(actor_dx)
    ld a,(player_x)
    ld e,a
    call segment_axis
    ld (side_x),hl
    ld (delta_x),bc
    ld a,d
    ld (step_x),a
    ld hl,(actor_dy)
    ld a,(player_y)
    ld e,a
    call segment_axis
    ld (side_y),hl
    ld (delta_y),bc
    ld a,d
    ld (step_y),a
    ld a,40
    ld (ray_budget),a
los_loop:
    ld a,(map_x)
    cp (ix+0)
    jr nz,los_step
    ld a,(map_y)
    cp (ix+1)
    jr z,los_clear
los_step:
    call dda_step
    ld a,(map_x)
    ld b,a
    ld a,(map_y)
    ld c,a
    call tile_at
    cp 1
    jr z,actor_out
    cp 2
    jr z,actor_out
    ld hl,ray_budget
    dec (hl)
    jr nz,los_loop
    or a
    ret
los_clear:
    scf
    ret
segment_axis:
    ld d,1
    bit 7,h
    jr z,segment_positive
    ld d,255
segment_positive:
    call abs_hl
    ld a,h
    or l
    jp z,axis_zero
    push de
    ld b,h
    ld c,l
    ld hl,65535
    call divide16
    bit 7,h
    jr z,segment_small
    ld hl,0x7fff
segment_small:
    ld b,h
    ld c,l
    pop de
    jp axis_distance

; Focal length = 60 pixels (90 degree horizontal FOV), wall height 1 cell.
; HL perpendicular distance -> A projected height = min(28,15360/d).
project_height:
    ld a,h
    or l
    jr z,project_near
    ld b,h
    ld c,l
    ld hl,PROJECTION_SCALE
    xor a
height_loop:
    or a
    sbc hl,bc
    ret c
    inc a
    cp VIEW_H
    jr c,height_loop
project_near:
    ld a,VIEW_H
    ret
