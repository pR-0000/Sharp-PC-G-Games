"""FR/EN: build Star Lane for G80X and G850 from shared sources."""
from pathlib import Path
import os,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_variants import build_variants
from cli_i18n import Parser

def main():
    parser=Parser('Construire Star Lane G80X/G850 FR/EN.','Build Star Lane G80X/G850 FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    build_variants(HERE,assembler,args.target,'star_lane',lambda native:{'name':'Star Lane','version':'0.2.0',
        'visible_pixels':[144,40] if native else [120,28],
        'lanes':5 if native else 3,'frame_bytes':864 if native else 480})
if __name__=='__main__':main()
