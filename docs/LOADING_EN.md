# Loading the games

[Français](LOADING.md) · **English** · [Collection](../README.md#english)

This procedure targets **PC-G801 and PC-G805**. Sharing a connector does not establish ROM compatibility on other models.

## PC and interface

Use a Sharp PC-G compatible serial interface with **RTS/CTS** and matching signal polarity. Do not directly connect a positive/negative-voltage RS-232 cable. For an FTDI interface configured for these machines, TXD/RXD/RTS#/CTS# inversion must already be programmed in EEPROM; the application does not program it.

Install **Sharp PC-G Link** from the separate [Sharp-PC-G-Link repository](https://github.com/pR-0000/Sharp-PC-G-Link). See [utility setup](TRANSFER_TOOL_EN.md). Select the adapter port; the [FTDI VCP driver](https://ftdichip.com/drivers/vcp-drivers/) may be needed. Personal INI settings stay in the utility folder.

## Sharp serial settings

Set these under **TEXT → Sio → Format** and match them on the PC:

| Setting | Recommended value |
|---|---|
| Baud rate | 4800 |
| Data bits | 8 |
| Parity | none |
| Stop bits | 1 |
| Protocol | RS/CS; RTS/CTS is enforced on the PC |
| End of line | CR LF |
| End of file | 1A |

Confirm changes on the Sharp. The **Recommended: 4800 / 8N1** button configures the PC only. The initial settings are **1200 / 7N1**; that slower configuration also works when both ends match.

## Receive machine code

Back up useful data first. In BASIC RUN mode enter:

```text
MON
USER17E2
R
```

This reserves Quest's memory for either language. Use `USER05FF` for Star Lane, `USER01FF` for the glyph test or **`USER19FF` for Pocket Depths on G805** instead. Monitor numbers are hexadecimal.

In **Sharp PC-G Link**, select the actual model, then choose a file under **Assembly → Browse**:

- Quest: `games/quest/build/quest_FR.hex` or `quest_EN.hex`.
- Star Lane: `build/star_lane_FR.hex` or `star_lane_EN.hex`.
- Pocket Rally (**G801/G805**, `USER17E2`) : `games/pocket-rally/build/rally_FR.hex` / `rally_EN.hex`.
- Pocket Jumper (**G801/G805**, `USER14FF`) : `games/pocket-jumper/build/jumper_FR.hex` / `jumper_EN.hex`.
- Pocket Runner (**G801/G805**, `USER0FFF`): `games/pocket-runner/build/runner_FR.hex` or `runner_EN.hex`.
- Pocket Depths (**select PC-G805**): `games/pocket-depths/build/depths_FR.hex` or `depths_EN.hex`.
- Pocket Depths Lite (**G801/G805**, `USER17E2`): `games/pocket-depths/build/depths_lite_FR.hex` or `depths_lite_EN.hex`.
- Pocket Depths 2 (**G801/G805**, `USER13FF`): `games/pocket-depths-2/build/depths2_FR.hex` or `depths2_EN.hex`.
- Glyph test: `build/glyph_demo_FR.hex` or `glyph_demo_EN.hex`.

Click **Send ASM** after preparing the Sharp with `R`. Once reception finishes on the Sharp, enter:

```text
G100
```

All programs are assembled for **0100h**. HEX files contain addresses; for a BIN use **BIN load address = 0100**, **Entry point = 0100**. Changing that field does not relocate machine code. Do not append EOF 1A yourself. **Q or BREAK** exits; in Quest, use Q on the map.

## Start from BASIC after loading

Use **`CALL &H100`** in BASIC RUN mode after reserving USER memory and receiving the binary. It starts resident machine code, rather than loading a file. The code must retain the caller stack and end with RET. See the [BASIC guide](BASIC_CALL_EN.md).

## Troubleshooting

- **“Bytes sent”** reports PC transmission without file acknowledgement from the Sharp. Check reception and execution on the device. CTS can be active even outside receive mode.
- **I/O DEVICE ERROR / ERROR 10**: check receive mode, matching serial format, RS/CS, wiring and FTDI inversions. Assembly games use **MON → R**, rather than **TEXT → Sio → Load** or BASIC `LOAD`.
- If **FRE shows about 64 KB on an 8 KB G801**, back up anything recoverable, perform **RESET** and answer **Y** to **MEMORY CLEAR O.K. ?**. This clears memory; use it for inconsistent memory state. Recheck serial settings afterward.
- The **glyph test** and Star Lane help check loading and graphics calls before a larger program.

## BASIC examples

For listings under `examples/basic/` (Sharp-PC-G-Link), use **Send BASIC**, receive with **TEXT → Sio → Load**, view them in **TEXT → Edit**, then convert using **TEXT → Basic → Basic←text**, before **RUN**. Conversion replaces existing BASIC code. This differs from the machine-code game loading procedure above.

References: [readrom, serial settings and monitor commands](https://github.com/fu-sen/readrom), [z88dk SIO sender](https://github.com/z88dk/z88dk/blob/master/examples/g800/send.py). USER reservations above come from this collection's binaries, not the readrom program.
