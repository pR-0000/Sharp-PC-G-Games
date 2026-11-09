"""FR/EN: build original Pocket Invaders; stdlib + SjASMPlus only."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import intel_hex,read_symbols
from cli_i18n import Parser,pick

def main():
    parser=Parser('Construire Pocket Invaders FR/EN.','Build Pocket Invaders FR/EN.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    args=parser.parse_args();assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    output=HERE/'build';output.mkdir(exist_ok=True)
    manifest={'name':'Pocket Invaders','version':'0.2.0','target':'PC-G801/G805; hardware testing pending',
              'origin':'0100','entry':'0100','playfield_pixels':[90,28],'hud':'right, five character columns',
              'formation_start_y':1,'initial_invasion_ticks':1210,'programs':{}}
    for language,value in (('FR',0),('EN',1)):
        base=output/f'invaders_{language}'
        subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',
            f'--inc={(ROOT/"include").as_posix()}',f'--raw={base.as_posix()}.bin',
            f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',(HERE/'invaders.asm').as_posix()],cwd=HERE,check=True)
        data=base.with_suffix('.bin').read_bytes();symbols=read_symbols(base.with_suffix('.sym'))
        assert symbols['entry']==0x100 and symbols['program_end']==len(data)+0x100<=0x17e3
        base.with_suffix('.hex').write_text(intel_hex(data,0x100),encoding='ascii')
        reserve=min((symbols['program_end']-1)|255,0x17e2)
        manifest['programs'][base.name]={'bytes':len(data),'last_address':f'{symbols["program_end"]-1:04X}',
            'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
            'sha256_bin':hashlib.sha256(data).hexdigest(),'sha256_hex':hashlib.sha256(base.with_suffix('.hex').read_bytes()).hexdigest()}
        print(f'Pocket Invaders {language}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
