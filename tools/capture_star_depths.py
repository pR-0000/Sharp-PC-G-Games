"""FR/EN: LCD-only G80X photos, checked against the distributed Z80 renderer."""
from pathlib import Path
import json,os,shutil,sys,tempfile
from cli_i18n import Parser
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=Parser('Capturer Star Lane et Pocket Depths G80X.','Capture Star Lane and Pocket Depths G80X.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    sys.path.insert(0,str(ROOT/'games/star-lane'))
    from check_star import StarMachine
    sys.path.insert(0,str(ROOT/'games/pocket-depths'))
    from check_depths import DepthsMachine
    from PIL import Image
    scenes=[];reports=[]
    m=StarMachine();m.start();m.set_word('score',425);m.set_byte('combo',3)
    m.set_byte('shot_x',8);m.set_byte('shot_lane',1)
    for lane,col,tile in ((0,9,1),(0,18,3),(1,15,4),(2,7,5),(2,13,3),(2,22,6)):
        m.set_tile(lane,col,tile)
    scenes.append(('star-lane','star_lane','PC-G801',m,'draw_game',range(7,28)))
    for name,lite,x,y in (('depths_hall',False,4,7),('depths_combat',False,4,6),('depths_lite',True,4,7)):
        m=DepthsMachine(lite=lite);m.start();m.set_byte('player_x',x);m.set_byte('player_y',y)
        scenes.append(('pocket-depths',name,'PC-G801' if lite else 'PC-G805',m,'render',range(21)))
    with tempfile.TemporaryDirectory(prefix='star-depths-lcd-') as folder:
        temporary=Path(folder)
        for game,name,model,m,renderer,ys in scenes:
            # Star does not need an isolated-routine helper for this snapshot.
            data=bytearray(m.cpu.memory[256:m.sym['program_end']])
            draw,key=m.sym[renderer],m.sym['pcg_key_scan']
            data[:9]=bytes((0xCD,draw&255,draw>>8,0xCD,key&255,key>>8,0xC3,3,1))
            fixture=temporary/(name+'.ihx');fixture.write_text(intel_hex(data,256),encoding='ascii')
            path=ROOT/'games'/game/'docs'/(name+'_g800.png')
            report=capture(emulator,fixture,path,model=model)
            # Decode pixels from a separate CPU run of the same snapshot.
            from check_programs import Machine
            (temporary/(name+'.bin')).write_bytes(data)
            shutil.copyfile((ROOT/'games'/game/'build/g80x')/
                (('star_lane_FR' if game=='star-lane' else 'depths_lite_FR' if m.lite else 'depths_FR')+'.sym'),temporary/(name+'.sym'))
            actual=Machine(name,temporary)
            frame=m.sym['frame_buffer']
            expected=bytes(actual.cpu.memory[frame:frame+480])
            picture=Image.open(path).convert('RGB').resize((144,32),Image.Resampling.NEAREST)
            tones=sorted({color for count,color in picture.getcolors(144*32)},key=sum);assert len(tones) in (2,3)
            for y in ys:
                for x in range(120):
                    wanted=bool(expected[y//7*120+x]&(1<<(y%7)))
                    assert (picture.getpixel((x+x//5,y+y//7))==tones[0])==wanted,(name,x,y)
            report.update({'image':path.relative_to(ROOT).as_posix(),'viewport_matches_z80':True})
            reports.append(report)
    folder=ROOT/'.local/star-depths';folder.mkdir(parents=True,exist_ok=True)
    (folder/'captures.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print('LCD / Z80: '+str(len(reports)))
if __name__=='__main__':main()
