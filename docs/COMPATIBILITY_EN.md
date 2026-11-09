# Target models and memory

[Français](COMPATIBILITY.md) · **English** · [Collection](../README.md#english)

The collection targets **PC-G801 / PC-G805** and their four-row LCD through the Sharp IOCS interface. The model list describes the intended target, rather than all machines sharing the PC-G name or connector. PC-G81X, G820/G830 and G850 require their own firmware and display adaptation.

| Game | Target | Reservation |
|---|---|---|
| Sharp PC-G80X Quest | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Rally | PC-G801 / PC-G805 | `USER17E2` |
| Pocket Jumper | PC-G801 / PC-G805 | `USER14FF` |
| Pocket Runner | PC-G801 / PC-G805 | `USER0FFF` |
| Pocket Depths 2 | PC-G801 / PC-G805 | `USER13FF` |
| Pocket Depths | PC-G805 | `USER19FF` |
| Pocket Invaders | PC-G801 / PC-G805 | `USER0BFF` |
| Star Lane | PC-G801 / PC-G805 | `USER05FF` |
| Pocket Depths Lite | PC-G801 / PC-G805 | `USER17E2` |

Programs start at **0100h** and include their own working data and buffers. The G801 allocation limit used here is **17E2h**, or **5,859 bytes** from 0100h. Full Pocket Depths exceeds that budget; use Lite on G801. Every build manifest lists exact lengths and SHA-256 hashes. Internal firmware entry points documented separately are specific to the G805 profile.

[IOCS](../include/sharp-pc-g8xx.inc) · [g800](https://ver0.sakura.ne.jp/pc/) · [z88dk](https://github.com/z88dk/z88dk/tree/master/libsrc/target/g800)
