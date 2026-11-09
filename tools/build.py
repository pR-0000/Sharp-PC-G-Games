"""Build the independent G801 programs with SjASMPlus; Python stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from cli_i18n import Parser, pick

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT


def intel_hex(data: bytes, origin: int) -> str:
    lines = []
    for offset in range(0, len(data), 16):
        address = origin + offset
        chunk = data[offset:offset + 16]
        record = bytes((len(chunk), address >> 8, address & 255, 0)) + chunk
        lines.append(":" + (record + bytes((-sum(record) & 255,))).hex().upper())
    return "\n".join(lines + [":00000001FF"]) + "\n"


def read_symbols(path: Path) -> dict[str, int]:
    symbols = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([^:]+): EQU 0x([0-9A-Fa-f]+)", line)
        if match:
            symbols[match[1]] = int(match[2], 16)
    return symbols


def main():
    parser = Parser("Construire le test de motifs et Star Lane en français/anglais.",
                    "Build the glyph test and Star Lane in French/English.")
    parser.add_argument("--assembler", default=os.environ.get("SJASMPLUS", "sjasmplus"),
                        help=pick(parser.lang, "Exécutable SjASMPlus (ou SJASMPLUS / PATH).", "SjASMPlus executable (or SJASMPLUS / PATH)."))
    args = parser.parse_args()
    assembler = shutil.which(args.assembler)
    if not assembler:
        parser.error(pick(args.lang, "SjASMPlus absent : indiquer --assembler ou SJASMPLUS / PATH.",
                         "SjASMPlus not found: use --assembler or SJASMPLUS / PATH."))
    output = TARGET / "build"
    output.mkdir(exist_ok=True)
    manifest = {"origin": "0100", "entry": "0100", "programs": {}}
    for stem, name, language in (
        ("examples/glyph_demo.asm", "glyph_demo", 1), ("examples/glyph_demo.asm", "glyph_demo_EN", 1),
        ("examples/glyph_demo.asm", "glyph_demo_FR", 0), ("games/star-lane/star_lane.asm", "star_lane", 1),
        ("games/star-lane/star_lane.asm", "star_lane_EN", 1), ("games/star-lane/star_lane.asm", "star_lane_FR", 0),
    ):
        source = TARGET / stem
        base = output / name
        subprocess.run([assembler, "--nologo", "--color=off", "--fullpath=rel",
                        f"-DBUILD_LANG_EN={language}", f"--inc={(TARGET / 'include').as_posix()}", f"--raw={base.as_posix()}.bin",
                        f"--sym={base.as_posix()}.sym", f"--lst={base.as_posix()}.lst", source.as_posix()],
                       cwd=ROOT, check=True)
        data = base.with_suffix(".bin").read_bytes()
        symbols = read_symbols(base.with_suffix(".sym"))
        assert symbols["entry"] == 0x100
        assert symbols["program_end"] == 0x100 + len(data)
        end = symbols["program_end"] - 1
        assert end < 0x1000
        base.with_suffix(".hex").write_text(intel_hex(data, 0x100), encoding="ascii")
        user = end | 0xFF
        manifest["programs"][name] = {
            "bytes": len(data), "last_address": f"{end:04X}",
            "user_command": f"USER{user:04X}", "run_command": "G100",
            "sha256_bin": hashlib.sha256(data).hexdigest(),
            "sha256_hex": hashlib.sha256(base.with_suffix('.hex').read_bytes()).hexdigest(),
        }
        unit = pick(args.lang, "octets", "bytes")
        print(f"{name}: {len(data)} {unit}, 0100-{end:04X}, USER{user:04X}, G100")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
