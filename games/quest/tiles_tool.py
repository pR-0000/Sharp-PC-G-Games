"""FR : convertir l'atlas BMP éditable en données Z80, et inversement.
EN: convert the editable BMP atlas to Z80 data and back. Python stdlib only.
"""
from pathlib import Path
import json
import re
import struct
import sys
import unicodedata
import zlib

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from cli_i18n import Parser, pick


class TileError(ValueError):
    def __init__(self, fr, en):
        self.fr, self.en = fr, en
        super().__init__(fr + " / " + en)


def catalog():
    spec = json.loads((HERE / "tiles.json").read_text(encoding="utf-8"))
    assert (spec["width"], spec["height"], spec["columns"], spec["hero_id"]) == (5, 7, 1, 15)
    assert [tile["id"] for tile in spec["tiles"]] == list(range(23))
    return spec["tiles"]


def read_inc(path):
    text = Path(path).read_text(encoding="utf-8").split("status_hint:", 1)[0]
    rows = []
    for line in text.splitlines():
        match = re.match(r"\s*db\s+((?:0x[0-9A-Fa-f]{2},?\s*){5})(?:;.*)?$", line)
        if match:
            rows.append(bytes(int(value, 16) for value in re.findall(r"0x([0-9A-Fa-f]{2})", match[1])))
    if len(rows) != 23 or any(value & 128 for row in rows for value in row):
        raise TileError("Il faut 23 motifs de cinq octets, bit 7 nul.", "Expected 23 five-byte patterns with bit 7 clear.")
    return rows


