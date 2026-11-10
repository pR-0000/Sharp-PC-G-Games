# Target models and memory

[Français](COMPATIBILITY.md) · **English** · [Collection](../README.md#english)

Distributed builds target **PC-G801 / PC-G805**, with **Pocket Clash, Pocket Vector, Pocket Jumper, Pocket Depths 2, Quest, Pocket Invaders, Pocket Runner, Pocket Rally, Star Lane and Pocket Depths for PC-G850**. Choose the file intended for the model and its RAM. Shared IOCS entry points may let some simple programs work across models; that does not establish compatibility for every game. LCD drivers, keyboard, system workspaces and geometry must match the intended profile.

### Three display profiles

| Profile | Usable display | Software buffer | Collection status |
|---|---|---:|---|
| Cell-based G80X / E200 | 24 × 4 cells of 5 × 7, or 120 × 28 addressable dots, with physical gaps | 480 bytes, four seven-bit bands | G801/G805 builds; other models need checking |
| PC-G815 | 144 × 32 continuous dots | 576 bytes | Separate profile to develop |
| PC-G850 | 144 × 48 continuous dots | 864 bytes | Pocket Clash, Pocket Vector, Jumper, Depths 2, Quest, Invaders, Runner, Rally, Star Lane, Depths; S/V/VS variants require separate checks |

G815 is therefore a separate graphics height and controller, rather than an interchangeable four-row G850. G80X machines already draw patterns and sprites; the physical cell gaps remain visible. The [original g800 source](https://ver0.sakura.ne.jp/pc/g800src.0.11.4.tgz), especially `g800.h`, `iocs.c` and `io.c`, explicitly distinguishes these three profiles.

[Maruhiro’s software page](https://ver0.sakura.ne.jp/g800/) is a shared catalogue with per-program model lists. G-KART targets G850/S/V/VS; Pocket BlackJack supplies G850 and E200 versions. The page title does not guarantee a universal binary.

**Pocket Vector and Pocket Clash G80X 32 KiB builds are available.** They target G801/G805 machines whose firmware recognizes the expansion; rendering uses the 5 × 7 cells. Extra RAM does not turn their LCD into a G850 display. See the [G80X 32 KiB guide](G80X_32K.md#english).

### Available builds

| Game | Target | Reservation |
|---|---|---|
| Pocket Clash, prototype | PC-G850 | `USER55FF` |
| Pocket Vector, prototype | PC-G850 | `USER6DFF` |
| Pocket Vector G80X 32K | PC-G801 / PC-G805, 32 Kio / KiB | `USER6BFF` |
| Pocket Clash G80X 32K | PC-G801 / PC-G805, 32 Kio / KiB | `USER59FF` |
| Pocket Jumper G850 | PC-G850 | `USER19FF` |
| Pocket Depths 2 G850 | PC-G850 | `USER16FF` |
| Quest G850 | PC-G850 | `USER1FFF` |
| Pocket Invaders G850 | PC-G850 | `USER0DFF` |
| Pocket Runner G850 | PC-G850 | `USER11FF` |
| Pocket Rally G850 | PC-G850 | `USER19FF` |
| Star Lane G850 | PC-G850 | `USER0BFF` |
| Pocket Depths G850 | PC-G850 | `USER1EFF` |
| Sharp PC-G80X Quest | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Rally | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Jumper | PC-G801 / PC-G805 | `USER14FF` |
| Pocket Runner | PC-G801 / PC-G805 | `USER0FFF` |
| Pocket Depths 2 | PC-G801 / PC-G805 | `USER13FF` |
| Pocket Depths | PC-G805 | `USER19FF` |
| Pocket Invaders | PC-G801 / PC-G805 | `USER0BFF` |
| Star Lane | PC-G801 / PC-G805 | `USER09FF` |
| Pocket Depths Lite | PC-G801 / PC-G805 | `USER17E2` |

Programs start at **0100h** and include their own working data and buffers. The G801 allocation limit used here is **17E2h**, or **5,859 bytes** from 0100h. Full Pocket Depths exceeds that budget; use Lite on G801. Every build manifest lists exact lengths and SHA-256 hashes. Internal firmware entry points documented separately are specific to the G805 profile.

[IOCS](../include/sharp-pc-g8xx.inc) · [g800](https://ver0.sakura.ne.jp/pc/) · [z88dk](https://github.com/z88dk/z88dk/tree/master/libsrc/target/g800)
