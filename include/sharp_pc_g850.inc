; SHARP PC-G850 family definitions, revision A. No code or data emitted.
; FR : geometrie, IOCS et ports G850 ; ne pas substituer aux defines G805.
; EN: G850 geometry, IOCS and ports; never substitute G805 ROM work areas.
; Copyright (c) 2026 P.RAIMBAULT. MIT licence.
;
; Primary references / references :
; [G800] maruhiro, g800 0.11.4, g800.h / iocs.c / io.c
; https://ver0.sakura.ne.jp/pc/g800src.0.11.4.tgz
; [MAME] pcg850v_io / sed1560_update, pce220.cpp
; https://github.com/mamedev/mame/blob/master/src/mame/sharp/pce220.cpp
; Only public IOCS contracts and hardware maps are named here. Internal
; banked firmware routines, RAM work areas, SIO and sound entry points
; require the exact model/ROM revision and are intentionally not aliased.

    IFNDEF SHARP_PC_G850_INCLUDED
    DEFINE SHARP_PC_G850_INCLUDED

PCG850_USER_ORIGIN       EQU 0x0100
PCG850_LCD_COLS          EQU 24
PCG850_LCD_ROWS          EQU 6
PCG850_CELL_WIDTH        EQU 6
PCG850_CELL_HEIGHT       EQU 8
PCG850_LCD_WIDTH         EQU 144
PCG850_LCD_HEIGHT        EQU 48
PCG850_FRAME_STRIDE      EQU 144
PCG850_FRAME_PAGES       EQU 6
PCG850_FRAME_BYTES       EQU 864
PCG850_PIXEL_MASK        EQU 0xFF
; Buffer[x + 144*(y/8)], bit y%8. Continuous pixels; six full 8-bit pages.
; The physical LCD controller has extra columns/pages for system symbols.
; Upload the visible 144 columns only; preserve firmware scrolling state.

PCG850_IOCS_KEY_SCAN     EQU 0xBE53
; Non-blocking, A=raw code, zero if none. Other flags/registers undefined.
PCG850_IOCS_KEY_WAIT     EQU 0xBCFD
; Wait for release/press, A=raw key. Main and alternate registers undefined.
PCG850_IOCS_PUTC         EQU 0xBE62
; A=printable character, D=row 0..5, E=character column 0..23.
PCG850_IOCS_PATTERN      EQU 0xBFD0
; HL=data, B=1..144 pixel columns, D=cell row 0..5, E=cell column.
; E is a CHARACTER column (six pixels), not an arbitrary pixel x.
; At E=0 use B=144. Keep 6*E+B<=144. All eight bits are visible.
; PATTERN_READ and other internal entries are deferred until a matching
; G850 firmware contract is available; do not import the G805 definition.
PCG850_IOCS_SCROLL       EQU 0xBFEB
PCG850_IOCS_REPEAT       EQU 0xBFEE
; A=character, B=character count, DE=cell; wraps without bottom scrolling.
PCG850_IOCS_STRING       EQU 0xBFF1
; HL=text, B=length (not NUL terminated), DE=cell; can wrap/scroll.

; Low-byte I/O addresses. Definitions do not authorize arbitrary writes.
PCG850_PORT_KEYS         EQU 0x10
PCG850_PORT_KEYS_LOW     EQU 0x11
PCG850_PORT_KEYS_HIGH    EQU 0x12
PCG850_PORT_SHIFT        EQU 0x13
PCG850_PORT_TIMER        EQU 0x14
PCG850_PORT_IRQ_STATE    EQU 0x16
PCG850_PORT_IRQ_MASK     EQU 0x17
PCG850_PORT_LCD_COMMAND  EQU 0x40
PCG850_PORT_LCD_DATA     EQU 0x41
PCG850_PORT_IO_WAIT      EQU 0x66
PCG850_PORT_CLOCK        EQU 0x67
PCG850_PORT_ROM_BANK     EQU 0x69
; Raw keyboard matrix: active-high, ten strobes, NOT the ASCII codes.
; G850 strobe settling differs from E200/G805. Do not reuse its delay.
; LCD commands, busy waits and contrast restoration need their own driver;
; use the PATTERN IOCS until a hardware-aware backend is available.

PCG850_KEY_NONE          EQU 0x00
PCG850_KEY_Q             EQU 0x02
PCG850_KEY_R             EQU 0x05
PCG850_KEY_Z             EQU 0x11
PCG850_KEY_X             EQU 0x12
PCG850_KEY_M             EQU 0x17
PCG850_KEY_SPACE         EQU 0x1E
PCG850_KEY_DOWN          EQU 0x1F
PCG850_KEY_UP            EQU 0x20
PCG850_KEY_LEFT          EQU 0x21
PCG850_KEY_RIGHT         EQU 0x22
PCG850_KEY_RETURN        EQU 0x28
PCG850_KEY_P             EQU 0x39
PCG850_KEY_BREAK         EQU 0x51
PCG850_KEY_MULTIPLE      EQU 0x52
PCG850_KEY_SHIFT_BIT     EQU 0x80
PCG850_KEY_BASE_MASK     EQU 0x7F
PCG850_ASCII_SPACE       EQU 0x20
PCG850_ASCII_CR          EQU 0x0D
PCG850_ASCII_LF          EQU 0x0A
PCG850_SIO_EOF           EQU 0x1A

    ASSERT PCG850_LCD_WIDTH == PCG850_LCD_COLS*PCG850_CELL_WIDTH
    ASSERT PCG850_FRAME_BYTES == PCG850_LCD_WIDTH*PCG850_LCD_ROWS
    ENDIF
