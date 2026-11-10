"""FR/EN: common Runner gameplay with native graphics for each display."""
from pathlib import Path
import importlib.util,os,shutil,sys
from assets import generate
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from cli_i18n import Parser
from build_variants import build_variants


def main():
    parser=Parser('Construire Pocket Runner FR/EN.','Build Pocket Runner FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    generate()
    if args.target!='g80x':
        spec=importlib.util.spec_from_file_location('runner_g850_assets',HERE/'targets/g850/assets.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.generate()
    def metadata(native):
        return {'name':'Pocket Runner','version':'0.2.0','world_cells':[20,12],
            'visible_cells':[20,5] if native else [20,4],'tile_pixels':[7,8] if native else [5,7],
            'frame_bytes':864 if native else 480,'levels':3,
            'graphics':'original tiles, vertical scrolling, native-digit HUD'}
    build_variants(HERE,assembler,args.target,'runner',metadata)


if __name__=='__main__':main()
