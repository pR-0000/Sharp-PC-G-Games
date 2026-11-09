"""Build both Quest languages using SjASMPlus, with no downloads."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ASSEMBLY = HERE.parents[1]
sys.path.insert(0, str(ASSEMBLY / "tools"))
from build import intel_hex, read_symbols
from cli_i18n import Parser, pick
from tiles_tool import read_bmp, write_inc, write_preview, write_map, TileError


def main():
    parser = Parser("Construire Quest FR/EN avec SjASMPlus, à partir du BMP éditable.",
                    "Build Quest FR/EN with SjASMPlus from the editable BMP.")
    parser.add_argument("--assembler", default=os.environ.get("SJASMPLUS", "sjasmplus"),
                        help=pick(parser.lang, "Exécutable SjASMPlus (ou SJASMPLUS / PATH).", "SjASMPlus executable (or SJASMPLUS / PATH)."))
    parser.add_argument("--typing-reload", type=int, default=6,
                        help=pick(parser.lang, "Lectures clavier par unité de délai (1–64 ; défaut : 6).", "Keyboard polls per timeout unit (1–64; default: 6)."))
    args = parser.parse_args()
    if not 1 <= args.typing_reload <= 64:
        parser.error(pick(args.lang, "--typing-reload doit être compris entre 1 et 64.", "--typing-reload must be between 1 and 64."))
    assembler = shutil.which(args.assembler)
    if not assembler:
        parser.error(pick(args.lang, "SjASMPlus absent ; indiquer --assembler ou SJASMPLUS / PATH.",
                         "SjASMPlus not found; use --assembler or SJASMPLUS / PATH."))
    try:
        tiles = read_bmp(HERE / "tiles.bmp")
        write_inc(HERE / "tiles.inc", tiles)
        write_preview(HERE / "docs/tiles_preview.png", tiles)
        write_map(HERE / "map.bmp", tiles, preview_path=HERE / "docs/map_preview.png")
    except TileError as error:
        parser.error(pick(args.lang, error.fr, error.en))
    except OSError as error:
        parser.error(pick(args.lang, f"Erreur de fichier : {error}", f"File error: {error}"))
    output = HERE / "build"
    output.mkdir(exist_ok=True)
    manifest = {"name": "Sharp PC-G80X Quest", "version": (HERE / "VERSION").read_text().strip(), "origin": "0100", "entry": "0100", "sound": False,
                "typing_reload": args.typing_reload, "timing_reference": "g800 0.11.4 PC-G801, 4000 kHz, emulated IOCS", "programs": {}}
    for lang, value in (("FR", 0), ("EN", 1)):
        base = output / f"quest_{lang}"
        subprocess.run([assembler, "--nologo", "--color=off", "--fullpath=rel",
                        f"-DBUILD_LANG_EN={value}", f"-DTYPING_TICK_RELOAD={args.typing_reload}", f"--inc={(ASSEMBLY / 'include').as_posix()}",
                        f"--raw={base.as_posix()}.bin", f"--lst={base.as_posix()}.lst",
                        f"--sym={base.as_posix()}.sym", (HERE / "quest.asm").as_posix()], cwd=HERE, check=True)
        binary = base.with_suffix(".bin").read_bytes()
        symbols = read_symbols(base.with_suffix(".sym"))
        assert symbols["entry"] == 0x100
        assert symbols["program_end"] == 0x100 + len(binary)
        end = 0xFF + len(binary)
        assert end <= 0x17E2
        base.with_suffix(".hex").write_text(intel_hex(binary, 0x100), encoding="ascii")
        user = min(end | 255, 0x17E2)
        manifest["programs"][f"quest_{lang}"] = {
            "bytes": len(binary), "last_address": f"{end:04X}",
            "user_command": f"USER{user:04X}", "run_command": "G100",
            "sha256_bin": hashlib.sha256(binary).hexdigest(),
            "sha256_hex": hashlib.sha256(base.with_suffix('.hex').read_bytes()).hexdigest(),
        }
        unit = pick(args.lang, "octets", "bytes")
        print(f"Quest {lang}: {len(binary)} {unit}, 0100-{end:04X}, USER{user:04X}, G100")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
