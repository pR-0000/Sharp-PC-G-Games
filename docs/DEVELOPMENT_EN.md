# Development

[Français](DEVELOPMENT.md) · **English** · [Collection](../README.md#english)

Build from the repository root with Python 3.10+ and SjASMPlus. Both languages are generated:

```text
python tools/build_all.py --lang en --assembler "sjasmplus.exe"
```

The `SJASMPLUS` environment variable or PATH may also select the assembler. BIN, Intel HEX and manifests are kept with each game; symbols and listings are generated locally. Rebuild distributed binaries after source edits.

## Target organization

Keep **one repository organized by game**: `games/<game>/` holds its rules, source artwork and bilingual documentation. `include/` and `lib/` hold hardware contracts and drivers by profile. LCD and keyboard differences belong in that layer; gameplay rules and circuits remain shared where possible.

When a game gains multiple builds, add `targets/g850/`, `targets/g815/` or `targets/g80x-32k/` within its folder for adaptations, plus `build/<target>/` for each family. Include the target in downloaded filenames too, for example `clash_g850_FR.ihx` and `clash_g80x_32k_FR.ihx`. This layout also applies to single-target games. Distribute `.ihx` and `.bin` files with their manifest; keep no duplicates at the root of `build/`.

Each target manifest should identify the model, minimum RAM, display geometry, origin, USER reservation, entry point, language and hashes. The main README serves as a catalogue with a [compatibility matrix](COMPATIBILITY_EN.md); release archives may group games by target and memory requirement. A shared Z80 CPU or connector does not establish profile compatibility.

## Automated checks

Quest, Pocket Invaders, Pocket Runner, Pocket Rally, Pocket Jumper, Pocket Depths 1/2 and Star Lane use `include/game_platform.inc` and `lib/game_runtime.asm`, sharing only public IOCS interfaces. G850 builds do not import G805 internal system pointers. Their build scripts produce G80X and G850; `--target g850` or `--target g80x` selects one target. G850 files live in `games/<game>/build/g850/`; G80X files live in `games/<game>/build/g80x/`.

```text
python -m pip install -r tests/requirements.txt
python tools/check_publication.py --lang en
python -m unittest discover -s tests -p "test_*.py"
python tests/check_programs.py --lang en
python games/star-lane/check_star.py --lang en
python games/star-lane/check_g850.py --lang en
python games/pocket-depths/check_g850.py --lang en
python games/quest/check_quest.py --lang en
python games/quest/check_tiles.py --lang en
python games/pocket-depths/check_depths.py --lang en
python games/pocket-depths-2/check_depths2.py --lang en
python games/pocket-invaders/check_invaders.py --lang en
python games/pocket-runner/check_runner.py --lang en
python games/pocket-rally/check_rally.py --lang en
python games/pocket-vector/check_vector.py --lang en
python games/pocket-clash/check_clash.py --lang en
python tests/check_g80x32_ports.py --lang en
python tests/check_g850_backend.py --lang en --assembler "sjasmplus.exe"
python games/pocket-jumper/check_jumper.py --lang en
python games/pocket-jumper/check_assets.py --lang en --assembler "sjasmplus.exe"
python games/pocket-jumper/check_g850.py --lang en
python games/pocket-depths-2/check_g850.py --lang en
python games/quest/check_g850.py --lang en
python games/pocket-invaders/check_g850.py --lang en
python games/pocket-runner/check_g850.py --lang en
python games/pocket-rally/check_g850.py --lang en
```

The publication check verifies README links and anchors, manifest hashes, BIN/IHX equivalence, checksums and memory reservations. It only needs standard Python and also runs before archive creation. CPU checks execute assembled Z80 code with simulated IOCS contracts; they require `z80==1.2.0`. Building and playing do not require this dependency.

## Graphics

The pixel format uses **480 bytes**: four 120-column bands, with seven useful bits per byte. Pixel `(x,y)` is at `120*(y//7)+x`, mask `1<<(y%7)`. Upload each band using `PCG_IOCS_PATTERN`, with D=row, E=character column and B=pixel-column count. The physical LCD keeps gaps between its cells. Right-hand HUD digits can use the native ROM font.

See `games/pocket-jumper/render.asm` for clipped sprite composition, `games/pocket-depths-2/raycaster.asm` for fixed-point DDA, and `include/sharp-pc-g8xx.inc` for IOCS contracts.

The [G850 development profile](G850.md#english) uses a separate 864-byte buffer and `sharp_pc_g850.inc`. [Pocket Vector](../games/pocket-vector/README.md#english) is a playable prototype for this profile. The [engine study](../designs/pocket-vector/README.md#english) details floor projection and processing budgets.

## g800

```text
python tools/play_jumper.py --lang en --emulator "g800.exe"
```

The same launcher pattern is available for `play_quest.py`, `play_rally.py`, `play_runner.py`, `play_invaders.py`, `play_star.py`, `play_depths.py` and `play_depths2.py`. `play_clash.py` / `play_vector.py` selects the PC-G850 profile. Add `--lite` for Depths Lite. g800 is installed separately. The launchers use simulated IOCS without a ROM. Optional Windows screenshot tools require `tools/requirements-capture.txt` and capture only the LCD.

For Quest, Invaders, Runner, Rally, Jumper, Star Lane and Depths 1/2, add **`--model PC-G850`** to the launcher. `python tools/capture_g850_games.py --lang en --emulator "g800.exe"` captures their LCDs and checks playfield pixels and graphical battle portraits against the Z80 program buffer. Capture states are prepared; temporary capture files never replace distributed programs.

## Release archive

```text
python tools/package_collection.py --lang en
```

Creates a ZIP and SHA-256 file in `../deliverables/`, excluding environments, personal settings, caches and local reports.


Pocket Vector and Pocket Clash: `--target g80x-32k` builds or launches the 32 KiB profile; `--target g850` selects the native profile. Builds without a selector generate both. G850 files live in `build/g850/`. [G80X 32 KiB loading](G80X_32K.md#english).


## Animated gallery

```text
python tools/capture_animations.py --lang en --emulator "g800.exe"
```

Produces the five G850 GIFs from distributed binaries: Vector, Clash, Jumper, Rally and Depths 2. `--game jumper` selects one game. Each frame passes through g800 and its playfield pixels are compared against Z80 execution. Counters use the native font; GIF timing is illustrative. Temporary snapshots and reports remain outside the distribution.
