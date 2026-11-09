; SHARP PC-G80X QUEST - port of Canon X-07 Quest.
; FR : chargement et lancement confirmes sur PC-G801 et PC-G805.
; EN: loading and startup reported on physical PC-G801 and PC-G805.
; See NOTICE.md for provenance. No Canon ROM, IO ports or sound driver.
    INCLUDE "sharp_pc_g801.inc"
    IFNDEF BUILD_LANG_EN
BUILD_LANG_EN EQU 0
    ENDIF
    IF BUILD_LANG_EN
HUD_HP EQU 'H'
HUD_LEVEL EQU 'L'
HUD_GOLD EQU 'G'
    ELSE
HUD_HP EQU 'V'
HUD_LEVEL EQU 'N'
HUD_GOLD EQU 'O'
    ENDIF
    ORG PCG_USER_ORIGIN

WORLD_W_TILES EQU 30
WORLD_H_TILES EQU 16
CHUNK_W_TILES EQU 15
CHUNK_H_TILES EQU 4
CHUNKS_X EQU 2
CHUNKS_Y EQU 4
; Keep original VIRTUAL coordinates for the game rules, not LCD pixels.
STEP_X EQU 8
STEP_Y EQU 8
SCREEN_WIDTH_PIXELS EQU 120
SCREEN_HEIGHT_PIXELS EQU 32
HOME_CHUNK_X EQU 0
HOME_CHUNK_Y EQU 3
HOME_PLAYER_X EQU 5*STEP_X
HOME_PLAYER_Y EQU 1*STEP_Y
    IFNDEF TYPING_TICK_RELOAD
TYPING_TICK_RELOAD EQU 6         ; FR: delai +20 % environ / EN: about 20% more time
    ENDIF
    ASSERT TYPING_TICK_RELOAD >= 1 && TYPING_TICK_RELOAD <= 64
MAX_LEVEL EQU 99
TYPING_RESULT_MISS EQU 0
TYPING_RESULT_NORMAL EQU 1
TYPING_RESULT_AMP EQU 2
BATTLE_OUTCOME_NONE EQU 0
BATTLE_OUTCOME_WIN EQU 1
BATTLE_OUTCOME_FLEE EQU 2
BATTLE_OUTCOME_LOSE EQU 3
EVENT_FLAG_BOSS_CEMETERY EQU 1
EVENT_FLAG_BOSS_FOREST EQU 2
EVENT_FLAG_BOSS_RUINS EQU 4
EVENT_FLAG_BOSS_OASIS EQU 8
EVENT_FLAG_BOSS_TOWER EQU 16
TILE_CASTLE_LEFT EQU 2
TILE_CASTLE_RIGHT EQU 3
SAVE_MAGIC_VALUE EQU 0xA7
DEBUG_SKIP_RANDOM_BATTLES EQU 0
DEBUG_IMMORTAL EQU 0
DEBUG_INITIAL_FLAGS EQU 0
DEBUG_INITIAL_LEVEL EQU 1
DEBUG_INITIAL_GOLD EQU 10
DEBUG_SKIP_INTRO EQU 0
INTRO_TEXT_PTR EQU intro_text
; ASCII transliteration: Canon font byte values are not Sharp character codes.
CHAR_E_DIAERESIS EQU 'e'
CHAR_E_GRAVE EQU 'e'
CHAR_E_CIRC EQU 'e'
CHAR_E_ACUTE EQU 'e'
CHAR_E_CAPITAL_ACUTE EQU 'E'
CHAR_A_GRAVE EQU 'a'
CHAR_A_CIRC EQU 'a'
CHAR_C_CAPITAL_CEDILLA EQU 'C'
CHAR_C_CEDILLA EQU 'c'

entry:
start:
    push ix
    push iy
    ld (saved_return_sp),sp
    xor a
    ld (key_last),a
    call pcg_clear
    ld hl,title_text
    ld de,0x0401
    ld (cursor_xy),de
    call quest_puts
    call menu_set_cancel_none
    ld hl,menu_title
    call menu_vertical
    or a
    jp nz,quit
    call game_begin_from_title
    call world_redraw_map_with_player
main:
    call quest_read_key
    cp PCG_KEY_Q
    jp z,quit
    cp PCG_KEY_M
    jr z,.status
    cp PCG_KEY_TAB
    jr z,.status
    xor a
    ld (moved),a
    ld a,(key_last)
    cp PCG_KEY_LEFT
    jr z,.left
    cp PCG_KEY_RIGHT
    jr z,.right
    cp PCG_KEY_UP
    jr z,.up
    cp PCG_KEY_DOWN
    jr nz,main
    call move_down_chunk
    jr .after
.left:
    call move_left_chunk
    jr .after
.right:
    call move_right_chunk
    jr .after
.up:
    call move_up_chunk
.after:
    ld a,(moved)
    or a
    jr z,main
    call check_tile_event
    or a
    jr nz,main
    call check_random_battle
    jr main
.status:
    call world_show_status_menu
    jr main

quit:
    ld sp,(saved_return_sp)      ; unwind menus, keep entry's monitor stack
    pop iy
    pop ix
    ret

title_menu_continue:
    xor a
    ret
title_menu_new:
    xor a
    ld (save_magic),a
    ret
title_menu_quit:
    ld a,1
    ret

    INCLUDE "movement.inc"
    INCLUDE "events.inc"
    INCLUDE "progression.inc"
    INCLUDE "typing.inc"
    INCLUDE "battle.inc"
    INCLUDE "menu.asm"
    INCLUDE "display.asm"
    INCLUDE "platform.asm"
    INCLUDE "save.inc"
    DEFINE PCG_RUNTIME_NO_PUTS
    INCLUDE "../../lib/pcg801_runtime.asm"

data_start:
    INCLUDE "tiles.inc"
    INCLUDE "map_packed.inc"
    INCLUDE "data.inc"
title_text: db "SHARP PC-G80X QUEST",0
menu_title:
    db 3
    dw title_menu_continue,title_menu_new,title_menu_quit
    IF BUILD_LANG_EN
    db 7,2,"Continue",0,7,3,"New game",0,7,4,"Quit",0
    ELSE
    db 7,2,"Continuer",0,7,3,"Nouvelle partie",0,7,4,"Quitter",0
    ENDIF
decimal_powers: dw 10000,1000,100,10,1
raw_ascii:
    db 0,0,'Q','W','E','R','T','Y','U','A','S','D','F','G','H','J'
    db 'K','Z','X','C','V','B','N','M',',',0,0,0,0,0,' ',0
    db 0,0,0,0,'0','.','=','+',13,'L',';',0,'1','2','3','-'
    db 0,'I','O',0,'4','5','6','*',0,'P',8,0,'7','8','9','/'
    INCLUDE "state.asm"
program_end:
    ASSERT program_end <= 0x17E3 ; conservative G801 loader limit, inclusive 17E2
