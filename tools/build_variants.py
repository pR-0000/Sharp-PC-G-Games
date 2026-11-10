"""FR/EN: common build, reservation and checksums for two-target games."""
from pathlib import Path
import hashlib,json,subprocess
from build import intel_hex,read_symbols


def build_variants(here,assembler,target,stem,metadata):
    here=Path(here);root=here.parents[1]
    for model in ('g80x','g850') if target=='all' else (target,):
        native=model=='g850';output=here/'build'/('g850' if native else 'g80x')
        output.mkdir(parents=True,exist_ok=True)
        manifest=dict(metadata(native));manifest.update({'target':'PC-G850' if native else 'PC-G801 / PC-G805',
            'origin':'0100','entry':'0100','programs':{}})
        for lang,value in (('FR',0),('EN',1)):
            base=output/f'{stem}_{"g850_" if native else ""}{lang}'
            subprocess.run([assembler,'--nologo','--color=off',f'-DBUILD_LANG_EN={value}',f'-DTARGET_G850={int(native)}',
                f'--inc={(root/"include").as_posix()}',f'--inc={(root/"lib").as_posix()}',
                f'--raw={base.as_posix()}.bin',f'--sym={base.as_posix()}.sym',f'--lst={base.as_posix()}.lst',
                (here/(stem+'.asm')).as_posix()],cwd=here,check=True)
            data=base.with_suffix('.bin').read_bytes();sym=read_symbols(base.with_suffix('.sym'))
            assert sym['entry']==256 and sym['program_end']==len(data)+256<=(0x7000 if native else 0x17e3)
            base.with_suffix('.ihx').write_text(intel_hex(data,256),encoding='ascii')
            reserve=min((sym['program_end']-1)|255,0x76e2 if native else 0x17e2)
            manifest['programs'][base.name]={'bytes':len(data),'last_address':f'{sym["program_end"]-1:04X}',
                'user_command':f'USER{reserve:04X}','run_command':'G100','basic_command':'CALL &H100',
                'sha256_bin':hashlib.sha256(data).hexdigest(),
                'sha256_ihx':hashlib.sha256(base.with_suffix('.ihx').read_bytes()).hexdigest()}
            print(f'{manifest["name"]} {model} {lang}: {len(data)} bytes / octets; USER{reserve:04X}, G100')
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
