# Quest provenance

[Français](NOTICE.md) · **English**

This port derives from **[Canon X-07 Quest](https://github.com/pR-0000/Canon_X-07_RPG)**. `upstream.json` records the source-file hashes.

The map, text, statistics and some Z80 routines come from that game. Sharp routines, 5 × 7 patterns, compact state storage and porting tools/tests were added for this adaptation. The G850 target also uses the Canon atlas’s 23 original 8 × 8 graphics, kept in `targets/g850/tiles.bmp`; enlarged portraits are generated from this atlas. Canon music and the sound driver are not included.

Inherited Quest material remains subject to its author's terms; this port does not assume any change to the original game's licence. The repository's MIT licence covers the new tools and Sharp components, subject to the inherited material above.

Sharp IOCS addresses/contracts come from public g800 and z88dk sources, described in the [compatibility guide](../../docs/COMPATIBILITY_EN.md) and the root's `include/sharp_pc_g801.inc`. SjASMPlus, z80, g800 and SDL retain their own licences and are not redistributed in the archive.
