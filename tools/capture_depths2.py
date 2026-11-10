"""FR/EN: reproducible LCD-only captures of actual Pocket Depths 2 code.

Optional verification dependencies: z80==1.2.0, Pillow, external g800, Windows.
Inspection snapshots stay in a temporary directory; never ship as game HEX.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys
import tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture

ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'games/pocket-depths-2'

def main():
    parser=Parser('Capturer le LCD de Pocket Depths 2 dans g800.','Capture the Pocket Depths 2 LCD in g800.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'),
        help=pick(parser.lang,'Chemin g800, G800 ou PATH.','g800 path, G800 or PATH.'))
    parser.add_argument('--animation',action='store_true',
        help=pick(parser.lang,'Ajouter une animation de rotation (cadence illustrative).','Add a turning animation (illustrative cadence).'))
    args=parser.parse_args()
    emulator=shutil.which(args.emulator)
    if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
    sys.path.insert(0,str(GAME))
    from check_depths2 import Depths2Machine
    from PIL import Image
    output=GAME/'docs';output.mkdir(exist_ok=True)
    manifest={'captures':[],'rom_included':False,'inspection_states':True}
    def scene(name,x,y,angle,path,language='FR',model='PC-G801'):
        m=Depths2Machine(language);m.start()
        m.set_word('player_x',x);m.set_word('player_y',y);m.set_byte('angle',angle)
        data=bytearray(m.cpu.memory[0x100:m.sym['program_end']])
        target,key=m.sym['render'],m.sym['pcg_key_scan']
        # Snapshot entry only: CALL renderer, CALL key scan, JP scan.
        # All rendering routines and data come from the assembled game.
        data[:9]=bytes((0xcd,target&255,target>>8,0xcd,key&255,key>>8,0xc3,3,1))
        fixture=temporary/(name+'.ihx')
        fixture.write_text(intel_hex(data,0x100),encoding='ascii')
        report=capture(emulator,fixture,path,model=model)
        report.update({'image':path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
            'language':language,'scene':'Prepared camera, actual game renderer; no Sharp ROM or physical hardware.',
            'camera_q8_8':[x,y],'angle_units':angle,'palette_colors':len(Image.open(path).getcolors(864*192)),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        return report
    with tempfile.TemporaryDirectory(prefix='depths2-lcd-') as folder:
        temporary=Path(folder)
        for name,x,y,angle in (('hall',0x0380,0x0d80,208),('door',0x0580,0x0c80,0),('combat',0x0d80,0x0580,128)):
            manifest['captures'].append(scene(name,x,y,angle,output/f'depths2_{name}_g800.png'))
        manifest['captures'].append(scene('combat_en',0x0d80,0x0580,128,output/'depths2_combat_en_g800.png','EN','PC-G805'))
        if args.animation:
            pictures=[]
            angles=list(range(184,225,8))
            for i,angle in enumerate(angles):
                path=temporary/f'turn_{i}.png'
                scene('turn_'+str(i),0x0380,0x0d80,angle,path)
                pictures.append(Image.open(path).convert('RGB'))
            sequence=pictures+pictures[-2:0:-1]
            gif=output/'depths2_turn_g800.gif'
            sequence[0].save(gif,save_all=True,append_images=sequence[1:],duration=240,loop=0,optimize=True)
            manifest['animation']={'image':gif.relative_to(ROOT).as_posix(),'frames':len(sequence),
                'source':'Actual g800 LCD captures; prepared camera positions; illustrative 240 ms cadence, not a hardware benchmark.',
                'sha256':hashlib.sha256(gif.read_bytes()).hexdigest()}
    local=ROOT/'.local/pocket-depths-2';local.mkdir(parents=True,exist_ok=True)
    (local/'captures.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    validation_path=ROOT/'.local/lcd_capture_validation.json'
    validation=json.loads(validation_path.read_text(encoding='utf-8')) if validation_path.exists() else {'captures':[]}
    validation['captures']=[r for r in validation['captures'] if not r['image'].startswith('games/pocket-depths-2/')]+manifest['captures']
    validation_path.write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Captures LCD et provenance enregistrées.','LCD captures and provenance saved.'))

if __name__=='__main__':main()
