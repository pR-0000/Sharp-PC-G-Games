"""FR : tests du BMP éditable. EN: editable BMP checks. No dependencies."""
from pathlib import Path
import struct
import hashlib
import subprocess
import sys
import tempfile
import unittest

from tiles_tool import read_inc, read_bmp, write_bmp, write_inc, write_preview, read_map, write_map, TileError
from cli_i18n import Parser, pick

HERE=Path(__file__).resolve().parent


class TileChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/"tiles.bmp"
        self.tiles=read_bmp(HERE/"tiles.bmp")
        write_bmp(self.path,self.tiles)

    def tearDown(self):
        self.temp.cleanup()

    def test_bmp_matches_inc_and_generated_assembly(self):
        self.assertEqual(self.tiles,read_inc(HERE/"tiles.inc"))
        generated=self.path.with_suffix(".inc")
        write_inc(generated,self.tiles)
        self.assertEqual(read_inc(generated),self.tiles)
        self.assertEqual(len(self.tiles),23)

    def test_asymmetric_pixel_edit_keeps_orientation_and_tile_id(self):
        edited=list(self.tiles)
        tile=bytearray(edited[22]);tile[4]^=1;edited[22]=bytes(tile)
        write_bmp(self.path,edited)
        self.assertEqual(read_bmp(self.path),edited)
        self.assertEqual(read_bmp(self.path)[:22],self.tiles[:22])
        data=self.path.read_bytes()
        # Tile 22, top-right -> visual y=154, x=4; BMP stores bottom row first.
        pixel=54+(160-154)*16+4*3
        expected=0 if edited[22][4]&1 else 255
        self.assertEqual(data[pixel:pixel+3],bytes((expected,))*3)

    def test_top_down_bmp(self):
        data=bytearray(self.path.read_bytes())
        struct.pack_into("<i",data,22,-161)
        rows=[data[54+p*16:54+(p+1)*16] for p in range(161)]
        data[54:]=b"".join(reversed(rows))
        self.path.write_bytes(data)
        self.assertEqual(read_bmp(self.path),self.tiles)

    def test_indexed_monochrome_palettes(self):
        for depth in (1,4,8):
            stride=((5*depth+31)//32)*4
            raw=bytearray()
            for y in reversed(range(161)):
                row=bytearray(stride)
                for x in range(5):
                    black=int(bool(self.tiles[y//7][x]&(1<<(y%7))))
                    row[x*depth//8]|=black<<(8-depth-(x*depth%8))
                raw.extend(row)
            header=struct.pack("<2sIHHI",b"BM",62+len(raw),0,0,62)
            header+=struct.pack("<IiiHHIIiiII",40,5,161,1,depth,0,len(raw),2835,2835,2,0)
            self.path.write_bytes(header+bytes((255,255,255,0,0,0,0,0))+raw)
            self.assertEqual(read_bmp(self.path),self.tiles)

    def test_wrong_size_compression_and_truncation_rejected(self):
        original=self.path.read_bytes()
        for offset,value in ((18,6),(22,160),(30,1)):
            data=bytearray(original);struct.pack_into("<i",data,offset,value)
            self.path.write_bytes(data)
            with self.assertRaises(TileError):read_bmp(self.path)
        self.path.write_bytes(original[:-16])
        with self.assertRaises(TileError):read_bmp(self.path)

    def test_antialiased_or_colored_pixels_rejected(self):
        data=bytearray(self.path.read_bytes());data[54:57]=bytes((127,127,127))
        self.path.write_bytes(data)
        with self.assertRaises(TileError):read_bmp(self.path)

    def test_export_protects_existing_edited_bitmap(self):
        original=self.path.read_bytes()
        result=subprocess.run([sys.executable,str(HERE/"tiles_tool.py"),"export","--bmp",str(self.path),"--lang","en"],capture_output=True,text=True,encoding="utf-8")
        self.assertNotEqual(result.returncode,0)
        self.assertIn("already exists",result.stderr)
        self.assertEqual(original,self.path.read_bytes())

    def test_bilingual_help_and_preview(self):
        for language,word in (("fr","Exporter/importer"),("en","Export/import")):
            result=subprocess.run([sys.executable,str(HERE/"tiles_tool.py"),"--lang",language,"--help"],capture_output=True,text=True,encoding="utf-8",check=True)
            self.assertIn(word,result.stdout)
        output=self.path.with_suffix(".png")
        write_preview(output,self.tiles)
        self.assertTrue(output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(struct.unpack_from(">II",output.read_bytes(),16),(420,1244))

    def test_full_map_pixels_and_eight_chunk_placement(self):
        rows=read_map(HERE/"map_packed.inc")
        packed=bytes((row[x]<<4)|row[x+1] for row in rows for x in range(0,30,2))
        self.assertEqual(hashlib.sha256(packed).hexdigest(),
                         "b10460c259318e0543a15f9f2a7e825c438a477b279eec37927e85b4faa7f0eb")
        # Fixed world coordinates: ruins, forest, village, castle halves, graveyard, tower.
        for x,y,tile in ((16,2,5),(3,6,7),(12,6,4),(3,13,2),(4,13,3),(18,13,6),(27,13,8)):
            self.assertEqual(rows[y][x],tile)
        output=self.path.with_name("map.bmp")
        preview=self.path.with_name("map.png")
        write_map(output,self.tiles,preview_path=preview)
        data=output.read_bytes()
        self.assertEqual(struct.unpack_from("<iiHHI",data,18),(150,112,1,24,0))
        offset=struct.unpack_from("<I",data,10)[0]
        stride=452
        self.assertEqual(len(data),offset+112*stride)
        # Reassemble each 15x4 screen independently; verify every pixel, including seams.
        for cy in range(4):
            for cx in range(2):
                for ty in range(4):
                    for tx in range(15):
                        columns=self.tiles[rows[cy*4+ty][cx*15+tx]]
                        for py in range(7):
                            for px in range(5):
                                x=(cx*15+tx)*5+px
                                y=(cy*4+ty)*7+py
                                start=offset+(111-y)*stride+x*3
                                color=0 if columns[px]&(1<<py) else 255
                                self.assertEqual(data[start:start+3],bytes((color,))*3)
        self.assertEqual(struct.unpack_from(">II",preview.read_bytes(),16),(600,448))

    def test_invalid_map_dimensions_and_sprite_ids_rejected(self):
        source=(HERE/"map_packed.inc").read_text(encoding="utf-8")
        path=self.path.with_suffix(".inc")
        for invalid in (source.replace("$99", "$F9", 1), source.rsplit("\n",2)[0], source.replace("$99", "$9", 1)):
            path.write_text(invalid,encoding="utf-8")
            with self.assertRaises(TileError):read_map(path)


if __name__=="__main__":
    parser=Parser("Vérifier l'atlas BMP, sa conversion assembleur et la carte complète.","Check the BMP atlas, its assembly conversion and the full world map.")
    args=parser.parse_args()
    print(pick(args.lang,"Vérification des motifs BMP et de la carte complète.","BMP pattern and full world map checks."),flush=True)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TileChecks))
    raise SystemExit(not result.wasSuccessful())
