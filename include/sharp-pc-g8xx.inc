; SHARP PC-G8xx Z80 definitions, revision B (G805 ROM profile; historical G801 names)
; FR : définitions Z80, écran, clavier et IOCS ; guide dans README.md.
; EN: Z80, display, keyboard and IOCS definitions; guide in README.md#english.
; Copyright (c) 2026 P.RAIMBAULT. MIT licence, see LICENSE.txt.
; PCG801_* names are legacy API identifiers for internal G805 definitions.
; SjASMPlus syntax. This file emits NO code or data.
;
; Sources: [ROM] PC-G805 firmware profile (contracts in
; docs/ROM_G801.md / ROM_G801_EN.md). [SRC] g800 0.11.4 by Maruhiro, g800.h / iocs.c / io.c.
; https://ver0.sakura.ne.jp/pc/g800src.0.11.4.tgz
; [Z88] z88dk libsrc/target/g800/stdio/getk.asm also calls BE53h.
; https://github.com/z88dk/z88dk/tree/master/libsrc/target/g800
; [EMU] simulated IOCS contracts used by the automated checks.
; See docs/COMPATIBILITY.md for target models and memory limits.
; G850-specific RAM pointers and banked graphics calls are intentionally absent.

    IFNDEF SHARP_PC_G8XX_INCLUDED
    DEFINE SHARP_PC_G8XX_INCLUDED
    DEFINE SHARP_PC_G801_INCLUDED ; source compatibility / compatibilite

; ---- Display [SRC]: G801 belongs to g800's MACHINE_E200 family ---------
PCG_LCD_COLS        EQU 24
PCG_LCD_ROWS        EQU 4
PCG_GLYPH_WIDTH     EQU 5
PCG_GLYPH_HEIGHT    EQU 7
PCG_ROW_COLUMNS     EQU PCG_LCD_COLS * PCG_GLYPH_WIDTH ; 120 bytes
PCG_GLYPH_MASK      EQU 0x7F
; A glyph consists of five vertical columns: bit 0 = top, bit 6 = bottom.
; Bit 7 is not displayed on this family. There is no writable font ROM.
; BFD0h draws software glyphs in character cells, not persistent UDG codes.

; ---- Monitor application convention ---------------------------------
PCG_USER_ORIGIN     EQU 0x0100   ; USER reservation starts here
; USERxxxx reserves through xxxx, inclusive; include variables/buffers.
; Keep the monitor's stack. Return with RET from a monitor G command.
; G801 ROM RAM is mirrored: 78EDh aliases 18EDh on the 8 KiB model.
; [SRC] G801 RAM mirrors follow g800's MACHINE_E200 memory model.
; Firmware-specific definitions below target G805 ROM; never use G850 pointers.

; ---- Shared IOCS entries [SRC] ---------------------------------------
; D = character row (0..3), E = character column (0..23).
; Contracts below describe inputs/results; assume other registers/flags
; and alternate registers may be destroyed. Wrappers live in ../lib/.

PCG_IOCS_KEY_WAIT   EQU 0xBCFD
; Wait release / press. A = RAW key code (not ASCII).
PCG_IOCS_KEY_SCAN   EQU 0xBE53 ; [Z88] [EMU]
; Non-blocking. A = raw key code, 0 if none. Do not rely on carry/Z.
PCG_IOCS_KEY_ASCII  EQU 0xBE56
; Raw key -> ASCII; uses model/ROM-specific work area. Not used here.
PCG_IOCS_PUTC_CTRL  EQU 0xBE5F
; A = ROM glyph code, DE = cell; accepts extra glyphs below 20h.
; Does not implement CR/LF cursor motion. Font lookup selects bank 04.
PCG_IOCS_PUTC       EQU 0xBE62 ; [EMU]
; A = printable character, DE = cell. Codes <= 20h become spaces.
PCG_IOCS_PATTERN    EQU 0xBFD0 ; [EMU]
; HL -> B consecutive pixel-column bytes, DE = starting CHARACTER cell.
; B counts COLUMNS, not characters. Never cross the right edge.
; A single 5-column glyph: B=5. A full row: E=0, B=120.
; On return assume AF/BC/DE/HL destroyed (E is not a useful cursor).
PCG_IOCS_SCROLL     EQU 0xBFEB
PCG_IOCS_REPEAT     EQU 0xBFEE ; [EMU]
; Repeat A, B times, at DE; wraps, STOPS at bottom (does NOT scroll).
; B must be 1..255. BFF1h STRING, unlike REPEAT, does scroll.
PCG_IOCS_STRING     EQU 0xBFF1
; HL -> B characters, DE = cell, wraps/scrolls. NOT a zero-ended string!

