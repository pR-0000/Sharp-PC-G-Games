"""FR/EN: actual g800 LCD photos and an illustrative nine-scale camera animation."""
from pathlib import Path
import hashlib,json,os,shutil,sys,tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1];GAME=ROOT/'games/pocket-clash'

def main():
    parser=Parser('Capturer Pocket Clash dans g800.','Capture Pocket Clash in g800.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--animation',action='store_true')
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    sys.path.insert(0,str(GAME))
    from check_clash import ClashG850
    from PIL import Image
    reports=[]
    original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (GAME/'build/g850').glob('*.ihx')}
    with tempfile.TemporaryDirectory(prefix='clash-g800-') as folder:
        temporary=Path(folder)
        def scene(m,name,renderer='draw_game',output=None):
            m.routine(renderer)
            expected=m.pixels()
            data=bytearray(m.cpu.memory[256:m.sym['program_end']])
            target,key=m.sym[renderer],m.sym['pcg_key_scan']
            data[:9]=bytes((0xCD,target&255,target>>8,0xCD,key&255,key>>8,0xC3,3,1))
            fixture=temporary/(name+'.ihx');fixture.write_text(intel_hex(data,256),encoding='ascii')
            path=output or GAME/'docs'/(name+'_g800.png')
            result=capture(emulator,fixture,path,model='PC-G850')
            picture=Image.open(path).convert('RGB').resize((144,48),Image.Resampling.NEAREST)
            tones=sorted({color for count,color in picture.getcolors(144*48)},key=sum)
            assert len(tones)==2
            if renderer=='draw_game':
                for y in range(8,48):
                    for x in range(144):
                        assert (picture.getpixel((x,y))==tones[0])==bool(expected[y//8*144+x]&(1<<(y%8))),(name,x,y)
            result.update({'image':path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name,
                'scene':'Prepared camera/combat state; actual distributed Z80 renderer and g800 IOCS; no Sharp ROM.',
                'viewport_matches_z80':renderer=='draw_game','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            reports.append(result);return path
        for language in ('FR','EN'):
            m=ClashG850(language);scene(m,'clash_title_'+language.lower(),'title_screen')
        for index,selected in ((0,0),(1,1),(2,3)):
            m=ClashG850();m.set_byte('selected',selected);m.start();m.set_byte('round_index',index)
            m.routine('start_round');m.set_byte('countdown',0);m.set_byte('frame_count',4)
            floor=m.cpu.memory[m.sym['platforms']+2]-16
            m.fighter(0,x=86,y=floor,damage=37,attack=8,ground=1)
            m.fighter(1,x=113,y=floor,damage=68,ground=1,guard=int(index==2))
            m.set_byte('camera_ready',0);m.routine('update_camera')
            scene(m,'clash_arena'+str(index+1))
        m=ClashG850();m.tap(0x0b)
        for index in range(3):
            for frame in range(2600):
                if m.byte('phase')!=1:break
                m.routine('world_step')
            assert m.byte('phase') in (2,3)
            if index<2:m.tap(0x28)
        scene(m,'clash_standings','standings_screen')
        if args.animation:
            m=ClashG850();m.live();m.fighter(0,x=80,y=64,attack=8);m.fighter(1,x=135,y=64,guard=1)
            pictures=[]
            for n in range(8,17):
                m.set_byte('zoom_n',n);m.set_word('camera_x',(112-144*8//n)&65535)
                m.set_word('camera_y',(70-40*8//n)&65535)
                path=scene(m,'scale_'+str(n),output=temporary/f'scale_{n}.png')
                pictures.append(Image.open(path).convert('RGB'))
            sequence=pictures+pictures[-2:0:-1]
            output=GAME/'docs/clash_zoom_g800.gif'
            sequence[0].save(output,save_all=True,append_images=sequence[1:],duration=140,loop=0,optimize=True)
    assert original=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (GAME/'build/g850').glob('*.ihx')}
    folder=ROOT/'.local/pocket-clash';folder.mkdir(parents=True,exist_ok=True)
    (folder/'captures.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Captures LCD verifiees : ','Verified LCD captures: ')+str(len(reports)))
if __name__=='__main__':main()
