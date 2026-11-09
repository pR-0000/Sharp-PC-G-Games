"""FR/EN: editable BMP round trips and real assembly after a pixel edit."""
from pathlib import Path
from contextlib import contextmanager
import json,os,shutil,subprocess,tempfile,unittest,sys
import assets,asset_tool
from assets import ROOT,BLACK,WHITE,COLOURS,WIDTH,HEIGHT
from bitmap import read_bmp,write_bmp
from build import read_symbols
from cli_i18n import Parser
ASSEMBLER=None

@contextmanager
def sandbox():
    old,old_tool=assets.HERE,asset_tool.HERE
    with tempfile.TemporaryDirectory(prefix='jumper-assets-') as folder:
        assets.HERE=asset_tool.HERE=Path(folder)
        try:yield Path(folder)
        finally:assets.HERE,asset_tool.HERE=old,old_tool

class AssetChecks(unittest.TestCase):
    def test_default_atlas_level_and_metadata_round_trip(self):
        with sandbox() as folder:
            self.assertEqual(assets.art(),assets.default_art())
            self.assertEqual(assets.level(),assets.default_level())
            assets.generate()
            self.assertEqual(read_bmp(folder/'sprites.bmp')[:2],(12,180))
            self.assertEqual(read_bmp(folder/'level_01.bmp')[:2],(768,48))
            spec=json.loads((folder/'sprites.json').read_text())
            self.assertEqual(len(spec['frames']),15);self.assertEqual(len(spec['level_palette']),9)
    def test_source_bitmaps_never_overwritten_by_generate(self):
        with sandbox() as folder:
            assets.generate();paths=[folder/'sprites.bmp',folder/'level_01_layout.bmp',folder/'level_01.json']
            before=[p.read_bytes() for p in paths];assets.generate()
            self.assertEqual([p.read_bytes() for p in paths],before)
    def test_padding_colours_dimensions_and_air_are_rejected(self):
        with sandbox() as folder:
            assets.generate();path=folder/'sprites.bmp';w,h,pixels=read_bmp(path)
            for index,value in ((0,BLACK),(8,BLACK),(12*12, (1,2,3))):
                changed=list(pixels);changed[index]=value;write_bmp(path,w,h,changed)
                with self.assertRaises(ValueError):assets.art()
            write_bmp(path,1,1,[WHITE])
            with self.assertRaises(ValueError):assets.art()
    def test_layout_colours_dimensions_and_patrol_bounds(self):
        with sandbox() as folder:
            assets.generate();path=folder/'level_01_layout.bmp'
            write_bmp(path,WIDTH,HEIGHT,[(1,2,3)]*(WIDTH*HEIGHT))
            with self.assertRaises(ValueError):assets.level()
            write_bmp(path,1,1,[WHITE])
            with self.assertRaises(ValueError):assets.level()
            path=folder/'level_01.json';spec=json.loads(path.read_text());spec['enemies'][0]['x']=999
            path.write_text(json.dumps(spec))
            with self.assertRaises(ValueError):assets.level_spec()
    def test_rendered_map_import_round_trip(self):
        with sandbox() as folder:
            assets.generate();expected=assets.level();path=folder/'level_01.bmp'
            asset_tool.import_map(path);self.assertEqual(assets.level(),expected)
            w,h,pixels=read_bmp(path);coin=assets.art()['tile_coin']
            for y in range(8):
                for x in range(8):pixels[y*w+x]=BLACK if coin[y][x]=='#' else WHITE
            write_bmp(path,w,h,pixels);asset_tool.import_map(path)
            self.assertEqual(assets.level()[0],4)
    def test_failed_import_keeps_original_layout(self):
        with sandbox() as folder:
            assets.generate();layout=folder/'level_01_layout.bmp';before=layout.read_bytes()
            path=folder/'level_01.bmp';w,h,pixels=read_bmp(path);pixels[0]=BLACK;write_bmp(path,w,h,pixels)
            with self.assertRaises(ValueError):asset_tool.import_map(path)
            self.assertEqual(layout.read_bytes(),before)
    def test_pixel_and_layout_edit_reach_assembled_binary(self):
        with sandbox() as folder:
            # Mirror the include layout in a disposable workspace.
            game=folder/'games/pocket-jumper';game.mkdir(parents=True)
            (folder/'include').mkdir();(folder/'lib').mkdir()
            for path in (ROOT/'include').glob('*.inc'):shutil.copy2(path,folder/'include'/path.name)
            shutil.copy2(ROOT/'lib/pcg801_runtime.asm',folder/'lib/pcg801_runtime.asm')
            for path in (ROOT/'games/pocket-jumper').glob('*.asm'):shutil.copy2(path,game/path.name)
            assets.HERE=asset_tool.HERE=game;assets.generate()
            def compile():
                subprocess.run([ASSEMBLER,'--nologo','--color=off','-DBUILD_LANG_EN=0',
                    f'--inc={(folder/"include").as_posix()}',f'--raw={(game/"test.bin").as_posix()}',
                    f'--sym={(game/"test.sym").as_posix()}',(game/'jumper.asm').as_posix()],cwd=game,check=True,capture_output=True)
                return (game/'test.bin').read_bytes(),read_symbols(game/'test.sym')
            before,sym=compile()
            path=game/'sprites.bmp';w,h,pixels=read_bmp(path);pixels[9*12*12]=BLACK
            write_bmp(path,w,h,pixels)
            path=game/'level_01_layout.bmp';w,h,pixels=read_bmp(path);pixels[0]=COLOURS[3]
            write_bmp(path,w,h,pixels);assets.generate();after,sym2=compile()
            self.assertEqual(sym,sym2)
            changed={i+256 for i,(a,b) in enumerate(zip(before,after)) if a!=b}
            self.assertEqual(changed,{sym['hero_a'],sym['hero_a_left']+22,sym['level_initial']})

def main():
    global ASSEMBLER
    parser=Parser('Verifier les BMP et leur assemblage.','Verify BMP assets and assembly.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    args=parser.parse_args();ASSEMBLER=shutil.which(args.assembler)
    if not ASSEMBLER:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
