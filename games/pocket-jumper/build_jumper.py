"""FR/EN: build original Pocket Jumper, standard Python + SjASMPlus."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
from assets import generate
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import intel_hex,read_symbols
from cli_i18n import Parser
def main():
    parser=Parser('Construire Pocket Jumper FR/EN.','Build Pocket Jumper FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g80x','g850'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    generate()
    for target in ('g80x','g850') if args.target=='all' else (args.target,):
        native=target=='g850';output=HERE/'build'/('g850' if native else 'g80x')
        output.mkdir(parents=True,exist_ok=True)
        manifest={'name':'Pocket Jumper','version':'0.2.0','target':'PC-G850' if native else 'PC-G801 / PC-G805',
            'origin':'0100','entry':'0100','world_pixels':[768,64 if native else 48],
            'visible_pixels':[144,40] if native else [100,28],'frame_bytes':864 if native else 480,
            'levels':1,'graphics':'pixel framebuffer, shared 12x12 hero, scrolling, native-digit HUD','programs':{}}
        for lang,value in (('FR',0),('EN',1)):
            base=output/f'jumper_{"g850_" if native else ""}{lang}'
            subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',f'-DTARGET_G850={int(native)}',
                f'--inc={(ROOT/"include").as_posix()}',f'--inc={(ROOT/"lib").as_posix()}',f'--raw={base.as_posix()}.bin',
                f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',(HERE/'jumper.asm').as_posix()],cwd=HERE,check=True)
            data=base.with_suffix('.bin').read_bytes();sym=read_symbols(base.with_suffix('.sym'))
            assert sym['entry']==0x100 and sym['program_end']==len(data)+256<=(0x7000 if native else 0x17e3)
            base.with_suffix('.ihx').write_text(intel_hex(data,256),encoding='ascii')
            reserve=min((sym['program_end']-1)|255,0x76e2 if native else 0x17e2)
            manifest['programs'][base.name]={'bytes':len(data),'last_address':f'{sym["program_end"]-1:04X}',
                'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
                'sha256_bin':hashlib.sha256(data).hexdigest(),'sha256_ihx':hashlib.sha256(base.with_suffix('.ihx').read_bytes()).hexdigest()}
            print(f'Pocket Jumper {target} {lang}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()

