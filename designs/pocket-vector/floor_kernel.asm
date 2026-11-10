; Pocket Vector: planar perspective sampling proof, NOT a complete game.
; FR/EN: real Q8.8 Z80 scanlines, 1x1 / 2x1 / 2x2, 144x32 ground plane.
; Inputs: 32/ROW_STEP [U,V,dU,dV] rows at 5000h; 128x128 1bpp map at 4000h.
; Output: 864-byte LCD page buffer at 6000h; ground occupies rows 8..39.
; The caller prepares perspective row coefficients; this kernel performs
; all per-sample coordinate stepping and texture lookup on the Z80.
; No IOCS, LCD, keyboard or bank writes; caller main/alternate regs clobbered.
; MIT, (c) 2026 P.RAIMBAULT.
    INCLUDE "sharp_pc_g850.inc"
    IFNDEF PIXEL_STEP
    DEFINE PIXEL_STEP 2
    ENDIF
    IFNDEF ROW_STEP
    DEFINE ROW_STEP 1
    ENDIF
    ASSERT PIXEL_STEP == 1 || PIXEL_STEP == 2
    ASSERT ROW_STEP == 1 || ROW_STEP == 2
MAP_DATA    EQU 0x4000
BIT_MASKS   EQU 0x4800
ROW_TABLE   EQU 0x5000
FRAME       EQU 0x6000
    ORG 0x0100
entry:
    ld hl,FRAME
    ld de,FRAME+1
    ld bc,PCG850_FRAME_BYTES-1
    ld (hl),0
    ldir
    ld hl,FRAME+PCG850_FRAME_STRIDE
    ld (band_base),hl
    ld a,(1 << ROW_STEP)-1
    ld (pixel_bit+1),a
    ld a,32/ROW_STEP
    ld (rows_left),a
    ld ix,ROW_TABLE
scanline:
    ld l,(ix+0)
    ld h,(ix+1)
    ld e,(ix+4)
    ld d,(ix+5)
    exx
    ld l,(ix+2)
    ld h,(ix+3)
    ld e,(ix+6)
    ld d,(ix+7)
    ld b,PCG850_LCD_WIDTH/PIXEL_STEP
    exx
    ld iy,(band_base)
sample:
    ; Map byte index = ((V>>8)&127)*16 + ((U>>11)&15).
    ld a,h
    rrca
    rrca
    rrca
    and 15
    ld c,a
    exx
    ld a,h
    exx
    ld b,a
    and 15
    rlca
    rlca
    rlca
    rlca
    or c
    ld c,a
    ld a,b
    rrca
    rrca
    rrca
    rrca
    and 7
    or MAP_DATA/256
    ld b,a
    ld a,(bc)
    ex af,af'
    ld a,h
    and 7
    ld c,a
    ld b,BIT_MASKS/256
    ld a,(bc)
    ld b,a
    ex af,af'
    and b
    jr z,white
    ld a,(iy+0)
pixel_bit:
    or 1
    ld (iy+0),a
    IF PIXEL_STEP == 2
    ld (iy+1),a
    ENDIF
white:
    inc iy
    IF PIXEL_STEP == 2
    inc iy
    ENDIF
    add hl,de
    exx
    add hl,de
    djnz next_sample
    exx
    ld a,(pixel_bit+1)
    rlca
    IF ROW_STEP == 2
    rlca
    ENDIF
    ld (pixel_bit+1),a
    jr nc,same_band
    ld hl,(band_base)
    ld de,PCG850_FRAME_STRIDE
    add hl,de
    ld (band_base),hl
same_band:
    ld bc,8
    add ix,bc
    ld a,(rows_left)
    dec a
    ld (rows_left),a
    jp nz,scanline
    ret
next_sample:
    exx
    jp sample
band_base: dw 0
rows_left: db 0
    ASSERT $ < 0x4000
