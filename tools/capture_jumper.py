"""FR/EN: render Pocket Jumper screenshots with g800, LCD only."""
from pathlib import Path
import os,shutil,sys,tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'games/pocket-jumper'

def main():
    parser=Parser('Capturer Pocket Jumper dans g800.','Capture Pocket Jumper in g800.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
    sys.path.insert(0,str(GAME))
    from check_jumper import JumperMachine
    output=GAME/'docs';output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='jumper-lcd-') as folder:
        for name,language,x,y in (('jumper_fr','FR',48,23),('jumper_jump','FR',190,17),('jumper_en','EN',388,28)):
            m=JumperMachine(language);m.start();m.position(x,y);m.set_byte('grace',0)
            m.set_byte('frame_count',4);m.set_word('score',140);m.set_byte('coins',4)
            raw=bytearray(m.cpu.memory[256:m.sym['program_end']])
            draw,key=m.sym['draw_game'],m.sym['pcg_key_scan']
            raw[:9]=bytes((0xcd,draw&255,draw>>8,0xcd,key&255,key>>8,0xc3,3,1))
            fixture=Path(folder)/(name+'.ihx');fixture.write_text(intel_hex(raw,256),encoding='ascii')
            capture(emulator,fixture,output/(name+'_g800.png'),model='PC-G805')
    print(pick(args.lang,'Captures LCD enregistrees.','LCD screenshots saved.'))
if __name__=='__main__':main()
