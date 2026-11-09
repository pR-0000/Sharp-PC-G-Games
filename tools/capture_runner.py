"""FR/EN: capture Pocket Runner's actual g800 LCD, no Sharp ROM."""
from pathlib import Path
import hashlib,json,os,shutil,sys,tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'games/pocket-runner'
def main():
    parser=Parser('Capturer Pocket Runner dans g800.','Capture Pocket Runner in g800.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'),help='g800 / G800 / PATH')
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
    sys.path.insert(0,str(GAME))
    from check_runner import RunnerMachine
    from PIL import Image
    out=GAME/'docs';out.mkdir(exist_ok=True);reports=[]
    with tempfile.TemporaryDirectory(prefix='runner-lcd-') as folder:
        for scene,lang,level,pos in (('runner_fr','FR',0,88),('runner_trap','FR',0,88),('runner_en','EN',2,150)):
            m=RunnerMachine(lang);m.start();m.set_byte('level_index',level);m.routine('load_level')
            m.set_byte('player_pos',pos);m.set_word('score',40);m.set_byte('gold_flags',240);m.set_byte('gold_left',4)
            if scene=='runner_trap':
                m.tile(7,5,0);m.hole(0,107,48);m.guard(1,107,3,97)
            raw=bytearray(m.cpu.memory[0x100:m.sym['program_end']])
            draw,key=m.sym['draw_game'],m.sym['pcg_key_scan']
            raw[:9]=bytes((0xcd,draw&255,draw>>8,0xcd,key&255,key>>8,0xc3,3,1))
            fixture=Path(folder)/(scene+'.hex');fixture.write_text(intel_hex(raw,256),encoding='ascii')
            image=out/(scene+'_g800.png')
            report=capture(emulator,fixture,image,model='PC-G805' if lang=='EN' else 'PC-G801')
            report.update({'image':image.relative_to(ROOT).as_posix(),'language':lang,
                'scene':'Prepared gameplay state, actual game renderer; no physical Sharp.',
                'palette_colors':len(Image.open(image).getcolors(864*192)),
                'sha256':hashlib.sha256(image.read_bytes()).hexdigest()})
            reports.append(report)
    local=ROOT/'.local/pocket-runner';local.mkdir(parents=True,exist_ok=True)
    (local/'captures.json').write_text(json.dumps({'captures':reports,'rom_included':False,'inspection_states':True},indent=2)+'\n',encoding='utf-8')
    path=ROOT/'.local/lcd_capture_validation.json'
    all_reports=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'captures':[]}
    all_reports['captures']=[r for r in all_reports['captures'] if not r['image'].startswith('games/pocket-runner/')]+reports
    path.write_text(json.dumps(all_reports,indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Trois captures LCD enregistrées.','Three LCD captures saved.'))
if __name__=='__main__':main()
