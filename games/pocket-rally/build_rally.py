"""FR/EN: build Pocket Rally with shared rules and native target geometry."""
from pathlib import Path
import os,shutil,sys
from assets import generate
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'lib'))
from build_variants import build_variants
from cli_i18n import Parser


def main():
    parser=Parser('Construire Pocket Rally FR/EN.','Build Pocket Rally FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    generate()
    def metadata(native):
        return {'name':'Pocket Rally','version':'0.2.0','world_pixels':[192,128],
            'visible_pixels':[144,40] if native else [100,28],'frame_bytes':864 if native else 480,
            'levels':2,'graphics':'two-axis pixel scroll, shared 4x4 tiles and 7x7 cars, native-font HUD'}
    build_variants(HERE,assembler,args.target,'rally',metadata)


if __name__=='__main__':main()
