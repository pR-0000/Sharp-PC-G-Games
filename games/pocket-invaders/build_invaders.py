"""FR/EN: build Pocket Invaders for both Sharp display families."""
from pathlib import Path
import os,shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from cli_i18n import Parser
from build_variants import build_variants


def main():
    parser=Parser('Construire Pocket Invaders FR/EN.','Build Pocket Invaders FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    def metadata(native):
        return {'name':'Pocket Invaders','version':'0.3.0',
            'playfield_pixels':[108,48] if native else [90,28],'frame_bytes':864 if native else 480,
            'hud':'right, native font','aliens':16,'formation_start_y':3 if native else 1,
            'initial_invasion_ticks':1885 if native else 1210,'simultaneous_controls':native}
    build_variants(HERE,assembler,args.target,'invaders',metadata)


if __name__=='__main__':main()
