"""FR : construire la collection. EN: build the collection."""
from pathlib import Path
import os
import subprocess
import sys
from cli_i18n import Parser, pick

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = Parser("Construire tous les jeux et exemples FR/EN.", "Build all FR/EN games and examples.")
    parser.add_argument("--assembler", default=os.environ.get("SJASMPLUS", "sjasmplus"),
                        help=pick(parser.lang, "Chemin SjASMPlus, ou SJASMPLUS / PATH.", "SjASMPlus path, or SJASMPLUS / PATH."))
    args = parser.parse_args()
    for script in (ROOT / "tools/build.py", ROOT / "games/quest/build_quest.py", ROOT / "games/pocket-depths/build_depths.py", ROOT / "games/pocket-invaders/build_invaders.py", ROOT / "games/pocket-depths-2/build_depths2.py", ROOT / "games/pocket-runner/build_runner.py", ROOT / "games/pocket-jumper/build_jumper.py", ROOT / "games/pocket-rally/build_rally.py"):
        subprocess.run([sys.executable, str(script), "--lang", args.lang, "--assembler", args.assembler],
                       cwd=ROOT, check=True)
    print(pick(args.lang, "Collection FR/EN construite.", "FR/EN collection built."))


if __name__ == "__main__":
    main()
