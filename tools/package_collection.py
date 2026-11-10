"""FR : archiver les sources et jeux. EN: package sources and games."""
from pathlib import Path
import hashlib
import zipfile
from cli_i18n import Parser, pick
from check_publication import check_collection

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", ".local", "__pycache__", "dist", "deliverables", "rom-dumps", "ROM dumps"}


def included(path, root=ROOT):
    relative = path.relative_to(root)
    name = path.name.casefold()
    return (not any(part.casefold() in {p.casefold() for p in EXCLUDED} for part in relative.parts)
            and path.suffix.casefold() not in {".pyc", ".pyo", ".lst", ".sym", ".exe", ".log"}
            and name not in {"sharp_pc_g_link.ini", "sharp_pc_g_link.ini.tmp", "hardware_reports.json", "captures.json", "timing_comparison.json", "timing_patch.md", "timing_patch_en.md", "quest_0_1_4_or_0_1_5_typing_patch.ihx"}
            and not (path.suffix.casefold() == ".json" and ("validation" in name or name.startswith("typing_adjustment_")
                    or "docs" in relative.parts and (name.startswith("capture_") or name.startswith("depths_door_")))))


def main():
    parser = Parser("Créer l'archive GitHub de la collection FR/EN.", "Create the FR/EN collection GitHub archive.")
    args = parser.parse_args()
    check_collection(ROOT, included)
    destination = ROOT.parent / "deliverables"
    destination.mkdir(exist_ok=True)
    version = (ROOT / "VERSION").read_text(encoding="ascii").strip()
    output = destination / f"Sharp_PC-G_Games_{version}_GitHub.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if path.is_file() and included(path):
                archive.write(path, ROOT.name + "/" + path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ZIP checksum error")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".SHA256.txt").write_text(f"{digest}  {output.name}\n", encoding="ascii")
    print(pick(args.lang, f"Archive vérifiée : {output}", f"Verified archive: {output}"))


if __name__ == "__main__":
    main()
