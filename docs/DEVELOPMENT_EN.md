# Development

[Français](DEVELOPMENT.md) · **English** · [Collection](../README.md#english)

Ready-to-load `.ihx` files require no development tools. To edit a game, install Python 3.10+ and [SjASMPlus](https://github.com/z00m128/sjasmplus), then build its sources from the repository root. Example:

```text
python games/star-lane/build_star.py --lang en --assembler "sjasmplus.exe"
```

Each `games/<game>/build_*.py` script generates both languages. Use `--target g80x` or `--target g850` where supported; Vector and Clash use `--target g80x-32k` for expanded G80X machines.

Game rules, source artwork and build scripts live with each game. `include/` defines hardware interfaces; `lib/` contains shared assembly routines and the small Python modules needed by source builds. `build/<target>/manifest.json` records sizes, USER reservations and SHA-256 hashes.

G80X graphics use 120 × 28 useful pixels in four seven-bit bands. G850 graphics use 144 × 48 pixels in six eight-bit bands. Game rules are shared where possible; LCD geometry and keyboard handling belong to target-specific code.
