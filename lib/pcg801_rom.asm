; FR : appels internes du profil ROM G805 ; noms historiques G801.
; EN: internal calls for the G805 ROM profile; legacy G801 names.
; Include sharp-pc-g8xx.inc first; include this file ONCE after your code.
; MIT, (c) 2026 P.RAIMBAULT. See docs/ROM_G801.md / ROM_G801_EN.md.
;
; A = pitch 0..254 (255 wraps to the longest delay), DE = repetitions,
; BC = oscillation cycles per tone. DE=0 / BC=0 produce no oscillation.
; Preserves BC, DE, HL; AF undefined (carry does NOT report BREAK).
; BREAK aborts. Blocking. Leaves bits 6/7 of port 18 low, preserves 0/1.
; Buzzer hardware must be installed. Do not use during serial/CMT transfer.
; Do not invoke from an interrupt; keep ROM bank port/shadow consistent.
; This gate returns to the trampoline's CALLER, not after the descriptor.
pcg801_rom_beep:
    call PCG801_ROM_BANK_GATE
    db PCG801_ROM_BEEP_BANK
    dw PCG801_ROM_BEEP_ADDRESS
