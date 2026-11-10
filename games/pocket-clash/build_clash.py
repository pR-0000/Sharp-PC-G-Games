"""FR/EN: build original G850 platform fighter with Python stdlib + SjASMPlus."""
from pathlib import Path
import os,shutil,sys,hashlib,json,subprocess
from assets import generate
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import intel_hex,read_symbols
from cli_i18n import Parser

def main():
    parser=Parser('Construire Pocket Clash FR/EN.','Build Pocket Clash FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g850','g80x-32k'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    for target in ('g850','g80x-32k') if args.target=='all' else (args.target,):
        build_target(assembler,target)

def build_target(assembler,target):
    native=target=='g850'
    generate(target);output=HERE/'build'/('g850' if native else 'g80x-32k');output.mkdir(parents=True,exist_ok=True)
    spec={'name':'Pocket Clash','version':(HERE/'VERSION').read_text(encoding='ascii').strip(),'target':'PC-G850' if native else 'PC-G801 / PC-G805 (32 KiB)','origin':'0100','entry':'0100',
        'visible_pixels':[144,40],'characters':4,'arenas':3,'cup_battles':3,'sprite_scales':list(range(8,17)),
        'programs':{}}
    if not native:
        spec.update({'visible_pixels':[120,21],'sprite_scales':list(range(4,17)),'required_ram_kib':32,'lcd_pixels':[120,28]})
    for lang,value in (('FR',0),('EN',1)):
        base=output/f'clash_{"g850" if native else "g80x_32k"}_{lang}'
        subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',f'-DTARGET_G850={int(native)}',
            f'--inc={(ROOT/"include").as_posix()}',f'--inc={(ROOT/"lib").as_posix()}',
            f'--raw={base.as_posix()}.bin',f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',
            (HERE/'clash.asm').as_posix()],cwd=HERE,check=True)
        data=base.with_suffix('.bin').read_bytes();sym=read_symbols(base.with_suffix('.sym'))
        assert sym['entry']==256 and sym['program_end']==len(data)+256<=(0x7000 if native else 0x7600)
        base.with_suffix('.ihx').write_text(intel_hex(data,256),encoding='ascii')
        reserve=min((sym['program_end']-1)|255,0x76e2 if native else 0x77e2)
        spec['programs'][base.name]={'bytes':len(data),'last_address':f'{sym["program_end"]-1:04X}',
            'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
            'sha256_bin':hashlib.sha256(data).hexdigest(),'sha256_ihx':hashlib.sha256(base.with_suffix('.ihx').read_bytes()).hexdigest()}
        print(f'Pocket Clash {target} {lang}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
    (output/'manifest.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
