"""FR/EN: real Z80 CPU scenarios and independent pixel reference."""
from pathlib import Path
from collections import deque
import hashlib,json,sys,unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser
from assets import level

class JumperMachine(Machine):
    def __init__(self,language='FR'):
        self.tstates=0
        self.keys=()
        self.strobe=self.last_strobe=0
        self.strobe_at=0
        self.inputs=[];self.outputs=[]
        super().__init__('jumper_'+language,HERE/'build/g80x')
        self.cpu.set_input_callback(self.input)
        self.cpu.set_output_callback(self.output)
    def now(self):return self.tstates+60000-self.cpu.ticks_to_stop
    def decay(self):
        if self.now()-self.strobe_at>26:self.strobe=self.last_strobe
    def input(self,port):
        assert port&255==0x10,f'Unexpected IN {port:04x}'
        self.decay();self.inputs.append(self.strobe)
        value=0
        for key in self.keys:
            if 1<=key<=80 and self.strobe&(1<<((key-1)//8)):value|=1<<((key-1)%8)
        return value
    def output(self,port,value):
        port&=255;assert port in (0x11,0x12),f'Unexpected OUT {port:04x}'
        self.outputs.append((port,value));self.decay()
        self.last_strobe=value if port==0x11 else value<<8
        self.strobe|=self.last_strobe;self.strobe_at=self.now()
    def poll(self,key=0):
        self.keys=tuple(key) if isinstance(key,(tuple,list)) else (key&127,) if key else ()
        raw=0x51 if 0x51 in self.keys else 0x52 if len(self.keys)>1 else self.keys[0] if self.keys else 0
        super().poll(raw)
    def seek_key(self):
        for _ in range(5000):
            self.cpu.ticks_to_stop=60000;self.cpu.run()
            self.tstates+=60000-self.cpu.ticks_to_stop
            if self.cpu.pc in (0xBE53,RETURN):return
            if self.cpu.pc in IOCS:self.rom_return()
        raise AssertionError(f'CPU did not yield {self.cpu.pc:04X}')
    def rom_return(self,key=None):
        if self.cpu.pc==0xBFD0:
            row,col,width=self.cpu.d,self.cpu.e,self.cpu.b
            self.text[row][col:col+(width+4)//5]=b' '*((width+4)//5)
        super().rom_return(key)
    def routine(self,name,**registers):
        context={r:getattr(self.cpu,r) for r in ('pc','sp','af','bc','de','hl','ix','iy')}
        stack=bytes(self.cpu.memory[0x1e00:0x2000])
        try:
            self.cpu.pc,self.cpu.sp=self.sym[name],0x1ff0
            self.cpu.memory[0x1ff0:0x1ff2]=RETURN.to_bytes(2,'little')
            for k,v in registers.items():setattr(self.cpu,k,v)
            self.seek_key();assert self.cpu.pc==RETURN,name
            return {r:getattr(self.cpu,r) for r in ('af','bc','de','hl','ix','iy')}
        finally:
            self.cpu.memory[0x1e00:0x2000]=stack
            for r,v in context.items():setattr(self.cpu,r,v)

    def tile(self,x,y,value=None):
        p=self.sym['world']+y*96+x
        if value is not None:self.cpu.memory[p]=value
        return self.cpu.memory[p]
    def position(self,x,y):
        self.set_word('player_x',x*16);self.set_word('player_y',y*16)
        self.set_byte('velocity_x',0);self.set_byte('velocity_y',0)
    def arena(self):
        p=self.sym['world'];self.cpu.memory[p:p+576]=bytes(480)+bytes([1])*96
        for i in range(4):self.cpu.memory[self.sym['enemies']+9*i+8]=0
        self.position(32,28);self.set_byte('grounded',1)
    def frame(self,key=0):
        self.keys=tuple(key) if isinstance(key,(tuple,list)) else (key,) if key else ()
        self.routine('world_step')
    def pixels(self):
        p=self.sym['frame_buffer'];return bytes(self.cpu.memory[p:p+480])

class JumperChecks(unittest.TestCase):
    def machine(self):
        m=JumperMachine();m.start();m.arena();return m
    def test_title_languages_exit_and_memory(self):
        for language in ('FR','EN'):
            m=JumperMachine(language);self.assertIn(b'POCKET JUMPER',m.text[0]);m.start()
            self.assertEqual(bytes(m.text[0][20:24]),b'0010') # first nearby coin
            self.assertEqual(bytes(m.text[3][20:24]),b'N 01' if language=='FR' else b'L 01')
            p=m.sym['world'];expected=bytearray(level());expected[3*96+3]=0
            self.assertEqual(bytes(m.cpu.memory[p:p+576]),expected)
            m.tap(0x51);self.assertEqual(m.cpu.pc,RETURN)
            self.assertEqual((m.cpu.sp,m.cpu.ix,m.cpu.iy),(0x1ff2,0x1234,0x5678));m.check_memory()
    def test_blitter_independent_pixel_reference(self):
        m=self.machine();source=m.sym['hero_a']
        words=[int.from_bytes(m.cpu.memory[source+2*i:source+2*i+2],'little') for i in range(12)]
        for x in (-12,-11,-1,0,1,4,5,89,94,99,100,200):
            for y in (-12,-11,-6,-1,0,1,6,7,12,13,19,20,26,27,28):
                p=m.sym['frame_buffer'];m.cpu.memory[p:p+480]=bytes(480)
                m.set_word('draw_x',x&65535);m.set_word('draw_y',y&65535)
                m.routine('draw_sprite',hl=source,b=12)
                expected=bytearray(480)
                for col,value in enumerate(words):
                    for row in range(12):
                        if value>>row&1 and 0<=x+col<100 and 0<=y+row<28:
                            px,py=x+col,y+row;expected[py//7*120+px]|=1<<(py%7)
                self.assertEqual(m.pixels(),expected,(x,y))
        m.check_memory()
    def test_acceleration_friction_and_boundary(self):
        m=self.machine()
        for _ in range(12):m.frame(0x22)
        self.assertEqual(m.byte('velocity_x'),32);self.assertGreater(m.word('player_x'),32*16)
        for _ in range(12):m.frame()
        self.assertEqual(m.byte('velocity_x'),0)
        for _ in range(80):m.frame(0x21)
        self.assertEqual(m.word('player_x'),0);m.check_memory()
    def test_jump_arc_and_landing(self):
        m=self.machine();m.set_byte('jump_buffer',4);heights=[]
        for _ in range(28):m.frame();heights.append(m.word('player_y')/16)
        self.assertLess(min(heights),16);self.assertEqual(m.word('player_y'),28*16)
        self.assertEqual(m.byte('grounded'),1);m.check_memory()
    def test_swept_wall_and_ceiling_collision(self):
        m=self.machine();m.tile(6,3,1);m.tile(6,4,1);m.position(35,28)
        m.set_byte('velocity_x',64);m.routine('move_x')
        self.assertEqual(m.word('player_x'),36*16);self.assertEqual(m.byte('velocity_x'),0)
        m.position(32,24);m.tile(4,2,3);m.set_byte('velocity_y',(-64)&255);m.routine('move_y')
        self.assertEqual(m.tile(4,2),8);self.assertEqual(m.byte('coins'),2)
        self.assertEqual(m.word('player_y'),24*16);m.check_memory()
    def test_brick_and_bonus_only_once(self):
        m=self.machine();m.tile(4,2,2);m.position(32,24);m.set_byte('velocity_y',204)
        m.routine('move_y');self.assertEqual(m.tile(4,2),0)
        m.tile(4,2,3);m.set_byte('velocity_y',204);m.routine('move_y')
        coins=m.byte('coins');m.set_byte('velocity_y',204);m.routine('move_y')
        self.assertEqual(m.byte('coins'),coins);self.assertEqual(m.tile(4,2),8);m.check_memory()
    def test_top_boundary_does_not_reuse_previous_block_hit(self):
        m=self.machine();m.tile(4,2,3);m.set_word('hit_pointer',m.sym['world']+2*96+4)
        m.set_byte('hit_kind',3);m.position(32,0);m.set_byte('velocity_y',204)
        coins=m.byte('coins');m.routine('move_y')
        self.assertEqual(m.word('player_y'),0);self.assertEqual(m.tile(4,2),3)
        self.assertEqual(m.byte('coins'),coins);m.check_memory()
    def test_coins_checkpoint_damage_and_win(self):
        m=self.machine();m.tile(4,3,4);m.routine('collect_items')
        self.assertEqual(m.tile(4,3),0);self.assertEqual(m.byte('coins'),2)
        m.tile(4,4,7);m.routine('collect_items');self.assertEqual(m.word('respawn_x'),32)
        m.position(120,28);m.tile(15,4,5);m.routine('collect_items')
        self.assertEqual(m.byte('lives'),2);self.assertEqual(m.word('player_x'),32*16)
        m.tile(4,4,6);m.routine('collect_items');self.assertEqual(m.byte('phase'),3)
        self.assertIn(b'DRAPEAU',bytes(m.text[1]));m.check_memory()
    def test_enemy_stomp_and_contact(self):
        m=self.machine();p=m.sym['enemies'];m.cpu.memory[p:p+9]=bytes((32,0,32,24,0,48,0,1,1))
        m.position(32,21);m.set_byte('previous_y',18);m.set_byte('velocity_y',32);m.routine('enemy_contact')
        self.assertEqual(m.cpu.memory[p+8],0);self.assertEqual(m.byte('velocity_y'),220)
        m.cpu.memory[p+8]=1;m.position(32,28);m.set_byte('previous_y',28);m.set_byte('grace',0);m.routine('enemy_contact')
        self.assertEqual(m.byte('lives'),2);m.check_memory()
    def test_enemy_patrol_stays_on_floor(self):
        m=self.machine();p=m.sym['enemies'];m.cpu.memory[p:p+9]=bytes((32,0,32,24,0,48,0,1,1))
        for _ in range(150):
            m.routine('enemies_step');x=int.from_bytes(m.cpu.memory[p:p+2],'little')
            self.assertTrue(24<=x<48)
        m.check_memory()
    def test_buffer_coyote_and_directional_jump(self):
        m=self.machine();m.set_byte('grounded',0);m.set_byte('coyote',2);m.set_byte('jump_buffer',2)
        m.frame();self.assertGreater(m.byte('velocity_y'),128)
        m.position(32,28);m.set_byte('grounded',1)
        m.frame(0x12);self.assertEqual(m.byte('velocity_x'),32);self.assertLess(m.word('player_y'),28*16)
        m.check_memory()
    def test_simultaneous_arrows_space_and_up(self):
        for keys,direction in (((0x21,0x1e),-1),((0x22,0x1e),1),((0x21,0x20),-1),((0x22,0x20),1)):
            m=self.machine();m.set_word('player_x',80*16)
            before=m.word('player_x');m.poll(keys)
            self.assertLess(m.word('player_y'),28*16,keys)
            self.assertEqual((m.word('player_x')-before)>0,direction>0,keys)
            self.assertEqual(m.byte('input_buttons'),(1 if direction<0 else 2)|4)
            self.assertTrue(all(row in (4,8,16) for row in m.inputs));m.check_memory()
    def test_jump_held_does_not_repeat_on_direction_changes(self):
        m=self.machine();m.position(80,28)
        for _ in range(40):m.poll((0x21,0x1e))
        self.assertEqual(m.byte('grounded'),1)
        m.poll((0x22,0x1e));self.assertEqual(m.byte('velocity_y'),0)
        m.poll(0x1e);self.assertEqual(m.byte('velocity_y'),0)
        m.poll(0x22);m.poll((0x22,0x1e));self.assertGreater(m.byte('velocity_y'),128)
        m.check_memory()
    def test_opposite_arrows_neutral_and_matrix_cleanup(self):
        m=self.machine();m.position(80,28)
        m.poll((0x21,0x22));self.assertEqual(m.word('player_x'),80*16)
        self.assertEqual(m.byte('velocity_x'),0)
        self.assertEqual(m.outputs[-2:],[(0x11,0),(0x12,0)])
        self.assertEqual(m.last_strobe,0);m.check_memory()
    def test_interrupt_state_preserved(self):
        for enabled in (0,1):
            m=self.machine()
            m.cpu._Z80State__iff1[0]=enabled;m.cpu._Z80State__iff2[0]=enabled
            m.routine('sample_controls')
            self.assertEqual(m.cpu._Z80State__iff1[0],enabled)
            self.assertEqual(m.cpu._Z80State__iff2[0],enabled);m.check_memory()
    def test_pit_and_game_over(self):
        m=self.machine();m.position(32,48);m.routine('world_step');self.assertEqual(m.byte('lives'),2)
        m.routine('lose_life');m.routine('lose_life');self.assertEqual(m.byte('phase'),2)
        self.assertIn(b'TERMINEE',bytes(m.text[1]));m.check_memory()
    def test_camera_clipping_and_hud(self):
        m=self.machine()
        for x in (0,7,32,255,300,666,740,756):
            for y in (0,8,16,28):
                m.position(x,y);m.routine('draw_game');self.assertTrue(0<=m.word('camera_x')<=668)
                self.assertTrue(0<=m.byte('camera_y')<=20)
        m.set_word('score',9999);m.routine('draw_game');self.assertEqual(bytes(m.text[0][20:24]),b'9999')
        m.routine('add_score',hl=50);self.assertEqual(m.word('score'),9999);m.check_memory()
    def test_pause_help_restart(self):
        m=JumperMachine();m.start();m.tap(0x39);x=m.word('player_x');f=m.byte('frame_count')
        for _ in range(12):m.poll(0x22)
        self.assertEqual(m.word('player_x'),x);self.assertEqual(m.byte('frame_count'),f)
        m.tap(0x39);m.tap(0x17);self.assertEqual(m.byte('phase'),4)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1)
        m.set_byte('lives',1);m.set_word('score',500);m.tap(0x05)
        self.assertEqual(m.byte('lives'),3);self.assertEqual(m.word('score'),10);m.check_memory()
    def test_ui_strings_fit(self):
        for lang in ('FR','EN'):
            m=JumperMachine(lang)
            for name in ('title_text','subtitle','start_text','title_help','help_1','help_2','help_3','help_4',
                         'pause_text','over_text','win_text','restart_text'):
                p=m.sym[name];self.assertLessEqual(bytes(m.cpu.memory[p:p+64]).index(0),24,(lang,name))
    def test_complete_level_through_keyboard_in_both_languages(self):
        # Independent recorded keyboard route: no gameplay RAM changes.
        runs=((34,6),(18,1),(34,9),(18,1),(34,17),(18,1),(34,9),(18,1),(34,10),(18,1),
              (34,13),(18,1),(34,26),(18,1),(34,15),(18,1),(34,9),(18,1),(34,6),(18,1),
              (34,6),(18,1),(34,27),(18,1),(34,19),(18,1),(34,37),(18,1),(34,9),(18,1),
              (34,42),(18,1),(34,22),(18,1),(34,6),(18,1),(34,10),(18,1),(34,39))
        for language in ('FR','EN'):
            for simultaneous in (False,True):
                m=JumperMachine(language);m.start()
                for key,count in runs:
                    for _ in range(count):m.poll((0x22,0x1e) if simultaneous and key==18 else key)
                self.assertEqual(m.byte('phase'),3);self.assertEqual(m.byte('lives'),3)
                self.assertEqual(m.word('score'),1090);m.check_memory()

def main():
    parser=Parser('Verifier Pocket Jumper sur CPU Z80.','Verify Pocket Jumper on a Z80 CPU.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    report={'tests':result.testsRun,'success':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors)}
    (HERE/'build/cpu_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
