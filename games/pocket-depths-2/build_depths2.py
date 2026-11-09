"""FR/EN: build Pocket Depths 2, integer DDA for stock G801/G805."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
from assets import generate

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import intel_hex,read_symbols
from cli_i18n import Parser

def main():
    parser=Parser('Construire Pocket Depths 2 FR/EN.','Build Pocket Depths 2 FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    args=parser.parse_args()
    assembler=shutil.which(args.assembler)
    if not assembler: parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    generate()
    output=HERE/'build';output.mkdir(exist_ok=True)
    manifest={'name':'Pocket Depths 2','version':'0.1.0','target':'PC-G801 / PC-G805',
              'engine':'runtime fixed-point DDA, Q8.8, 40 rays, 256 angular units, 32 movement headings',
              'origin':'0100','entry':'0100','active_pixels':[120,28],'programs':{}}
    for language,value in (('FR',0),('EN',1)):
        base=output/f'depths2_{language}'
        subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',
            f'--inc={(ROOT/"include").as_posix()}',f'--raw={base.as_posix()}.bin',
            f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',(HERE/'depths2.asm').as_posix()],cwd=HERE,check=True)
        data=base.with_suffix('.bin').read_bytes();symbols=read_symbols(base.with_suffix('.sym'))
        assert symbols['entry']==0x100 and symbols['program_end']==len(data)+0x100<=0x17e3
        base.with_suffix('.hex').write_text(intel_hex(data,0x100),encoding='ascii')
        reserve=min((symbols['program_end']-1)|255,0x17e2)
        manifest['programs'][base.name]={'bytes':len(data),'last_address':f'{symbols["program_end"]-1:04X}',
            'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
            'sha256_bin':hashlib.sha256(data).hexdigest(),'sha256_hex':hashlib.sha256(base.with_suffix('.hex').read_bytes()).hexdigest()}
        print(f'Pocket Depths 2 {language}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
