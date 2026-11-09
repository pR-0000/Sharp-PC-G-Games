"""FR: scenarios CPU du FPS. EN: FPS CPU scenarios. Requires z80==1.2.0."""
from pathlib import Path
import json
import sys
import unittest
from collections import deque

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser,pick

from level_chunks import DEFAULT_SEED, level_map, validate, choices

LITE=False
CAMPAIGN_REPORTS=[]


def play_campaign(m):
    """Play using normal key events only; no RAM fixtures or health cheats."""
    vectors=((0,-1),(1,0),(0,1),(-1,0))
    goal_index=0
    m.start();m.tap(0x2e)
    goals=[]
    for tile in (6,7,8,9):
        goals.append(next((x,y) for y in range(16) for x in range(16) if m.tile(x,y)==tile))
    def face(target):
        current=m.byte('direction')
        if current==target:return False
        m.tap(0x22 if (target-current)%4 in (1,2) else 0x21)
        return True
    def visible(x,y):
        px,py=m.coords()
        for step in range(1,101):
            ax=px+.5+(x-px)*step/100;ay=py+.5+(y-py)*step/100
            if m.tile(int(ax),int(ay)) in (1,2,3,9):return False
        return True
    for actions in range(500):
        if m.byte('phase')!=1:return actions
        px,py=m.coords()
        if (px,py)==goals[goal_index] and goal_index<3:goal_index+=1
        threats=[]
        for i in range(4):
            x,y,kind,hp,alert=m.actor(i)
            if not hp or not visible(x,y):continue
            dx,dy=x-px,y-py
            for direction,(fx,fy) in enumerate(vectors):
                forward=dx*fx+dy*fy;lateral=dx*(-fy)+dy*fx
                if 1<=forward<=3 and abs(lateral)<=1:threats.append((forward,i,direction))
        if threats:
            _,_,direction=min(threats)
            if not face(direction):m.tap(0x1e)
            continue
        queue=deque([(m.coords(),[])])
        seen={m.coords()};route=None
        while queue:
            (x,y),path=queue.popleft()
            if (x,y)==goals[goal_index]:route=path;break
            for direction,(dx,dy) in enumerate(vectors):
                nx,ny=x+dx,y+dy
                if not (0<=nx<16 and 0<=ny<16) or (nx,ny) in seen:continue
                tile=m.tile(nx,ny)
                if tile in (1,2) or (tile==3 and not m.byte('key_owned')):continue
                if tile==9 and (m.byte('switches')!=3 or not m.byte('key_owned')):continue
                seen.add((nx,ny));queue.append(((nx,ny),path+[direction]))
        assert route,('No campaign route',m.coords(),goals[goal_index])
        direction=route[0]
        if face(direction):continue
        dx,dy=vectors[direction]
        m.tap(0x04 if m.tile(px+dx,py+dy)==3 else 0x20)
    raise AssertionError('Campaign exceeded its action budget')


