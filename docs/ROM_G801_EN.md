# PC-G805 firmware routines

[Français](ROM_G801.md) · **English** · [IOCS](../include/sharp-pc-g8xx.inc)

These definitions describe the **PC-G805 firmware profile**. Internal entry points are revision-specific. Legacy `PCG801_*` symbol names and the `sharp_pc_g801.inc` alias are retained for source compatibility; they do not imply identical firmware across models. No ROM is distributed.

## LCD / IOCS

D = row 0–3; E = character column 0–23. Patterns contain five seven-bit columns per character cell; B counts pixel columns. Keep patterns within a row and B ≥ 1. Conservative register-preserving wrappers are in [pcg801_runtime.asm](../lib/pcg801_runtime.asm).

| IOCS | Address | Parameters |
|---|---|---|
| `PCG_IOCS_PUTC` | BE62h | A = ASCII, DE = cell |
| `PCG_IOCS_PATTERN` | BFD0h | HL = source, B = width, DE = cell |
| `PCG_IOCS_PATTERN_READ` | BD00h | HL = destination, B = width, DE = cell |
| `PCG_IOCS_STRING` | BFF1h | HL = text, B = length, DE = cell; wraps/scrolls |
| `PCG_IOCS_REPEAT` | BFEEh | A = character, B = count, DE = cell; stops at bottom |
| `PCG_IOCS_SCROLL` | BFEBh | Scroll |
| `PCG_IOCS_STATUS` | BFE8h | Status indicators |
| `PCG_IOCS_LCD_ENABLE` | BFD3h | Display enable, command 3Fh |
| `PCG_IOCS_KEY_SCAN` | BE53h | A = raw key |

The ALL RESET animation alternates a solid-character frame with spaces and a restored pixel pattern. LCD commands 3Eh/3Fh disable/enable the display; they are not contrast controls. Games use software blinking or inversion for damage feedback. Do not apply G850 contrast commands to this controller.

## SIO

| IOCS | Address | Contract |
|---|---|---|
| `PCG_IOCS_SIO_OPEN` | BCE8h | Initialize serial I/O |
| `PCG_IOCS_SIO_CLOSE` | BCEBh | Close serial I/O |
| `PCG_IOCS_SIO_TX` | BFAFh | A = byte; wait CS; carry = BREAK |
| `PCG_IOCS_SIO_RX` | BCE2h | Assert RS, receive A; carry = error |
| `PCG_IOCS_SIO_RX_NEXT` | BCE5h | Receive without asserting RS |
| `PCG_IOCS_SIO_PUTS` | BFB2h | NUL-terminated text |
| `PCG_IOCS_SIO_NEWLINE` | BCEEh | Build line ending at HL; no transmission |

TX/RX preserve BC/DE/HL but use alternate registers. RX errors: A=0 BREAK, A=1 framing/line timeout, A=2 parity. A successful NUL byte has A=0 and carry clear. RX waits for a byte or BREAK; it is blocking. Native TX waits for CS, so keep hardware flow control enabled.

Settings reside at 78EDh (speed), 78EEh (format), 78EFh (EOF); status at 78ECh. Save and restore firmware settings around custom code. Speed masks 01/02/04/08/10h select 300/600/1200/2400/4800 baud. Format: bit 7 = 8 bits, bit 6 = parity enabled, bit 5 = even parity, bit 4 = two stops. Status bit 10h selects raw RX without CR/LF conversion. The include also names the relevant ports and RAM mirrors.

## BEEP

The bank-01 routine at E71Fh takes A=pitch delay, DE=sound count and BC=cycles per sound. Larger A means a longer period, not a higher MIDI note. BC=0 or DE=0 produces no oscillation. Use the bank-switching wrapper [pcg801_rom.asm](../lib/pcg801_rom.asm), rather than calling a banked address directly.

```asm
    INCLUDE "sharp-pc-g8xx.inc"
    ld a,7
    ld de,1
    ld bc,100
    call pcg801_rom_beep
    ; ... program return ...
    INCLUDE "pcg801_rom.asm"
```

The wrapper preserves BC/DE/HL; AF is undefined. BREAK can stop a sound but carry is cleared by cleanup. The routine toggles port 18h bits 6/7, including XOUT. It requires a fitted buzzer, must run outside interrupts and serial/cassette transfers, and assumes normal bank-mirror coherence.

[g800](https://ver0.sakura.ne.jp/pc/) · [Include](../include/sharp-pc-g8xx.inc) · [Development](DEVELOPMENT_EN.md)
