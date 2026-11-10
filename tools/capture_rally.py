"""FR/EN: Pocket Rally LCD screenshots and smooth-scroll preview in g800."""
from pathlib import Path
import os,shutil,sys,tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'games/pocket-rally'

def main():
    parser=Parser('Capturer Pocket Rally dans g800.','Capture Pocket Rally in g800.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--animation',action='store_true',help=pick(parser.lang,'Apercu GIF du defilement.','GIF scrolling preview.'))
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
    sys.path.insert(0,str(GAME))
    from check_rally import RallyMachine,reference_driver
    from assets import ROUTES
    from PIL import Image
    output=GAME/'docs';output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rally-lcd-') as folder:
        def picture(machine,path):
            raw=bytearray(machine.cpu.memory[256:machine.sym['program_end']])
            draw,key=machine.sym['draw_game'],machine.sym['pcg_key_scan']
            raw[:9]=bytes((0xcd,draw&255,draw>>8,0xcd,key&255,key>>8,0xc3,3,1))
            fixture=Path(folder)/'scene.ihx';fixture.write_text(intel_hex(raw,256),encoding='ascii')
            capture(emulator,fixture,path,model='PC-G805')
        m=RallyMachine();m.start();pictures=[]
        for f in range(165):
            m.poll(reference_driver(m.car(),ROUTES[0]))
            if f==20:picture(m,output/'rally_start_g800.png')
            if f==80:picture(m,output/'rally_straight_g800.png')
            if f==128:picture(m,output/'rally_turn_g800.png')
            if args.animation and f in range(130,162,2):
                path=Path(folder)/f'frame_{f}.png';picture(m,path);pictures.append(Image.open(path).convert('RGB'))
        if pictures:pictures[0].save(output/'rally_scroll_g800.gif',save_all=True,append_images=pictures[1:],duration=160,loop=0,optimize=True)
        m=RallyMachine('EN');m.set_byte('track_index',1);m.start()
        for _ in range(170):m.poll(reference_driver(m.car(),ROUTES[1]))
        picture(m,output/'rally_chicane_en_g800.png')
    print(pick(args.lang,'Captures LCD enregistrees.','LCD screenshots saved.'))
if __name__=='__main__':main()