class DepthsMachine(Machine):
    def __init__(self,language='FR',lite=None):
        self.tstates=0
        self.text_writes=[]
        self.heart_states=[]
        self.lite=LITE if lite is None else lite
        self.language=language
        super().__init__('depths_'+('lite_' if self.lite else '')+language,HERE/'build')
        self.cpu.set_input_callback(lambda p: (_ for _ in ()).throw(AssertionError(f'Unexpected IN {p}')))
        self.cpu.set_output_callback(lambda p,v: (_ for _ in ()).throw(AssertionError(f'Unexpected OUT {p}')))

    def rom_return(self,key=None):
        if self.cpu.d==3 and self.cpu.e==0:
            if self.cpu.pc==0xBE62 and self.cpu.a==32:self.heart_states.append(False)
            elif self.cpu.pc==0xBFD0 and self.cpu.b==5:self.heart_states.append(True)
        if self.cpu.pc==0xBFD0:
            row,col,width=self.cpu.d,self.cpu.e,self.cpu.b
            self.text[row][col:col+(width+4)//5]=b' '*((width+4)//5)
        if self.cpu.pc==0xBE62: self.text_writes.append((self.cpu.d,self.cpu.e,self.cpu.a))
        super().rom_return(key)

    def seek_key(self):
        for _ in range(5000):
            self.cpu.ticks_to_stop=100000
            self.cpu.run()
            self.tstates+=(100000-self.cpu.ticks_to_stop)&0xffffffff
            if self.cpu.pc in (0xBE53,RETURN): return
            if self.cpu.pc in IOCS: self.rom_return()
        raise AssertionError(f'CPU did not yield {self.cpu.pc:04X}')

    def coords(self): return self.byte('player_x'),self.byte('player_y')

    def routine(self,name,**registers):
        context={r:getattr(self.cpu,r) for r in ('pc','sp','af','bc','de','hl','ix','iy')}
        stack=bytes(self.cpu.memory[0x1e00:0x2000])
        try:
            self.cpu.pc,self.cpu.sp=self.sym[name],0x1ff0
            self.cpu.memory[0x1ff0:0x1ff2]=RETURN.to_bytes(2,'little')
            for key,value in registers.items(): setattr(self.cpu,key,value)
            for _ in range(5000):
                self.cpu.ticks_to_stop=100000
                self.cpu.run()
                if self.cpu.pc==RETURN: return
                if self.cpu.pc in IOCS:
                    if self.cpu.pc==0xBE53: raise AssertionError('Routine unexpectedly waits for keys')
                    self.rom_return()
            raise AssertionError('Routine failed to return: '+name)
        finally:
            self.cpu.memory[0x1e00:0x2000]=stack
            for key,value in context.items():setattr(self.cpu,key,value)

    def tile(self,x,y,value=None):
        p=self.sym['world']+16*y+x
        if value is None: return self.cpu.memory[p]
        self.cpu.memory[p]=value

    def actor(self,index,values=None):
        p=self.sym['enemies']+5*index
        if values is None: return list(self.cpu.memory[p:p+5])
        self.cpu.memory[p:p+5]=bytes(values)

    def peaceful(self):
        for i in range(4): self.actor(i,[1,1,0,0,0])


    def arena(self):
        self.peaceful()
        for y in range(16):
            for x in range(16): self.tile(x,y,int(x in (0,15) or y in (0,15)))
        self.set_byte('player_x',8);self.set_byte('player_y',12);self.set_byte('direction',0)
        self.routine('render')


class DepthsChecks(unittest.TestCase):
    def test_complete_level_in_both_languages_without_ram_fixtures(self):
        for language in ('FR','EN'):
            m=DepthsMachine(language)
            actions=play_campaign(m)
            self.assertEqual((m.byte('phase'),m.byte('kills'),m.byte('switches'),m.byte('key_owned')),(4,4,3,1))
            self.assertGreater(m.byte('health'),0)
            m.check_memory()
            CAMPAIGN_REPORTS.append({'language':language,'actions':actions,'health':m.byte('health'),'ammo':m.byte('ammo'),
                                     'edition':'lite' if LITE else 'full','ram_fixtures':False,'hardware_test':False})

    def test_basic_style_caller_stack_and_register_return(self):
        m=DepthsMachine()
        m.cpu.pc=m.sym['entry'];m.cpu.sp=0x7ff0
        m.cpu.memory[0x7ff0:0x7ff2]=RETURN.to_bytes(2,'little')
        expected={'bc':0x2345,'de':0x3456,'hl':0x4567,'ix':0x7c05,'iy':0x7c03}
        for key,value in expected.items():setattr(m.cpu,key,value)
        before=bytes(m.cpu.memory)
        m.seek_key();m.start();m.tap(0x02)
        self.assertEqual((m.cpu.pc,m.cpu.sp),(RETURN,0x7ff2))
        for key,value in expected.items():self.assertEqual(getattr(m.cpu,key),value)
        actual=bytes(m.cpu.memory)
        for lo,hi in ((0,m.sym['data_start']),(m.sym['program_end'],0x7e00),(0x7ff2,65536)):
            self.assertEqual(before[lo:hi],actual[lo:hi])
    def test_languages_hud_rom_digits_and_exit(self):
        for language in ('FR','EN'):
            m=DepthsMachine(language)
            self.assertIn(b'DEPTHS LITE' if LITE else b'POCKET DEPTHS',bytes(m.text[0]))
            m.start()
            self.assertEqual(m.coords(),(4,13))
            self.assertEqual(bytes(m.text[3][1:4]),b'100')
            self.assertEqual(bytes(m.text[3][21:24]),b'024')
            self.assertTrue(any((r,c,len(data))==(3,0,5) for r,c,data in m.pattern_calls))
            self.assertTrue(any((r,c,len(data))==(3,20,5) for r,c,data in m.pattern_calls))
            m.tap(0x02)
            self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,0x1ff2,0x1234,0x5678))
            m.check_memory()

    def test_key_edges_turns_strafe_and_walls(self):
        m=DepthsMachine();m.start();m.arena()
        m.tap(0x20)
        self.assertEqual(m.coords(),(8,11))
        m.poll(0x20)
        self.assertEqual(m.coords(),(8,11))
        m.tap(0x0B)
        self.assertEqual(m.coords(),(9,11))
        m.tap(0x09)
        self.assertEqual(m.coords(),(8,11))
        m.tap(0x22)
        self.assertEqual(m.byte('direction'),1)
        for y in range(1,15):m.tile(12,y,1)
        for _ in range(10): m.tap(0x20)
        self.assertEqual(m.coords(),(11,11))
        m.check_memory()

    def test_title_help_and_game_help_return(self):
        m=DepthsMachine()
        m.tap(0x17);self.assertEqual(m.byte('phase'),2)
        m.tap(0x28);self.assertEqual(m.byte('phase'),0)
        m.start();frames=m.word('frames')
        m.tap(0x17);self.assertEqual(m.byte('phase'),2)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1)
        self.assertGreater(m.word('frames'),frames)
        m.check_memory()

    def test_key_door_ammo_healing_and_restart(self):
        m=DepthsMachine();m.start();m.arena()
        m.tile(8,11,6);m.tile(3,7,3)
        m.tap(0x20);self.assertEqual(m.byte('key_owned'),1)
        self.assertEqual(m.tile(8,11),0)
        m.set_byte('player_x',4);m.set_byte('player_y',7);m.set_byte('direction',3)
        m.tap(0x04)
        self.assertEqual(m.tile(3,7),0)
        m.tile(3,7,4);m.set_byte('ammo',95);m.tap(0x20)
        self.assertEqual(m.byte('ammo'),99)
        m.tile(2,7,5);m.set_byte('health',90);m.tap(0x20)
        self.assertEqual(m.byte('health'),100)
        m.tap(0x05)
        self.assertEqual((m.coords(),m.byte('health'),m.byte('ammo')) ,((4,13),100,24))
        m.check_memory()

    def test_ray_reference_all_orientations_and_pillar_depth(self):
        m=DepthsMachine();m.start();m.arena()
        for y in range(1,15):
            m.tile(3,y,1);m.tile(12,y,1)
        m.tile(6,9,2);m.tile(10,5,2)
        for direction in range(4):
            m.set_byte('direction',direction)
            m.routine('render')
            actual=list(m.cpu.memory[m.sym['ray_depths']:m.sym['ray_depths']+40])
            expected=[]
            for ray in range(40):
                value=63
                fx,fy=((0,-1),(1,0),(0,1),(-1,0))[direction]
                lateral=(2*(ray+0.5)/40-1)*0.72
                rx,ry=fx-fy*lateral,fy+fx*lateral
                # Independent fine-step geometric reference, not the table generator.
                for step in range(1,7875):
                    distance=step/1000
                    x,y=int(8.5+rx*distance),int(12.5+ry*distance)
                    if (x-8)*fx+(y-12)*fy>=8: break # documented seven-cell forward clip
                    if not (0<=x<16 and 0<=y<16) or m.tile(x,y) in (1,2,3,9):
                        value=min(63,max(4,round(distance*8)));break
                expected.append(value)
            self.assertTrue(all(abs(a-b)<=1 for a,b in zip(actual,expected)),(direction,actual,expected))
        m.check_memory()

    def test_monster_pixels_do_not_leak_through_a_pillar(self):
        m=DepthsMachine();m.start();m.arena()
        m.tile(8,10,2)
        m.routine('render')
        plain=bytes(m.cpu.memory[m.sym['screen_buffer']:m.sym['screen_buffer']+480])
        m.actor(0,[8,9,0,3,0]);m.routine('render')
        hidden=bytes(m.cpu.memory[m.sym['screen_buffer']:m.sym['screen_buffer']+480])
        self.assertEqual(plain,hidden)
        m.actor(0,[8,11,0,3,0]);m.routine('render')
        shown=bytes(m.cpu.memory[m.sym['screen_buffer']:m.sym['screen_buffer']+480])
        self.assertNotEqual(plain,shown)
        m.check_memory()

    def test_death_restart_and_boundary_return(self):
        m=DepthsMachine();m.start();m.arena()
        m.set_byte('health',1);m.actor(0,[8,11,0,3,1])
        m.tap(0x21)
        self.assertEqual((m.byte('phase'),m.byte('health')),(3,0))
        self.assertIn(b'DEFAITE',bytes(m.text[1]))
        for _ in range(8): m.tap(0x05)
        self.assertEqual(m.byte('phase'),1)
        m.tap(0x51)
        self.assertEqual((m.cpu.pc,m.cpu.sp),(RETURN,0x1ff2))
        m.check_memory()

    def test_weapons_ammunition_damage_and_occlusion(self):
        m=DepthsMachine();m.start();m.arena()
        m.actor(0,[8,10,0,3,0])
        m.tap(0x2E) # shotgun
        m.tap(0x1E)
        self.assertEqual((m.actor(0)[3],m.byte('ammo')),(0,22))
        m.actor(0,[8,9,0,3,0]);m.tile(8,10,2)
        m.tap(0x2D) # pistol redraw updates the depth buffer
        m.tap(0x1E)
        self.assertEqual(m.actor(0)[3],3)
        m.tile(8,10,0);m.actor(0,[8,11,0,2,0])
        m.tap(0x2C) # knife
        before=m.byte('ammo');m.tap(0x1E)
        self.assertEqual(m.byte('ammo'),before)
        self.assertEqual(m.actor(0)[3],1)
        m.check_memory()

    def test_enemy_warning_cover_and_no_wall_crossing(self):
        m=DepthsMachine();m.start();m.arena()
        m.actor(0,[8,11,0,3,0])
        m.tap(0x21)
        self.assertEqual((m.actor(0)[4],m.byte('health')),(1,100))
        m.tap(0x22)
        self.assertEqual(m.byte('health'),92)
        m.actor(0,[8,9,1,3,0]);m.tile(8,10,2)
        before=m.byte('health')
        for _ in range(4): m.tap(0x21)
        self.assertEqual(m.byte('health'),before)
        self.assertNotEqual(m.actor(0)[:2],[8,10])
        m.check_memory()

    def test_objectives_and_victory_require_key_and_both_beacons(self):
        m=DepthsMachine();m.start();m.arena()
        m.tile(8,1,9);m.tile(1,2,7);m.tile(14,2,8)
        m.set_byte('player_x',8);m.set_byte('player_y',2)
        m.tap(0x20)
        self.assertEqual((m.coords(),m.byte('phase')),((8,2),1))
        m.set_byte('player_x',1);m.set_byte('player_y',3)
        m.tap(0x20);self.assertEqual(m.byte('switches'),1)
        m.set_byte('player_x',14);m.set_byte('player_y',3)
        m.tap(0x20);self.assertEqual(m.byte('switches'),3)
        m.set_byte('player_x',8);m.set_byte('player_y',2)
        m.tap(0x20);self.assertEqual(m.byte('phase'),1)
        m.set_byte('key_owned',1);m.tap(0x20)
        self.assertEqual(m.byte('phase'),4)
        self.assertIn(b'SORTIE',bytes(m.text[1]))
        m.check_memory()

    def test_texts_fit_and_idle_does_not_repaint(self):
        for language in ('FR','EN'):
            m=DepthsMachine(language)
            for name in ('title_text','mission_text','start_text','quit_text','help_1','help_2','help_3','help_4','restart_text'):
                p=m.sym[name];length=bytes(m.cpu.memory[p:p+80]).index(0)
                self.assertLessEqual(length,24,(language,name,length))
            m.start();frames=m.word('frames')
            for _ in range(30): m.poll(0)
            self.assertEqual(m.word('frames'),frames)
            m.check_memory()

    def test_compass_and_punctuation_strafe_in_both_languages(self):
        for language,letters in (('FR',b'NESO'),('EN',b'NESW')):
            m=DepthsMachine(language);m.start();m.arena()
            for direction in range(4):
                m.set_byte('direction',direction);m.routine('render')
                self.assertEqual(m.text[3][5],letters[direction])
                before=m.coords();m.tap(0x18);self.assertNotEqual(m.coords(),before)
                m.tap(0x2A);self.assertEqual(m.coords(),before)
            m.check_memory()

    def test_close_wall_front_and_side_have_visible_texture(self):
        m=DepthsMachine();m.start();m.arena()
        for visual in (4,4|0x40,8,8|0x40):
            m.cpu.memory[m.sym['screen_buffer']:m.sym['screen_buffer']+480]=bytes(480)
            m.set_byte('current_ray',20);m.set_byte('ray_visual',visual);m.set_byte('hit_kind',1)
            m.set_word('profile_pointer',m.sym['wall_profiles']+(visual&63)*8)
            m.routine('paint_wall')
            pixels=sum(int(m.cpu.memory[m.sym['screen_buffer']+row*120+x]).bit_count() for row in range(4) for x in range(60,63))
            self.assertGreaterEqual(pixels,12,visual)
        m.check_memory()

    def test_door_has_continuous_frame_central_join_handle_and_plain_panels(self):
        m=DepthsMachine();m.start()
        p=m.sym['screen_buffer']
        def stripe(kind,feature):
            m.cpu.memory[p:p+480]=bytes(480)
            m.set_byte('current_ray',20);m.set_byte('ray_visual',24|feature);m.set_byte('hit_kind',kind)
            m.set_word('profile_pointer',m.sym['wall_profiles']+24*8)
            m.routine('paint_wall')
            return [[(m.cpu.memory[p+(y//7)*120+60+x]>>(y%7))&1 for x in range(3)] for y in range(28)]
        panel=stripe(3,0);frame=stripe(3,0x80);join=stripe(3,0x40)
        self.assertEqual(panel[4],[1,1,1]);self.assertEqual(panel[23],[1,1,1])
        self.assertTrue(all(not any(panel[y]) for y in range(5,23)))
        self.assertTrue(all(frame[y][0] for y in range(4,24)))
        self.assertEqual(join[14],[1,1,0]);self.assertEqual(join[15],[1,1,0])
        self.assertEqual(join[13],[1,0,0])
        self.assertEqual(stripe(9,0x40),join)
        self.assertNotEqual(stripe(1,0),panel)
        m.check_memory()

    def test_front_door_projects_join_and_handle_from_the_generated_rays(self):
        m=DepthsMachine();m.start();m.arena()
        for x in range(1,15):m.tile(x,9,1)
        m.tile(8,9,3);m.routine('render')
        p=m.sym['screen_buffer']
        def pixel(x,y):return (m.cpu.memory[p+120*(y//7)+x]>>(y%7))&1
        for x in (57,60):
            self.assertEqual([pixel(x+i,14) for i in range(3)],[1,1,0])
            self.assertEqual(pixel(x+1,13),0)
        m.check_memory()

    def test_damage_flash_restores_frame_and_keeps_native_hud(self):
        m=DepthsMachine();m.start();m.arena()
        m.actor(0,[8,11,0,3,1]);m.pattern_calls.clear();m.tap(0x21)
        frames=[data for row,col,data in m.pattern_calls if len(data)==120]
        self.assertEqual(len(frames),8)
        for first,second in zip(frames[:4],frames[4:]):
            self.assertEqual(bytes(v^0x7f for v in first),second)
        self.assertEqual(m.byte('hurt_flash'),0)
        self.assertEqual(bytes(m.text[3][1:4]),b'092')
        changes=[]
        for visible in m.heart_states:
            if not changes or changes[-1]!=visible:changes.append(visible)
        self.assertEqual(changes[-5:],[True,False,True,False,True])
        m.check_memory()

    def test_fatal_hit_blinks_heart_before_result_screen(self):
        m=DepthsMachine();m.start();m.arena()
        m.set_byte('health',8);m.actor(0,[8,11,0,3,1]);m.heart_states.clear()
        m.tap(0x21)
        self.assertEqual((m.byte('health'),m.byte('phase'),m.byte('hurt_flash')),(0,3,0))
        changes=[]
        for visible in m.heart_states:
            if not changes or changes[-1]!=visible:changes.append(visible)
        self.assertEqual(changes[-5:],[True,False,True,False,True])
        m.check_memory()

    def test_generated_levels_match_reference_and_all_objectives_are_reachable(self):
        m=DepthsMachine();m.start()
        seeds=(DEFAULT_SEED,) if LITE else range(1,256)
        layouts=set()
        for seed in seeds:
            if not LITE:m.set_byte('level_seed',seed)
            m.routine('new_game')
            actual=bytes(m.cpu.memory[m.sym['world']:m.sym['world']+256])
            self.assertEqual(actual,bytes(validate(seed)),seed)
            layouts.add(actual)
        if not LITE:self.assertEqual(len(layouts),255)
        m.check_memory()

    def test_restart_reuses_layout_and_n_generates_another_only_in_full(self):
        m=DepthsMachine();m.start()
        initial=bytes(m.cpu.memory[m.sym['world']:m.sym['world']+256])
        m.tap(0x05)
        self.assertEqual(bytes(m.cpu.memory[m.sym['world']:m.sym['world']+256]),initial)
        m.tap(0x16)
        after=bytes(m.cpu.memory[m.sym['world']:m.sym['world']+256])
        if LITE:self.assertEqual(after,initial)
        else:
            self.assertNotEqual(after,initial)
            m.tap(0x05)
            self.assertEqual(bytes(m.cpu.memory[m.sym['world']:m.sym['world']+256]),after)
        m.check_memory()


if __name__=='__main__':
    parser=Parser('Verifier Pocket Depths avec les contrats IOCS simules.','Check Pocket Depths with mocked IOCS contracts.')
    parser.add_argument('--edition',choices=('all','full','lite'),default='all')
    args=parser.parse_args()
    passed=True;tests=failures=errors=0
    for LITE in ((False,True) if args.edition=='all' else (args.edition=='lite',)):
        print('Pocket Depths '+('Lite' if LITE else 'Full'),flush=True)
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DepthsChecks))
        tests+=result.testsRun;failures+=len(result.failures);errors+=len(result.errors);passed &= result.wasSuccessful()
    report={'tests':tests,'passed':passed,'failures':failures,'errors':errors,
            'cpu':'z80 1.2.0','iocs':'mocked contracts, not a Sharp ROM','hardware_tested':False,'campaigns':CAMPAIGN_REPORTS,
            'editions':args.edition,'generated_seeds_verified':255 if args.edition!='lite' else 1}
    (HERE/'build/cpu_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(not passed)