; ---- Additional fixed IOCS entries [ROM: G805 ROM profile; historical names] ----------------
PCG_IOCS_PATTERN_READ EQU 0xBD00
; HL -> B-byte destination, DE = character cell, B = pixel columns (1..120).
; Same left/right split as PATTERN. Keep within the current row.
PCG_IOCS_INSERT_LINE  EQU 0xBE65
; DE = cell. Insert blank cells from E through row end, shifting rows down.
; Graphics effects depend on row; preserve the current drawing state.
PCG_IOCS_STATUS       EQU 0xBFE8
; Update LCD annunciators from ROM RAM 7901h..7904h, not the text area.
PCG_IOCS_LCD_ENABLE   EQU 0xBFD3
; Reapply start row from 790Dh and command 3Fh (display ON). No contrast.
; Initialised firmware LCD state required. AF destroyed.

; ---- Native serial, software timed, blocking [ROM: G805 ROM profile; historical names] -------
PCG_IOCS_SIO_OPEN     EQU 0xBCE8
; Initialise port 18h / enable input in 15h; preserves AF/BC.
PCG_IOCS_SIO_CLOSE    EQU 0xBCEB
; Disable input and clear port 18h; preserves AF. Not a PC-side close.
PCG_IOCS_SIO_RX       EQU 0xBCE2
; Assert RS and wait for a byte. Returns A, carry clear on success.
; Carry set: A=0 BREAK, 1 line/stop timeout, 2 parity error.
; Native CR/LF and EOF processing applies; see RAW flag below.
; BC/DE/HL preserved; alternate registers/AF undefined except result.
PCG_IOCS_SIO_RX_NEXT  EQU 0xBCE5
; Same RX path without first asserting RS. Requires an active session.
PCG_IOCS_SIO_TX       EQU 0xBFAF
; A = byte. ALWAYS waits for CS or BREAK. Carry clear=sent, set=BREAK.
; BC/DE/HL preserved; alternate registers/AF undefined except status.
PCG_IOCS_SIO_PUTS     EQU 0xBFB2
; HL -> NUL-terminated string; stops on NUL or carry, HL advances.
PCG_IOCS_SIO_NEWLINE  EQU 0xBCEE
; Append configured CR/LF at (HL), advance HL; no serial I/O, no NUL.

; ---- Internal G805 ROM RAM addresses, historical names [ROM], NOT portable G8xx ABI -----------
; [SRC] All 78xx/79xx/7Fxx addresses below alias 18xx/19xx/1Fxx on stock G801.
; Save/restore settings when used by a game. Do not clear system RAM.
PCG801_RAM_ROM_BANK   EQU 0x7900 ; shadow used by the bank-call gate
PCG801_RAM_LCD_ROW    EQU 0x790D ; current top row, modulo 8
PCG801_RAM_SIO_STATE  EQU 0x78EC ; per-reception state
PCG801_RAM_SIO_BAUD   EQU 0x78ED ; one-hot low bits: 300..9600
PCG801_RAM_SIO_FORMAT EQU 0x78EE ; bits below, retain unrelated bits
PCG801_RAM_SIO_EOF    EQU 0x78EF ; normally 1Ah
PCG801_SIO_RAW        EQU 0x10   ; STATE: bypass CR/LF translation
; RAW still updates EOF state; these calls are not a packet/file protocol.
PCG801_SIO_300        EQU 0x01
PCG801_SIO_600        EQU 0x02
PCG801_SIO_1200       EQU 0x04
PCG801_SIO_2400       EQU 0x08
PCG801_SIO_4800       EQU 0x10
PCG801_SIO_9600_ROM   EQU 0x20 ; code path exists; hardware/UI unverified
PCG801_SIO_8_BITS     EQU 0x80 ; clear = 7 bits
PCG801_SIO_PARITY     EQU 0x40 ; clear = no parity
PCG801_SIO_EVEN       EQU 0x20 ; with PARITY: set=even, clear=odd
PCG801_SIO_2_STOPS    EQU 0x10 ; clear = 1 stop
PCG801_SIO_LF         EQU 0x01 ; FORMAT newline selection
PCG801_SIO_CRLF       EQU 0x02
PCG801_SIO_CR         EQU 0x04

; ---- G805 ROM I/O ports, historical G801 names; low 8-bit address ------
PCG801_PORT_KEYS      EQU 0x10
PCG801_PORT_KEYS_LOW  EQU 0x11
PCG801_PORT_KEYS_HIGH EQU 0x12
PCG801_PORT_SHIFT     EQU 0x13
PCG801_PORT_TIMER     EQU 0x14
PCG801_PORT_IO_ENABLE EQU 0x15
PCG801_PORT_IRQ_STATE EQU 0x16
PCG801_PORT_IRQ_MASK  EQU 0x17
PCG801_PORT_IO_OUT    EQU 0x18
PCG801_PORT_ROM_BANK  EQU 0x19
PCG801_PORT_IO_IN     EQU 0x1F
PCG801_IO_IN_CS       EQU 0x02 ; ACK connector pin 9; native TX waits high
PCG801_IO_IN_RX       EQU 0x04 ; XIN connector pin 6; inverted UART
PCG801_IO_IN_BREAK    EQU 0x80
PCG801_IO_OUT_RS      EQU 0x01 ; BUSY connector pin 4
PCG801_IO_OUT_DOUT    EQU 0x02 ; DOUT connector pin 5; serial init sets high
PCG801_IO_OUT_XOUT    EQU 0x80 ; XOUT connector pin 7; inverted UART TX
PCG801_IO_BEEP_MASK   EQU 0xC0 ; native BEEP toggles BOTH bits 6 and 7
PCG801_PORT_LCD_CMD   EQU 0x58
PCG801_PORT_LCD_BUSY  EQU 0x59
PCG801_PORT_LCD_WRITE EQU 0x5A
PCG801_PORT_LCD_READ  EQU 0x5B
PCG801_LCD_BUSY       EQU 0x80
PCG801_LCD_OFF        EQU 0x3E ; display enable only, NOT analog contrast
PCG801_LCD_ON         EQU 0x3F
PCG801_LCD_X          EQU 0x40 ; OR x, 0..60
PCG801_LCD_PAGE       EQU 0xB8 ; OR page, 0..7
PCG801_LCD_START      EQU 0xC0 ; OR ((top_row & 7) << 3)
PCG801_CONTRAST_VERIFIED EQU 0 ; no contrast command identified in this ROM

