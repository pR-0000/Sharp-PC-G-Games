"""FR/EN: shared Quest rules, model-specific editable bitmap artwork."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
ASSEMBLY=HERE.parents[1]
sys.path.insert(0,str(ASSEMBLY/'tools'))
from build import intel_hex,read_symbols
from cli_i18n import Parser,pick
from tiles_tool import read_bmp,write_inc,write_preview,write_map,TileError


def main():
    parser=Parser('Construire Quest FR/EN depuis les BMP editables.','Build Quest FR/EN from the editable BMP files.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    parser.add_argument('--typing-reload',type=int,default=None,
        help=pick(parser.lang,'Lectures clavier par unite (1–64 ; defaut G80X : 6, G850 : 12).',
                  'Keyboard polls per timeout unit (1–64; default G80X: 6, G850: 12).'))
    args=parser.parse_args()
    if args.typing_reload is not None and not 1<=args.typing_reload<=64:parser.error('--typing-reload: 1–64')
    assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    try:
        tiles=read_bmp(HERE/'tiles.bmp');write_inc(HERE/'tiles.inc',tiles)
        write_preview(HERE/'docs/tiles_preview.png',tiles)
        write_map(HERE/'map.bmp',tiles,preview_path=HERE/'docs/map_preview.png')
        if args.target!='g80x':
            spec=importlib.util.spec_from_file_location('quest_g850_assets',HERE/'targets/g850/assets.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.generate()
    except TileError as error:parser.error(pick(args.lang,error.fr,error.en))
    for target in ('g80x','g850') if args.target=='all' else (args.target,):
        native=target=='g850';output=HERE/'build'/('g850' if native else 'g80x')
        output.mkdir(parents=True,exist_ok=True)
        reload=args.typing_reload if args.typing_reload is not None else 12 if native else 6
        manifest={'name':'Sharp PC-G850 Quest' if native else 'Sharp PC-G80X Quest',
            'version':(HERE/'VERSION').read_text(encoding='utf-8').strip(),'origin':'0100','entry':'0100','sound':False,
            'target':'PC-G850' if native else 'PC-G801 / PC-G805','typing_reload':reload,
            'timing_reference':f'g800 0.11.4 {"PC-G850, 8000" if native else "PC-G801, 4000"} kHz, emulated IOCS',
            'tile_pixels':[8,8] if native else [5,7],'visible_tiles':[18,5] if native else [15,4],'programs':{}}
        for lang,value in (('FR',0),('EN',1)):
            base=output/f'quest_{"g850_" if native else ""}{lang}'
            subprocess.run([assembler,'--nologo','--color=off','--fullpath=rel',f'-DBUILD_LANG_EN={value}',
                f'-DTARGET_G850={int(native)}',f'-DTYPING_TICK_RELOAD={reload}',
                f'--inc={(ASSEMBLY/"include").as_posix()}',f'--inc={(ASSEMBLY/"lib").as_posix()}',
                f'--raw={base.as_posix()}.bin',f'--lst={base.as_posix()}.lst',
                f'--sym={base.as_posix()}.sym',(HERE/'quest.asm').as_posix()],cwd=HERE,check=True)
            binary=base.with_suffix('.bin').read_bytes();symbols=read_symbols(base.with_suffix('.sym'))
            assert symbols['entry']==256 and symbols['program_end']==256+len(binary)<=(0x7000 if native else 0x17E3)
            end=symbols['program_end']-1;user=min(end|255,0x76E2 if native else 0x17E2)
            base.with_suffix('.ihx').write_text(intel_hex(binary,256),encoding='ascii')
            manifest['programs'][base.name]={'bytes':len(binary),'last_address':f'{end:04X}',
                'user_command':f'USER{user:04X}','run_command':'G100','basic_command':'CALL &H100',
                'sha256_bin':hashlib.sha256(binary).hexdigest(),
                'sha256_ihx':hashlib.sha256(base.with_suffix('.ihx').read_bytes()).hexdigest()}
        reservation=max(int(p['user_command'][4:],16) for p in manifest['programs'].values())
        for name,program in manifest['programs'].items():
            program['user_command']=f'USER{reservation:04X}'
            print(f'Quest {target} {name}: {program["bytes"]} bytes / octets, USER{reservation:04X}, G100')
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
