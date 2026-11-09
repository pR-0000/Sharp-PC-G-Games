# Starting machine code from BASIC

[Français](BASIC_CALL.md) · **English** · [Loading](LOADING_EN.md)

This Sharp family uses **CALL address**. For games assembled at 0100h:

```text
CALL &H100
```

`CALL 256` is the same address in decimal. Reserve USER memory and load the code through MON → R first. Return to BASIC RUN without resetting memory, then call it. CALL starts resident code; it does not load a file. Do not transfer the Canon X-07 EXEC command to this platform.

A short BASIC launcher also works when enough BASIC RAM remains:

```basic
10 CALL &H100
20 END
```

[Transfer example](../examples/run_machine_code.bas). Prefer the direct command when Quest nearly fills an 8 KB G801. USER must reserve code, state and buffers.

Machine code must keep a valid caller stack and return with RET. Pocket Depths also preserves BC, DE, HL, IX and IY. MON's G100 and BASIC's CALL &H100 use the same entry point; exiting returns to the caller used.

Reference: [fu-sen PC-E200/G CALL documentation](https://github.com/fu-sen/SHARP-POCKET-COMPUTER-BASIC/blob/master/CALL.txt). Use each game's manifest for its entry address.
