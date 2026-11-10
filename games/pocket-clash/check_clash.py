"""FR/EN: execute the distributed G850 Z80 game with strict IOCS/keyboard stubs."""
from pathlib import Path
import json,sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from cli_i18n import Parser
from bitmap import read_bmp
FIELDS={'x':0,'y':2,'vx':4,'vy':5,'damage':6,'stocks':7,'char':8,'facing':9,'ground':10,'jumps':11,
    'attack':12,'cooldown':13,'stun':14,'invuln':15,'energy':16,'guard':17,'buttons':18,'last':19,
    'special':21,'hit':22,'drop':23,'kind':24,'air':25}
class ClashG850(G850Machine):
    def __init__(self,language='FR',target='g850'):
        self.language=language
        native=target=='g850'
        super().__init__('clash_'+('g850_' if native else 'g80x_32k_')+language,HERE/'build'/('g850' if native else 'g80x-32k'))
    def fighter(self,index,**values):
        base=self.sym['fighters']+32*index
        for key,value in values.items():
            address=base+FIELDS[key]
            if key in ('x','y'):self.cpu.memory[address:address+2]=(round(value*16)&65535).to_bytes(2,'little')
            else:self.cpu.memory[address]=value&255
        result={key:self.cpu.memory[base+offset] for key,offset in FIELDS.items()}
        for key in ('x','y'):result[key]=int.from_bytes(self.cpu.memory[base+FIELDS[key]:base+FIELDS[key]+2],'little',signed=True)/16
        return result
    def live(self):
        self.start();self.set_byte('countdown',0)
    def pair(self,routine):
        return self.routine(routine,ix=self.sym['fighters'],iy=self.sym['fighters']+32)

