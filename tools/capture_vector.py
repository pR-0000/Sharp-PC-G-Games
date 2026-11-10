"""FR/EN: capture the actual Z80 game renderer in g800, cropped to its LCD."""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture

ROOT=Path(__file__).resolve().parents[1];GAME=ROOT/'games/pocket-vector'


def main():
    parser=Parser('Capturer Pocket Vector dans g800 (LCD G850 uniquement).',
                  'Capture Pocket Vector in g800 (G850 LCD only).')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--animation',action='store_true')
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    sys.path.insert(0,str(GAME))
    from check_vector import VectorMachine
    from PIL import Image
    output=GAME/'docs';output.mkdir(exist_ok=True);reports=[]
    with tempfile.TemporaryDirectory(prefix='vector-lcd-') as folder:
        scenes=[]
        menu=VectorMachine();menu.start();scenes.append(('vector_menu',menu))
        grid=VectorMachine();grid.initialise();scenes.append(('vector_grid',grid))
        for name,lang,track,ticks in (('vector_fr','FR',0,24),('vector_curve','FR',1,40),('vector_en','EN',2,60)):
            m=VectorMachine(lang);m.byte('track_index',track);m.initialise(1)
            for _ in range(ticks):m.call('race_tick')
            # Choose the visible half of damage blinking for the overview photo.
            if m.byte('hurt_frames')&1:m.call('race_tick')
            scenes.append((name,m))
        spin=VectorMachine();spin.initialise()
        spin.byte('spin_frames',7);scenes.append(('vector_spin',spin))
        intro=VectorMachine();intro.initialise(1);intro.call('begin_start')
        for _ in range(8):intro.call('start_tick')
        scenes.append(('vector_intro',intro))
        arrival=VectorMachine();arrival.initialise(1);arrival.call('begin_arrival')
        for _ in range(8):arrival.call('start_tick')
        scenes.append(('vector_arrival',arrival))
        for stage,name in enumerate(('vector_count3','vector_count2','vector_count1','vector_go')):
            m=VectorMachine();m.initialise(1);m.call('begin_countdown')
            for _ in range(stage*7):m.call('start_tick')
            scenes.append((name,m))
        cup=VectorMachine();cup.initialise(1)
        for track in range(3):
            cup.byte('demo_mode',1)
            while cup.byte('phase') in (7,8,9):cup.call('start_tick')
            for _ in range(1800):
                cup.call('race_tick')
                if cup.byte('phase')!=1:break
            assert cup.byte('phase')==3
            if track==0:
                first=VectorMachine();first.initialise(1)
                for _ in range(1800):
                    first.call('race_tick')
                    if first.byte('phase')!=1:break
                assert first.byte('phase')==3
                scenes.append(('vector_result',first))
            cup.call('advance_result')
        assert cup.byte('phase')==6
        scenes.append(('vector_cup',cup))
        for name,m in scenes:
            data=bytearray(m.cpu.memory[256:m.sym['program_end']])
            target=m.sym['show_frame']
            data[:6]=bytes((0xCD,target&255,target>>8,0xC3,3,1))
            fixture=Path(folder)/(name+'.ihx');fixture.write_text(intel_hex(data,256),encoding='ascii')
            destination=output/(name+'_g800.png')
            staged=Path(folder)/(name+'.png')
            report=capture(emulator,fixture,staged,model='PC-G850')
            m.call('show_frame');expected=m.native_frame()
            thumb=Image.open(staged).resize((144,48),Image.Resampling.NEAREST)
            pixels=[thumb.getpixel((x,y)) for y in range(48) for x in range(144)]
            tones=sorted(set(pixels),key=sum)
            assert len(tones)==2,('Unexpected LCD palette',len(tones))
            wanted=[bool(expected[y//8*144+x]&(1<<(y&7))) for y in range(48) for x in range(144)]
            assert [pixel==tones[0] for pixel in pixels]==wanted,'g800 LCD differs from Z80 framebuffer'
            shutil.copyfile(staged,destination)
            report['framebuffer_match']=True
            report['image']=destination.relative_to(ROOT).as_posix()
            report['scene']='Actual Z80 game renderer, prepared race state; no physical hardware or Sharp ROM.'
            reports.append(report)
    if args.animation:
        # Execute the distributed CPU code; the GIF cadence is illustrative.
        m=VectorMachine();m.initialise(1);pictures=[]
        palette=sorted(Image.open(output/'vector_fr_g800.png').getcolors(864*288),
                       key=lambda item:sum(item[1]))
        black,white=palette[0][1],palette[-1][1]
        for _ in range(64):
            for _ in range(2):m.call('race_tick')
            m.call('show_frame');data=m.native_frame()
            image=Image.new('RGB',(144,48))
            image.putdata([black if data[y//8*144+x]&(1<<(y&7)) else white
                           for y in range(48) for x in range(144)])
            pictures.append(image.resize((864,288),Image.Resampling.NEAREST))
        pictures[0].save(output/'vector_demo_z80.gif',save_all=True,append_images=pictures[1:],
                         duration=240,loop=0,optimize=True)
        reports.append({'image':(output/'vector_demo_z80.gif').relative_to(ROOT).as_posix(),
                        'frames':64,'source':'Actual Z80 CPU execution; two game ticks per GIF frame, illustrative 240 ms cadence.'})
        # One real attack, eight consecutive game frames: four cardinal views twice.
        spin=VectorMachine();spin.initialise();spin.byte('control_pressed',32);spin.call('start_spin')
        pictures=[]
        for _ in range(8):
            spin.call('show_frame');data=spin.native_frame()
            image=Image.new('RGB',(144,48))
            image.putdata([black if data[y//8*144+x]&(1<<(y&7)) else white
                           for y in range(48) for x in range(144)])
            pictures.append(image.resize((864,288),Image.Resampling.NEAREST))
            spin.call('race_tick')
        assert spin.byte('spin_frames')==0
        pictures[0].save(output/'vector_spin_z80.gif',save_all=True,append_images=pictures[1:],
                         duration=140,loop=0,optimize=True)
        reports.append({'image':(output/'vector_spin_z80.gif').relative_to(ROOT).as_posix(),
                        'frames':8,'source':'One actual Z80 spin attack, four cardinal views twice; illustrative 140 ms per frame.'})
        intro=VectorMachine();intro.initialise(1);intro.call('begin_start');pictures=[]
        for _ in range(84):
            intro.call('show_frame');data=intro.native_frame()
            image=Image.new('RGB',(144,48))
            image.putdata([black if data[y//8*144+x]&(1<<(y&7)) else white
                           for y in range(48) for x in range(144)])
            pictures.append(image.resize((864,288),Image.Resampling.NEAREST))
            intro.call('start_tick' if intro.byte('phase') in (7,8,9) else 'race_tick')
        pictures[0].save(output/'vector_start_z80.gif',save_all=True,append_images=pictures[1:],
                         duration=140,loop=0,optimize=True)
        reports.append({'image':(output/'vector_start_z80.gif').relative_to(ROOT).as_posix(),
                        'frames':84,'source':'Actual Z80 empty orbit/grid arrival/countdown/start; illustrative 140 ms per frame.'})
    local=ROOT/'.local/pocket-vector';local.mkdir(parents=True,exist_ok=True)
    (local/'captures.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Captures LCD G850 enregistrees.','G850 LCD screenshots saved.'))


if __name__=='__main__':main()
