# Development

[Français](DEVELOPMENT.md) · **English** · [Collection](../README.md#english)

Build from the repository root with Python 3.10+ and SjASMPlus. Both languages are generated:

```text
python tools/build_all.py --lang en --assembler "sjasmplus.exe"
```

The `SJASMPLUS` environment variable or PATH may also select the assembler. BIN, Intel HEX and manifests are kept with each game; symbols and listings are generated locally. Rebuild distributed binaries after source edits.

## Automated checks

```text
python -m pip install -r tests/requirements.txt
python tools/check_publication.py --lang en
python -m unittest discover -s tests -p "test_*.py"
python tests/check_programs.py --lang en
python games/quest/check_quest.py --lang en
python games/quest/check_tiles.py --lang en
python games/pocket-depths/check_depths.py --lang en
python games/pocket-depths-2/check_depths2.py --lang en
python games/pocket-invaders/check_invaders.py --lang en
python games/pocket-runner/check_runner.py --lang en
python games/pocket-rally/check_rally.py --lang en
python games/pocket-jumper/check_jumper.py --lang en
python games/pocket-jumper/check_assets.py --lang en --assembler "sjasmplus.exe"
```

The publication check verifies README links and anchors, manifest hashes, BIN/HEX equivalence, checksums and memory reservations. It only needs standard Python and also runs before archive creation. CPU checks execute assembled Z80 code with simulated IOCS contracts; they require `z80==1.2.0`. Building and playing do not require this dependency.

## Graphics

The pixel format uses **480 bytes**: four 120-column bands, with seven useful bits per byte. Pixel `(x,y)` is at `120*(y//7)+x`, mask `1<<(y%7)`. Upload each band using `PCG_IOCS_PATTERN`, with D=row, E=character column and B=pixel-column count. The physical LCD keeps gaps between its cells. Right-hand HUD digits can use the native ROM font.

See `games/pocket-jumper/render.asm` for clipped sprite composition, `games/pocket-depths-2/raycaster.asm` for fixed-point DDA, and `include/sharp-pc-g8xx.inc` for IOCS contracts.

## g800

```text
python tools/play_jumper.py --lang en --emulator "g800.exe"
```

The same launcher pattern is available for `play_rally.py`, `play_runner.py`, `play_invaders.py`, `play_depths.py` and `play_depths2.py`. Add `--lite` for Depths Lite. g800 is installed separately. The launchers use simulated IOCS without a ROM. Optional Windows screenshot tools require `tools/requirements-capture.txt` and capture only the LCD.

## Release archive

```text
python tools/package_collection.py --lang en
```

Creates a ZIP and SHA-256 file in `../deliverables/`, excluding environments, personal settings, caches and local reports.
