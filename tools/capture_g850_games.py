"""FR/EN: LCD-only photos of distributed G850 renderers, checked pixel by pixel."""
from pathlib import Path
import importlib.util,json,os,shutil,sys,tempfile
from cli_i18n import Parser,pick
from build import intel_hex
from capture_lcd import capture
ROOT=Path(__file__).resolve().parents[1]


def load_checks(game,name):
    folder=ROOT/'games'/game;sys.path.insert(0,str(folder))
    sys.modules.pop('assets',None)  # each game owns its asset module
    spec=importlib.util.spec_from_file_location(name,folder/'check_g850.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def main():
    parser=Parser('Capturer les jeux G850, LCD uniquement.','Capture G850 games, LCD only.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--game',choices=('all','jumper','depths2','quest','invaders','runner','rally','star','depths'),default='all')
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    from PIL import Image
    scenes=[];reports=[]
    if args.game in ('all','jumper'):
        module=load_checks('pocket-jumper','jumper_g850_checks')
        for name,language,x,y in (('jumper_g850_fr','FR',80,36),('jumper_g850_jump','FR',190,32),
                                   ('jumper_g850_en','EN',448,44)):
            m=module.JumperG850(language);m.start();m.position(x,y)
            m.set_byte('grace',0);m.set_byte('frame_count',4);m.set_word('score',140);m.set_byte('coins',4)
            scenes.append(('pocket-jumper',name,m,'draw_game'))
    if args.game in ('all','depths2'):
        module=load_checks('pocket-depths-2','depths_g850_checks')
        for name,language,x,y,angle in (('depths2_g850_hall','FR',0x0380,0x0D80,208),
            ('depths2_g850_door','FR',0x0580,0x0C80,0),('depths2_g850_combat','FR',0x0D80,0x0580,128),
            ('depths2_g850_en','EN',0x0D80,0x0580,128)):
            m=module.DepthsG850(language);m.start()
            m.set_word('player_x',x);m.set_word('player_y',y);m.set_byte('angle',angle)
            scenes.append(('pocket-depths-2',name,m,'render'))
    if args.game in ('all','quest'):
        module=load_checks('quest','quest_g850_checks')
        for name,language,x,y in (('quest_g850_map','FR',5,13),('quest_g850_forest','FR',6,6),
                                  ('quest_g850_map_en','EN',16,2)):
            m=module.QuestG850(language);m.start();m.place(x,y)
            scenes.append(('quest',name,m,'world_redraw_map_with_player'))
        for language in ('FR','EN'):
            m=module.QuestG850(language);m.start();m.set_byte('player_level',4)
            m.set_byte('player_atk_bonus',1);m.routine('progress_sync_player_stats_from_level')
            m.set_byte('player_hp_cur',m.byte('player_hp_max'));m.place(17,13);m.tap(0x22)
            scenes.append(('quest','quest_g850_battle_'+language.lower(),m,'battle_show_menu',
                [(12,8,16,16),(108,8,16,16)]))
    if args.game in ('all','invaders'):
        module=load_checks('pocket-invaders','invaders_g850_checks')
        for language in ('FR','EN'):
            m=module.InvadersG850(language);m.start();m.set_byte('formation_y',7)
            m.set_byte('player_x',43);m.set_byte('shot_x',47);m.set_byte('shot_y',28)
            m.cpu.memory[m.sym['bombs']:m.sym['bombs']+2]=bytes((78,31))
            m.set_word('score',240);m.set_byte('wave',2)
            scenes.append(('pocket-invaders','invaders_g850_'+language.lower(),m,'draw_game',[(0,0,108,48)]))
    if args.game in ('all','runner'):
        module=load_checks('pocket-runner','runner_g850_checks')
        for language,row in (('FR',10),('EN',4)):
            m=module.RunnerG850(language);m.start();m.set_byte('player_pos',row*20+9)
            m.set_word('score',250)
            scenes.append(('pocket-runner','runner_g850_'+language.lower(),m,'draw_game'))
    if args.game in ('all','rally'):
        module=load_checks('pocket-rally','rally_g850_checks')
        for name,language,index,x,y,angle in (
            ('rally_g850_grid','FR',0,44,24,0),('rally_g850_curve','FR',0,151,29,2),
            ('rally_g850_en','EN',1,164,88,4)):
            m=module.RallyG850(language);m.set_byte('track_index',index);m.start()
            m.position(0,x,y,angle=angle,speed=5)
            if name!='rally_g850_grid':
                m.position(1,164,44,angle=4);m.position(2,153,25,angle=1)
                m.set_word('race_ticks',125);m.routine('update_rank')
            for _ in range(60):m.routine('update_camera')
            scenes.append(('pocket-rally',name,m,'draw_game'))
    if args.game in ('all','star'):
        module=load_checks('star-lane','star_g850_checks')
        for language in ('FR','EN'):
            m=module.StarG850(language);m.start();m.set_word('score',1325)
            m.set_byte('sector',4);m.set_byte('combo',3);m.set_byte('shot_x',8);m.set_byte('shot_lane',2)
            for lane,col,tile in ((0,8,1),(0,18,3),(1,12,2),(1,20,1),(2,15,4),
                (3,7,5),(3,13,3),(3,21,6),(4,11,1),(4,19,2)):
                m.set_tile(lane,col,tile)
            scenes.append(('star-lane','star_lane_g850_'+language.lower(),m,'draw_game'))
    if args.game in ('all','depths'):
        module=load_checks('pocket-depths','depths1_g850_checks')
        for name,language,x,y,heading in (('depths_g850_combat','FR',4,7,0),
            ('depths_g850_hall','FR',10,4,3),('depths_g850_en','EN',11,7,0)):
            m=module.DepthsG850(language);m.start()
            m.set_byte('player_x',x);m.set_byte('player_y',y);m.set_byte('direction',heading)
            scenes.append(('pocket-depths',name,m,'render',[(0,0,144,40)]))
    with tempfile.TemporaryDirectory(prefix='g850-games-lcd-') as folder:
        temporary=Path(folder)
        for game,name,m,renderer,*options in scenes:
            battle=renderer=='battle_show_menu'
            if not battle:m.routine(renderer)
            expected=b''.join(m.screen) if battle else m.pixels()
            regions=options[0] if options else [(0,8,144,40)]
            data=bytearray(m.cpu.memory[256:m.sym['program_end']])
            draw,key=m.sym[renderer],m.sym['pcg_key_scan']
            if battle:
                scene=m.sym['battle_draw_scene']
                data[:6]=bytes((0xCD,scene&255,scene>>8,0xC3,draw&255,draw>>8))
            else:data[:9]=bytes((0xCD,draw&255,draw>>8,0xCD,key&255,key>>8,0xC3,3,1))
            fixture=temporary/(name+'.ihx');fixture.write_text(intel_hex(data,256),encoding='ascii')
            staged=temporary/(name+'.png')
            report=capture(emulator,fixture,staged,model='PC-G850')
            thumb=Image.open(staged).convert('RGB').resize((144,48),Image.Resampling.NEAREST)
            tones=sorted({thumb.getpixel((x,y)) for y in range(48) for x in range(144)},key=sum)
            assert len(tones)==2
            for left,top,width,height in regions:
                for y in range(top,top+height):
                    for x in range(left,left+width):
                        wanted=bool(expected[y//8*144+x]&(1<<(y&7)))
                        assert (thumb.getpixel((x,y))==tones[0])==wanted,(name,x,y)
            destination=ROOT/'games'/game/'docs'/(name+'_g800.png')
            shutil.copyfile(staged,destination)
            report.update({'image':destination.relative_to(ROOT).as_posix(),
                'viewport_matches_z80':True,'regions':regions,
                'source':'Prepared game state, actual distributed Z80 renderer and g800 native HUD, no Sharp ROM.'})
            reports.append(report)
    output=ROOT/'.local/g850-ports';output.mkdir(parents=True,exist_ok=True)
    saved=output/'captures.json'
    previous=json.loads(saved.read_text(encoding='utf-8')) if saved.exists() else []
    updated={item['image']:item for item in previous}
    updated.update({item['image']:item for item in reports})
    saved.write_text(json.dumps(list(updated.values()),indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Captures G850 verifiees : ','Verified G850 captures: ')+str(len(reports)))


if __name__=='__main__':main()