; ---- Internal banked sound entry [ROM], use lib/pcg801_rom.asm ----------
PCG801_ROM_BANK_GATE    EQU 0x9249
PCG801_ROM_BEEP_BANK    EQU 1
PCG801_ROM_BEEP_ADDRESS EQU 0xE71F
; A=pitch, DE=repeat count, BC=cycles/tone. Blocking, BREAK can abort.
; Do NOT CALL E71Fh directly unless bank 1 is mapped. The supplied 6-byte
; trampoline preserves/restores the bank using the firmware shadow 7900h.
; AF undefined, BC/DE/HL preserved; no reliable carry status after cleanup.

; ---- Raw keyboard codes [SRC], NOT ASCII -----------------------------
PCG_KEY_NONE        EQU 0x00
PCG_KEY_OFF         EQU 0x01
PCG_KEY_Q           EQU 0x02
PCG_KEY_W           EQU 0x03
PCG_KEY_E           EQU 0x04
PCG_KEY_R           EQU 0x05
PCG_KEY_T           EQU 0x06
PCG_KEY_Y           EQU 0x07
PCG_KEY_U           EQU 0x08
PCG_KEY_A           EQU 0x09
PCG_KEY_S           EQU 0x0A
PCG_KEY_D           EQU 0x0B
PCG_KEY_F           EQU 0x0C
PCG_KEY_G           EQU 0x0D
PCG_KEY_H           EQU 0x0E
PCG_KEY_J           EQU 0x0F
PCG_KEY_K           EQU 0x10
PCG_KEY_Z           EQU 0x11
PCG_KEY_X           EQU 0x12
PCG_KEY_C           EQU 0x13
PCG_KEY_V           EQU 0x14
PCG_KEY_B           EQU 0x15
PCG_KEY_N           EQU 0x16
PCG_KEY_M           EQU 0x17
PCG_KEY_COMMA       EQU 0x18
PCG_KEY_BASIC       EQU 0x19
PCG_KEY_TEXT        EQU 0x1A
PCG_KEY_CAPS        EQU 0x1B
PCG_KEY_KANA        EQU 0x1C
PCG_KEY_TAB         EQU 0x1D
PCG_KEY_SPACE       EQU 0x1E
PCG_KEY_DOWN        EQU 0x1F
PCG_KEY_UP          EQU 0x20
PCG_KEY_LEFT        EQU 0x21
PCG_KEY_RIGHT       EQU 0x22
PCG_KEY_ANS         EQU 0x23
PCG_KEY_0           EQU 0x24
PCG_KEY_PERIOD      EQU 0x25
PCG_KEY_EQUAL       EQU 0x26
PCG_KEY_PLUS        EQU 0x27
PCG_KEY_RETURN      EQU 0x28
PCG_KEY_L           EQU 0x29
PCG_KEY_SEMICOLON   EQU 0x2A
PCG_KEY_1           EQU 0x2C
PCG_KEY_2           EQU 0x2D
PCG_KEY_3           EQU 0x2E
PCG_KEY_MINUS       EQU 0x2F
PCG_KEY_I           EQU 0x31
PCG_KEY_O           EQU 0x32
PCG_KEY_4           EQU 0x34
PCG_KEY_5           EQU 0x35
PCG_KEY_6           EQU 0x36
PCG_KEY_P           EQU 0x39
PCG_KEY_BACKSPACE   EQU 0x3A
PCG_KEY_7           EQU 0x3C
PCG_KEY_8           EQU 0x3D
PCG_KEY_9           EQU 0x3E
PCG_KEY_CLS         EQU 0x50
PCG_KEY_BREAK       EQU 0x51
PCG_KEY_MULTIPLE    EQU 0x52
PCG_KEY_SHIFT_BIT   EQU 0x80
PCG_KEY_BASE_MASK   EQU 0x7F

; ---- ASCII helpers --------------------------------------------------
PCG_ASCII_SPACE    EQU 0x20
PCG_ASCII_CR       EQU 0x0D
PCG_ASCII_LF       EQU 0x0A
PCG_SIO_EOF        EQU 0x1A

    ENDIF
