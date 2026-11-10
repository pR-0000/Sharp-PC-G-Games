"""FR/EN: build the standalone PC-G850 monochrome racing prototype."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from assets import generate

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'lib'))
from build import intel_hex,read_symbols
from cli_i18n import Parser


def main():
    parser=Parser('Construire Pocket Vector FR/EN : G850 et G80X 32 Kio.','Build Pocket Vector FR/EN: G850 and 32 KiB G80X.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--target',choices=('all','g850','g80x-32k'),default='all')
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    for target in ('g850','g80x-32k') if args.target=='all' else (args.target,):
        build_target(assembler,target)

def build_target(assembler,target):
    native=target=='g850'
    generate(target);output=HERE/'build'/('g850' if native else 'g80x-32k');output.mkdir(parents=True,exist_ok=True)
    manifest={'name':'Pocket Vector','version':'0.7.0','target':'PC-G850' if native else 'PC-G801 / PC-G805 (32 KiB)','tracks':3,
              'engine':'Q8.8 scanline floorcaster, 64 headings, 2x1 floor, native sprites/HUD',
              'origin':'0100','entry':'0100','active_pixels':[144,48],'programs':{}}
    if not native:
        manifest.update({'active_pixels':[120,28],'internal_pixels':[144,48],
                         'floor_sampling':[2,2],'required_ram_kib':32,
                         'engine':'shared Q8.8 floorcaster, 2x2 floor, native 7-bit HUD/minimap'})
    for language,value in (('FR',0),('EN',1)):
        base=output/f'vector_{"g80x_32k_" if not native else ""}{language}'
        subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',f'-DTARGET_G850={int(native)}',
            f'--inc={(ROOT/"include").as_posix()}',f'--raw={base.as_posix()}.bin',
            f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',(HERE/'vector.asm').as_posix()],cwd=HERE,check=True)
        data=base.with_suffix('.bin').read_bytes();sym=read_symbols(base.with_suffix('.sym'))
        assert sym['entry']==0x100 and sym['program_end']==len(data)+0x100<=(0x7000 if native else 0x7600)
        base.with_suffix('.ihx').write_text(intel_hex(data,0x100),encoding='ascii')
        last=sym['program_end']-1;reserve=last|255
        manifest['programs'][base.name]={'bytes':len(data),'last_address':f'{last:04X}',
            'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
            'sha256_bin':hashlib.sha256(data).hexdigest(),'sha256_ihx':hashlib.sha256(base.with_suffix('.ihx').read_bytes()).hexdigest()}
        print(f'Pocket Vector {target} {language}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