class ClashChecks(unittest.TestCase):
    def test_languages_four_character_selection_native_hud_and_return(self):
        for language in ('FR','EN'):
            m=ClashG850(language);self.assertIn(b'POCKET CLASH',m.text[0])
            for index in range(4):
                self.assertEqual(m.byte('selected'),index)
                m.tap(0x22)
            self.assertEqual(m.byte('selected'),0);m.live()
            self.assertEqual(bytes(m.text[0][:8]),b'NOVA000%')
            self.assertEqual(bytes(m.text[0][10:13]),b'1/3')
            self.assertEqual([row for row,col,data in m.pattern_calls[-6:]],list(range(6)))
            m.tap(0x51);self.assertEqual((m.cpu.pc,m.cpu.sp),(RETURN,m.stack+2));m.check_memory()
    def test_simultaneous_direction_jump_attack_and_two_jumps_only(self):
        m=ClashG850();m.live();m.fighter(1,invuln=250)
        old=m.fighter(0);m.poll((0x22,0x1e,0x11));p=m.fighter(0)
        self.assertGreater(p['x'],old['x']);self.assertLess(p['y'],old['y'])
        self.assertEqual((p['buttons'],p['jumps'],p['attack']),(14,1,12))
        m.poll();m.poll(0x1e);self.assertEqual(m.fighter(0)['jumps'],0)
        m.poll();vy=m.fighter(0)['vy'];m.poll(0x1e)
        self.assertEqual(m.fighter(0)['jumps'],0);self.assertNotEqual(m.fighter(0)['vy'],190)
        self.assertTrue(all(value in (4,8,16) for value in m.inputs));m.check_memory()
    def test_matrix_preserves_interrupt_state_and_clears_both_strobes(self):
        m=ClashG850();m.live()
        for enabled in (0,1):
            m.cpu._Z80State__iff1[0]=enabled;m.cpu._Z80State__iff2[0]=enabled
            m.keys=(0x22,0x1e,0x11)
            m.pair('sample_controls')
            self.assertEqual(m.cpu.iff1,enabled)
            self.assertEqual(m.fighter(0)['buttons'],14)
            self.assertEqual(m.outputs[-2:],[(0x11,0),(0x12,0)])
        m.check_memory()
    def test_timeout_draw_awards_one_point_to_each_combatant(self):
        m=ClashG850();m.live();m.fighter(0,damage=25);m.fighter(1,damage=25)
        m.routine('finish_round')
        self.assertEqual((m.byte('result_kind'),m.byte('phase')),(2,2))
        p=m.sym['points'];self.assertEqual(list(m.cpu.memory[p:p+2]),[1,1])
        self.assertEqual(sum(m.cpu.memory[p:p+4]),5);m.check_memory()
    def test_platform_landing_one_way_jump_and_drop_to_lower_platform(self):
        m=ClashG850();m.live();m.set_byte('actor_index',0)
        m.fighter(0,x=60,y=32,vy=80,ground=0,jumps=0)
        for _ in range(3):m.pair('fighter_step')
        self.assertEqual((m.fighter(0)['y'],m.fighter(0)['ground'],m.fighter(0)['jumps']),(38,1,2))
        m.fighter(0,x=60,y=60,vy=-80,ground=0)
        for _ in range(3):m.pair('fighter_step')
        self.assertLess(m.fighter(0)['y'],54);self.assertEqual(m.fighter(0)['ground'],0)
        m.fighter(0,x=60,y=38,vy=0,ground=1,buttons=36,last=0)
        m.pair('fighter_step');self.assertGreater(m.fighter(0)['y'],38)
        m.fighter(0,buttons=0)
        for _ in range(30):m.pair('fighter_step')
        self.assertEqual((m.fighter(0)['y'],m.fighter(0)['ground']),(64,1));m.check_memory()
    def test_melee_window_facing_occlusion_and_single_hit_per_attack(self):
        m=ClashG850();m.live();m.fighter(0,x=80,y=64,attack=9,kind=0,hit=0,facing=0)
        m.fighter(1,x=100,y=64,invuln=0,damage=0)
        m.pair('melee_hit');self.assertEqual(m.fighter(1)['damage'],10)
        m.fighter(1,invuln=0);m.pair('melee_hit');self.assertEqual(m.fighter(1)['damage'],10)
        for x,y in ((60,64),(100,30)):
            m.fighter(0,hit=0);m.fighter(1,x=x,y=y,damage=0,invuln=0)
            m.pair('melee_hit');self.assertEqual(m.fighter(1)['damage'],0)
        m.check_memory()
    def test_damage_increases_launch_and_heavy_fighter_resists_knockback(self):
        m=ClashG850();m.live();m.set_byte('hit_damage',10);m.set_byte('hit_direction',0)
        speeds=[]
        for damage,kind in ((0,0),(120,0),(120,2),(120,3)):
            m.fighter(1,damage=damage,char=kind,invuln=0,guard=0,stun=0)
            m.pair('apply_hit');speeds.append(m.fighter(1)['vx'])
        self.assertGreater(speeds[1],speeds[0]);self.assertLess(speeds[2],speeds[1]);self.assertGreater(speeds[3],speeds[1])
        self.assertEqual(m.word('damage_scores'),40);m.check_memory()
    def test_shield_consumes_stamina_and_break_has_real_stun(self):
        m=ClashG850();m.live();m.set_byte('hit_damage',12);m.set_byte('hit_direction',0)
        m.fighter(1,damage=10,guard=1,energy=40,invuln=0)
        m.pair('apply_hit');self.assertEqual((m.fighter(1)['damage'],m.fighter(1)['energy']),(10,32))
        m.fighter(1,guard=1,energy=4,invuln=0)
        m.pair('apply_hit');self.assertEqual(m.fighter(1)['damage'],22);self.assertGreaterEqual(m.fighter(1)['stun'],18)
        m.check_memory()
    def test_air_special_is_available_once_until_landing(self):
        m=ClashG850();m.live();m.fighter(0,ground=0,jumps=0,air=0,special=0,attack=0,y=30)
        m.poll(0x12);self.assertEqual(m.fighter(0)['air'],1);self.assertGreater(m.fighter(0)['vy'],128)
        m.poll();m.fighter(0,special=0,attack=0);before=m.fighter(0)['vy'];m.poll(0x12)
        self.assertEqual(m.fighter(0)['vy'],(before+5)&255);m.check_memory()
    def test_nova_dash_returns_to_running_speed_after_its_burst(self):
        m=ClashG850();m.live()
        m.fighter(0,buttons=16,last=0,kind=0,attack=0,ground=1)
        m.pair('fighter_step');self.assertEqual(m.fighter(0)['vx'],96)
        m.fighter(0,buttons=2)
        for _ in range(11):m.pair('fighter_step')
        self.assertLessEqual(m.fighter(0)['vx'],36)
        self.assertGreater(m.fighter(0)['stocks'],0);m.check_memory()
    def test_volt_projectile_moves_hits_target_and_not_owner(self):
        m=ClashG850();m.tap(0x22);m.live()
        m.fighter(1,x=130,y=64,stun=100,invuln=0)
        m.poll(0x12)
        for _ in range(16):m.poll()
        self.assertEqual(m.fighter(0)['damage'],0);self.assertEqual(m.fighter(1)['damage'],12)
        self.assertEqual(m.cpu.memory[m.sym['orbs']+5],0);m.check_memory()
    def test_ringout_spends_one_stock_and_respawn_is_protected(self):
        m=ClashG850();m.live();m.set_byte('actor_index',0)
        m.fighter(0,x=-25,y=64,stocks=2,damage=90)
        m.pair('check_ringout');self.assertEqual((m.fighter(0)['stocks'],m.fighter(0)['damage'],m.fighter(0)['invuln']),(1,0,40))
        self.assertEqual(m.cpu.memory[m.sym['knockouts']+1],1)
        m.fighter(0,y=129);m.pair('check_ringout');self.assertEqual(m.fighter(0)['stocks'],0);m.check_memory()
    def test_standings_points_kos_damage_tiebreak_and_enter_release(self):
        m=ClashG850();m.live()
        for index in range(3):
            m.fighter(1,stocks=0);m.routine('finish_round')
            self.assertEqual(m.byte('phase'),3 if index==2 else 2)
            self.assertEqual(m.cpu.memory[m.sym['points']],3*(index+1))
            if index==2:self.assertEqual(m.byte('ranking'),0)
            if index<2:
                m.tap(0x28);self.assertEqual(m.byte('round_index'),index+1)
                m.poll(0x28);self.assertEqual(m.byte('round_index'),index+1)
        p=m.sym['points'];m.cpu.memory[p:p+4]=bytes((6,6,3,6))
        p=m.sym['knockouts'];m.cpu.memory[p:p+4]=bytes((4,2,1,4))
        p=m.sym['damage_scores'];m.cpu.memory[p:p+8]=b''.join(v.to_bytes(2,'little') for v in (100,500,100,200))
        m.routine('sort_ranking');self.assertEqual(list(m.cpu.memory[m.sym['ranking']:m.sym['ranking']+4]),[3,0,1,2]);m.check_memory()
    def test_three_distinct_arenas_and_pause_photo_help_preserve_state(self):
        m=ClashG850();m.live();layouts=[]
        for index in range(3):
            m.set_byte('round_index',index);m.routine('start_round');layouts.append(bytes(m.cpu.memory[m.sym['platforms']:m.sym['platforms']+12]))
        self.assertEqual(len(set(layouts)),3)
        m.tap(0x1d);state=(m.pixels(),m.word('round_frames'),bytes(m.cpu.memory[m.sym['fighters']:m.sym['fighters']+64]))
        for _ in range(10):m.poll((0x22,0x1e))
        self.assertEqual(state,(m.pixels(),m.word('round_frames'),bytes(m.cpu.memory[m.sym['fighters']:m.sym['fighters']+64])))
        m.tap(0x1d);m.tap(0x17);self.assertEqual(m.byte('phase'),4)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1);m.check_memory()
    def test_camera_zoom_stays_bounded_and_responds_to_separation(self):
        m=ClashG850();m.live();m.fighter(0,x=35,y=64);m.fighter(1,x=190,y=10)
        for frame in range(32):m.set_byte('frame_count',frame);m.routine('update_camera')
        self.assertEqual(m.byte('zoom_n'),8)
        m.fighter(0,x=95,y=64);m.fighter(1,x=115,y=64)
        for frame in range(48):m.set_byte('frame_count',frame);m.routine('update_camera')
        self.assertEqual(m.byte('zoom_n'),16);m.check_memory()
    def test_masked_scaler_matches_independent_pixel_oracle_at_all_edges(self):
        m=ClashG850();m.live();w,h,pixels=read_bmp(HERE/'sprites.bmp');source={(x,y) for y in range(16) for x in range(16) if pixels[y*16+x]==(0,0,0)}
        frame=m.sym['frame_buffer']
        for n in range(8,17):
            ink={(x,y) for y in range(n) for x in range(n) if (min(15,(2*x+1)*8//n),min(15,(2*y+1)*8//n)) in source}
            mask=ink|{(x+dx,y+dy) for x,y in ink for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))}
            m.set_byte('zoom_n',n)
            for mirror in (0,1):
                m.set_byte('sprite_mirror',mirror)
                for x,y in ((-16,0),(-1,-1),(0,0),(1,7),(7,8),(127,27),(140,36),(144,40),(200,-16)):
                    m.cpu.memory[frame:frame+864]=bytes([165])*864
                    m.set_word('draw_x',x&65535);m.set_word('draw_y',y&65535);m.routine('draw_sprite',a=0)
                    expected=bytearray([165])*864
                    for py in range(n):
                        for px in range(n):
                            sx=n-1-px if mirror else px
                            if not (0<=x+px<144 and 0<=y+py<40):continue
                            index=(y+py+8)//8*144+x+px;bit=1<<((y+py)&7)
                            if (sx,py) in mask:expected[index]&=255^bit
                            if (sx,py) in ink:expected[index]|=bit
                    self.assertEqual(m.pixels(),expected,(n,mirror,x,y))
        m.check_memory()
    def test_texts_fit_24_columns_and_native_caller_registers_survive(self):
        labels=('choose_text','nova_text','volt_text','rok_text','lynx_text','cup_text','start_text','menu_help',
            'help_1','help_2','help_3','help_4','help_5','help_6','next_text','end_text')
        for language in ('FR','EN'):
            m=ClashG850(language)
            for label in labels:
                p=m.sym[label];length=bytes(m.cpu.memory[p:p+80]).index(0)
                self.assertLessEqual(length,24,(language,label,length))
            m.cpu.pc=m.sym['entry'];m.cpu.sp=m.stack
            m.cpu.memory[m.stack:m.stack+2]=RETURN.to_bytes(2,'little')
            expected={'bc':0x2345,'de':0x3456,'hl':0x4567,'ix':0x1234,'iy':0x5678}
            for name,value in expected.items():setattr(m.cpu,name,value)
            m.seek_key();m.start();m.tap(0x02)
            for name,value in expected.items():self.assertEqual(getattr(m.cpu,name),value)
            m.check_memory()
    def test_demo_completes_three_real_battles_and_a_final_ranking(self):
        records=[]
        for language in ('FR','EN'):
            m=ClashG850(language);m.tap(0x0b)
            for round_index in range(3):
                for frames in range(2600):
                    if m.byte('phase')!=1:break
                    m.routine('world_step')
                self.assertEqual(m.byte('phase'),3 if round_index==2 else 2,(round_index,frames))
                records.append((language,round_index,frames,m.fighter(0)['stocks'],m.fighter(1)['stocks']))
                if round_index<2:m.tap(0x28)
            self.assertIn(b'FINAL' if language=='EN' else b'FINAL',bytes(m.text[0]));m.check_memory()
        (HERE/'build/cpu_validation.json').write_text(json.dumps({'demo_battles':records,'hardware_tested':False},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    Parser('Verifier Pocket Clash G850.','Check Pocket Clash G850.').parse_args()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClashChecks)).wasSuccessful())