def write_bmp(path, tiles):
    width, height = 5, len(tiles) * 7
    pixels = bytes(color for y in range(height) for x in range(width)
                   for color in (0 if tiles[y // 7][x] & (1 << (y % 7)) else 255,) * 3)
    write_grayscale_bmp(path, width, height, pixels)


def write_grayscale_bmp(path, width, height, pixels):
    stride = (width * 3 + 3) & ~3
    image = bytearray()
    for y in reversed(range(height)):
        # Gris : RGB = BGR dans le BMP. / Grayscale: RGB equals BMP's BGR.
        image.extend(pixels[y * width * 3:(y + 1) * width * 3])
        image.extend(bytes(stride - width * 3))
    header = struct.pack("<2sIHHI", b"BM", 54 + len(image), 0, 0, 54)
    header += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(image), 2835, 2835, 0, 0)
    Path(path).write_bytes(header + image)


def read_map(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split(";", 1)[0].strip()
        if not line or line == "map_packed:":
            continue
        if not re.fullmatch(r"\.?db\s+\$[0-9A-Fa-f]{2}(?:\s*,\s*\$[0-9A-Fa-f]{2})*", line):
            raise TileError("Ligne de carte invalide.", "Invalid map data line.")
        packed = bytes(int(value, 16) for value in re.findall(r"\$([0-9A-Fa-f]{2})", line))
        rows.append(bytes(tile for value in packed for tile in (value >> 4, value & 15)))
    if len(rows) != 16 or any(len(row) != 30 or any(tile > 14 for tile in row) for row in rows):
        raise TileError("La carte doit contenir 30 × 16 cases d'identifiant 0 à 14.",
                        "The map must contain 30 × 16 tiles with IDs 0 to 14.")
    return rows


def write_map(path, tiles, map_path=HERE / "map_packed.inc", preview_path=None):
    rows = read_map(map_path)
    width, height = 150, 112
    pixels = bytes(color for y in range(height) for x in range(width)
                   for color in (0 if tiles[rows[y // 7][x // 5]][x % 5] & (1 << (y % 7)) else 255,) * 3)
    write_grayscale_bmp(path, width, height, pixels)
    if preview_path is not None:
        scale = 4
        enlarged = bytearray()
        for y in range(height):
            row = b"".join(pixels[(y * width + x) * 3:(y * width + x + 1) * 3] * scale for x in range(width))
            enlarged.extend(row * scale)
        write_png(preview_path, width * scale, height * scale, enlarged)


def read_bmp(path):
    data = Path(path).read_bytes()
    if len(data) < 54 or data[:2] != b"BM":
        raise TileError("Fichier BMP invalide ou tronqué.", "Invalid or truncated BMP file.")
    offset = struct.unpack_from("<I", data, 10)[0]
    dib = struct.unpack_from("<I", data, 14)[0]
    width, signed_height, planes, depth, compression = struct.unpack_from("<iiHHI", data, 18)
    if dib < 40 or 14 + dib > len(data) or offset < 14 + dib:
        raise TileError("En-tête BMP non pris en charge.", "Unsupported BMP header.")
    if (width, abs(signed_height)) != (5, 161):
        raise TileError("L'atlas doit mesurer exactement 5 × 161 pixels : 23 motifs de 5 × 7.",
                        "The atlas must be exactly 5 × 161 pixels: 23 patterns of 5 × 7.")
    if planes != 1 or compression != 0 or depth not in (1, 4, 8, 24, 32):
        raise TileError("Enregistrer en BMP non compressé, 1/4/8/24/32 bits.", "Save as uncompressed 1/4/8/24/32-bit BMP.")
    stride = ((width * depth + 31) // 32) * 4
    if len(data) < offset + stride * 161:
        raise TileError("Données BMP tronquées.", "Truncated BMP pixel data.")
    palette = []
    if depth <= 8:
        used = struct.unpack_from("<I", data, 46)[0] or (1 << depth)
        if used > 1 << depth or 14 + dib + used * 4 > offset:
            raise TileError("Palette BMP invalide.", "Invalid BMP palette.")
        palette = [tuple(data[p:p + 3]) for p in range(14 + dib, 14 + dib + used * 4, 4)]
    result = [bytearray(5) for _ in range(23)]
    for y in range(161):
        row = offset + (y if signed_height < 0 else 160 - y) * stride
        for x in range(5):
            if depth >= 24:
                p = row + x * (depth // 8)
                color = tuple(data[p:p + 3])
            else:
                packed = data[row + x * depth // 8]
                index = (packed >> (8 - depth - (x * depth % 8))) & ((1 << depth) - 1)
                if index >= len(palette):
                    raise TileError("Index de palette BMP invalide.", "Invalid BMP palette index.")
                color = palette[index]
            if color == (0, 0, 0):
                result[y // 7][x] |= 1 << (y % 7)
            elif color != (255, 255, 255):
                raise TileError(f"Pixel ({x},{y}) : utiliser uniquement du noir et du blanc, sans lissage.",
                                f"Pixel ({x},{y}): use only black and white, with no antialiasing.")
    return [bytes(row) for row in result]


def write_inc(path, tiles):
    lines = ["; Généré depuis tiles.bmp / Generated from tiles.bmp.",
             "; Modifier le BMP puis reconstruire / Edit the BMP, then rebuild.",
             "; 5 colonnes, bit 0 en haut / 5 columns, bit 0 at the top.", "glyph_tiles:"]
    for tile, row in zip(catalog(), tiles, strict=True):
        if tile["id"] == 15:
            lines.append("glyph_hero:")
        values = ",".join(f"0x{value:02X}" for value in row)
        lines.append(f"    db {values} ; {tile['id']:02} {tile['fr']} / {tile['en']}")
    lines.extend(["status_hint:", "    IF BUILD_LANG_EN", '    db "M:STATUS",0',
                  "    ELSE", '    db "M:STATUT",0', "    ENDIF", ""])
    target = Path(path)
    text = "\n".join(lines)
    if not target.exists() or target.read_text(encoding="utf-8") != text:
        target.write_text(text, encoding="utf-8")


# Small preview-only bitmap font. / Petite police réservée à l'aperçu.
FONT = {
    "A":"0E11111F111111", "B":"1E11111E11111E", "C":"0E11101010110E", "D":"1E11111111111E",
    "E":"1F10101E10101F", "F":"1F10101E101010", "G":"0E11101711110F", "H":"1111111F111111",
    "I":"0E04040404040E", "J":"0702020212120C", "K":"11121418141211", "L":"1010101010101F",
    "M":"111B1515111111", "N":"11191513111111", "O":"0E11111111110E", "P":"1E11111E101010",
    "Q":"0E11111115120D", "R":"1E11111E141211", "S":"0F10100E01011E", "T":"1F040404040404",
    "U":"1111111111110E", "V":"11111111110A04", "W":"11111115151B11", "X":"11110A040A1111",
    "Y":"11110A04040404", "Z":"1F01020408101F", "0":"0E11131519110E", "1":"040C040404040E",
    "2":"0E11010204081F", "3":"1E01010601011E", "4":"02060A121F0202", "5":"1F10101E01011E",
    "6":"0E10101E11110E", "7":"1F010204080808", "8":"0E11110E11110E", "9":"0E11110F01010E",
    "-":"0000001F000000", "/":"01010204081010", "(":"02040808080402", ")":"08040202020408",
    ",":"00000000000408", ":":"00040000000400", " ":"00000000000000",
}


def write_preview(path, tiles):
    width, height = 420, 48 + 23 * 52
    pixels = bytearray([255]) * (width * height * 3)
    def rect(x, y, w, h, color):
        row = bytes(color) * w
        for yy in range(y, y + h):
            start = (yy * width + x) * 3
            pixels[start:start + len(row)] = row
    def text(x, y, value, color=(25, 25, 25)):
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().upper()
        for char in value:
            pattern = bytes.fromhex(FONT.get(char, FONT[" "]))
            for yy, bits in enumerate(pattern):
                for xx in range(5):
                    if bits & (1 << (4 - xx)):
                        rect(x + xx * 2, y + yy * 2, 2, 2, color)
            x += 12
    text(8, 6, "QUEST - TUILES / TILES")
    text(8, 26, "5 X 7 - 23 MOTIFS / PATTERNS")
    for tile, columns in zip(catalog(), tiles, strict=True):
        y = 48 + tile["id"] * 52
        if tile["id"] % 2 == 0:
            rect(0, y, width, 52, (244, 244, 244))
        text(8, y + 17, f"{tile['id']:02}")
        for row in range(7):
            for col in range(5):
                rect(42 + col * 6, y + 5 + row * 6, 6, 6, (190, 190, 190))
                color = 0 if columns[col] & (1 << row) else 255
                rect(43 + col * 6, y + 6 + row * 6, 5, 5, (color,) * 3)
        text(88, y + 9, tile["fr"])
        text(88, y + 29, tile["en"], (90, 90, 90))
    write_png(path, width, height, pixels)


def write_png(path, width, height, pixels):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))
    raw = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


def main():
    parser = Parser("Exporter/importer les 23 motifs verticaux (BMP 5 × 161) et exporter la carte complète, sans dépendance.",
                    "Export/import the 23 vertically stacked patterns (5 × 161 BMP) and export the full world map, with no dependencies.")
    lang = parser.lang
    parser.add_argument("action", choices=("export", "import", "preview", "map"),
                        help=pick(lang, "export : INC → BMP ; import : BMP → INC ; preview : aperçu PNG ; map : carte complète BMP/PNG.",
                                  "export: INC → BMP; import: BMP → INC; preview: PNG contact sheet; map: full BMP/PNG world map."))
    parser.add_argument("--bmp", type=Path, default=HERE / "tiles.bmp", help=pick(lang, "Atlas BMP éditable.", "Editable BMP atlas."))
    parser.add_argument("--inc", type=Path, default=HERE / "tiles.inc", help=pick(lang, "Données assembleur générées.", "Generated assembly data."))
    parser.add_argument("--map-source", type=Path, default=HERE / "map_packed.inc", help=pick(lang, "Données de la carte complète.", "Full world map source data."))
    parser.add_argument("--output", type=Path, help=pick(lang, "Fichier de destination (aperçu/export/carte).", "Destination file (preview/export/map)."))
    parser.add_argument("--force", action="store_true", help=pick(lang, "Autoriser l'écrasement lors d'un export BMP.", "Allow overwriting an exported BMP."))
    args = parser.parse_args()
    try:
        if args.action == "export":
            target = args.output or args.bmp
            if target.exists() and not args.force:
                raise TileError("Ce BMP existe déjà ; utiliser --force pour le remplacer.", "This BMP already exists; use --force to replace it.")
            write_bmp(target, read_inc(args.inc))
        elif args.action == "import":
            target = args.inc
            write_inc(target, read_bmp(args.bmp))
        elif args.action == "map":
            target = args.output or HERE / "map.bmp"
            preview = HERE / "docs/map_preview.png"
            write_map(target, read_bmp(args.bmp), args.map_source, preview)
            print(pick(args.lang, f"Aperçu ×4 : {preview}", f"Preview ×4: {preview}"))
        else:
            target = args.output or HERE / "docs/tiles_preview.png"
            write_preview(target, read_bmp(args.bmp))
        print(pick(args.lang, f"Terminé : {target}", f"Done: {target}"))
    except TileError as error:
        parser.error(pick(args.lang, error.fr, error.en))
    except OSError as error:
        parser.error(pick(args.lang, f"Erreur de fichier : {error}", f"File error: {error}"))


if __name__ == "__main__":
    main()
