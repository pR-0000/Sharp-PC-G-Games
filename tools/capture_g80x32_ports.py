"""FR/EN: capture real g800 E200-family LCD output for the 32 KiB ports."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
from build import intel_hex
from capture_lcd import capture
from cli_i18n import Parser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from check_g80x32_ports import Vector80X,Clash80X


def main():
    parser=Parser('Capturer les portages G80X 32 Kio.','Capture the 32 KiB G80X ports.')
    parser.add_argument('--emulator',required=True)
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator')
    from PIL import Image
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for g in ('pocket-vector','pocket-clash')
            for p in (ROOT/'games'/g/'build').rglob('*.ihx')}
    reports=[]
    with tempfile.TemporaryDirectory(prefix='g80x-32k-lcd-') as folder:
        def snap(m,game,name,renderer,vector=False):
            if vector:
                ticks=m.call(renderer);expected=bytes(m.display)
                show,key=m.sym['g80x_upload'],m.sym['pcg_key_scan']
            else:
                m.routine(renderer);expected=b''.join(m.screen)
                show,key=m.sym[renderer],m.sym['pcg_key_scan'];ticks=None
            data=bytearray(m.cpu.memory[256:m.sym['program_end']])
            data[:9]=bytes((0xCD,show&255,show>>8,0xCD,key&255,key>>8,0xC3,3,1))
            fixture=Path(folder)/(name+'.ihx');fixture.write_text(intel_hex(data,256),encoding='ascii')
            out=ROOT/'games'/game/'docs'/(name+'_g800.png')
            result=capture(emulator,fixture,out,model='PC-G801')
            picture=Image.open(out).convert('RGB').resize((144,32),Image.Resampling.NEAREST)
            tones=sorted({color for _,color in picture.getcolors(144*32)},key=sum)
            checked=0
            if vector or renderer=='draw_game':
                for y in range(0 if vector else 7,28):
                    for x in range(120):
                        physical=(x//5*6+x%5,y//7*8+y%7)
                        actual=picture.getpixel(physical)==tones[0]
                        wanted=bool(expected[y//7*120+x]&(1<<(y%7)))
                        assert actual==wanted,(name,x,y,actual,wanted)
                        checked+=1
            result.update({'image':out.relative_to(ROOT).as_posix(),'target':'G80X with 32 KiB',
                           'logical_pixels':[120,28],'verified_pixels':checked,
                           'cpu_tstates_excluding_rom':ticks})
            reports.append(result)
        for language in ('FR','EN'):
            m=Vector80X(language);m.initialise();m.byte('phase',0)
            if language=='FR':snap(m,'pocket-vector','vector_g80x_menu_fr','show_frame',True)
            m.byte('phase',1);snap(m,'pocket-vector','vector_g80x_'+language.lower(),'show_frame',True)
        m=Vector80X();m.initialise(1)
        for _ in range(200):m.call('race_tick')
        snap(m,'pocket-vector','vector_g80x_curve','show_frame',True)
        for language in ('FR','EN'):
            m=Clash80X(language)
            snap(m,'pocket-clash','clash_g80x_title_'+language.lower(),'title_screen')
        for index,selected in ((0,0),(1,2),(2,3)):
            m=Clash80X();m.set_byte('selected',selected);m.start();m.set_byte('round_index',index)
            m.routine('start_round');m.set_byte('countdown',0);m.set_byte('frame_count',4)
            floor=m.cpu.memory[m.sym['platforms']+2]-16
            m.fighter(0,x=86,y=floor,damage=37,attack=8,ground=1)
            m.fighter(1,x=113,y=floor,damage=68,ground=1)
            m.set_byte('camera_ready',0);m.routine('update_camera')
            snap(m,'pocket-clash','clash_g80x_arena'+str(index+1),'draw_game')
    assert all(hashlib.sha256(path.read_bytes()).hexdigest()==digest for path,digest in before.items())
    dest=ROOT/'.local/g80x-32k-ports';dest.mkdir(parents=True,exist_ok=True)
    (dest/'captures.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'captures':len(reports),'verified_logical_pixels':sum(r['verified_pixels'] for r in reports)}))


if __name__=='__main__':main()
