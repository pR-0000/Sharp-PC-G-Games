# Loading the games

[Français](LOADING.md) · **English** · [Collection](../README.md#english)

This procedure targets **PC-G801 and PC-G805**. Sharing a connector does not establish ROM compatibility on other models.

**Pocket Vector and Pocket Clash on a 32 KiB G80X:** use the `g80x_32k` files with **USER6BFF** / **USER59FF**, respectively. On an expanded G801, enable **32 KiB RAM expansion (G80X)** in PC-G Link. [Loading and memory limits](G80X_32K.md#english).

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

This reserves Quest's memory for either language. Use `USER09FF` for Star Lane, `USER01FF` for the glyph test or **`USER19FF` for Pocket Depths on G805** instead. Monitor numbers are hexadecimal.

In **Sharp PC-G Link**, select the actual model, then choose a file under **Assembly → Browse**:

- Quest (**G801/G805**): `games/quest/build/g80x/quest_FR.ihx` or `quest_EN.ihx`.
- Quest (**PC-G850**, `USER1FFF`) : `games/quest/build/g850/quest_g850_FR.ihx` / `quest_g850_EN.ihx`.
- Pocket Invaders (**PC-G850**, `USER0DFF`) : `games/pocket-invaders/build/g850/invaders_g850_FR.ihx` / `invaders_g850_EN.ihx`.
- Pocket Runner (**PC-G850**, `USER11FF`) : `games/pocket-runner/build/g850/runner_g850_FR.ihx` / `runner_g850_EN.ihx`.
- Pocket Rally (**PC-G850**, `USER19FF`): `games/pocket-rally/build/g850/rally_g850_FR.ihx` / `rally_g850_EN.ihx`.
- Pocket Clash (**PC-G850**, `USER55FF`): `games/pocket-clash/build/g850/clash_g850_FR.ihx` / `clash_g850_EN.ihx`.
- Pocket Vector (**PC-G850**, `USER6DFF`): `games/pocket-vector/build/g850/vector_FR.ihx` or `vector_EN.ihx`.
- Pocket Jumper (**PC-G850**, `USER19FF`) : `games/pocket-jumper/build/g850/jumper_g850_FR.ihx` / `jumper_g850_EN.ihx`.
- Pocket Depths 2 (**PC-G850**, `USER16FF`) : `games/pocket-depths-2/build/g850/depths2_g850_FR.ihx` / `depths2_g850_EN.ihx`.
- Star Lane (**PC-G850**, `USER0BFF`) : `games/star-lane/build/g850/star_lane_g850_FR.ihx` / `star_lane_g850_EN.ihx`.
- Pocket Depths (**PC-G850**, `USER1EFF`) : `games/pocket-depths/build/g850/depths_g850_FR.ihx` / `depths_g850_EN.ihx`.
- Star Lane: `games/star-lane/build/g80x/star_lane_FR.ihx` or `star_lane_EN.ihx`.
- Pocket Rally (**G801/G805**, `USER17E2`) : `games/pocket-rally/build/g80x/rally_FR.ihx` / `rally_EN.ihx`.
- Pocket Jumper (**G801/G805**, `USER14FF`) : `games/pocket-jumper/build/g80x/jumper_FR.ihx` / `jumper_EN.ihx`.
- Pocket Runner (**G801/G805**, `USER0FFF`): `games/pocket-runner/build/g80x/runner_FR.ihx` or `runner_EN.ihx`.
- Pocket Depths (**select PC-G805**): `games/pocket-depths/build/g80x/depths_FR.ihx` or `depths_EN.ihx`.
- Pocket Depths Lite (**G801/G805**, `USER17E2`): `games/pocket-depths/build/g80x/depths_lite_FR.ihx` or `depths_lite_EN.ihx`.
- Pocket Depths 2 (**G801/G805**, `USER13FF`): `games/pocket-depths-2/build/g80x/depths2_FR.ihx` or `depths2_EN.ihx`.
- Glyph test: `examples/build/g80x/glyph_demo_FR.ihx` or `glyph_demo_EN.ihx`.

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
