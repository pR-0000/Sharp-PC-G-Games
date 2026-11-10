"""FR/EN: real Z80 CPU scenarios and independent pixel reference."""
from pathlib import Path
from collections import deque
import hashlib,json,sys,unittest
from math import atan2,pi
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser
from assets import track,ROUTES,PATTERNS

def reference_driver(car,route):
    """Map-aware keyboard driver; only returns keys, never writes game state."""
    tx,ty=route[car['gate']];dx,dy=tx-car['x'],ty-car['y']
    desired=round(atan2(dy,dx)*8/pi)&15
    difference=(desired-car['angle'])&15;keys=[]
    if difference:keys.append(0x21 if difference>=8 else 0x22)
    target_speed=7 if min(difference,16-difference)<=1 and max(abs(dx),abs(dy))>14 else 4
    keys.append(0x1f if car['speed']>target_speed else 0x1e)
    return tuple(keys)

class RallyMachine(Machine):
    def __init__(self,language='FR'):
        self.tstates=0
        self.keys=()
        self.strobe=self.last_strobe=0
        self.strobe_at=0
        self.inputs=[];self.outputs=[]
        super().__init__('rally_'+language,HERE/'build/g80x')
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

    def car(self,index=0):
        p=self.sym['cars']+11*index;v=self.cpu.memory[p:p+11]
        return {'x':int.from_bytes(v[:2],'little')/16,'y':int.from_bytes(v[2:4],'little')/16,
                'angle':v[4],'speed':v[5],'gate':v[6],'laps':v[7],'done':v[8],
                'finish':int.from_bytes(v[9:11],'little')}
    def position(self,index,x,y,angle=None,speed=None,gate=None,laps=None):
        p=self.sym['cars']+index*11
        self.cpu.memory[p:p+4]=int(x*16).to_bytes(2,'little')+int(y*16).to_bytes(2,'little')
        for offset,value in ((4,angle),(5,speed),(6,gate),(7,laps)):
            if value is not None:self.cpu.memory[p+offset]=value
    def frame(self,keys=()):
        self.keys=tuple(keys);self.routine('world_step')

class RallyChecks(unittest.TestCase):
    machine_class=RallyMachine
    def machine(self,index=0,lang='FR'):
        m=self.machine_class(lang);m.set_byte('track_index',index);m.start();return m
    def test_languages_title_and_return(self):
        for lang in ('FR','EN'):
            m=self.machine(lang=lang)
            self.assertEqual(bytes(m.text[0][20:24]),b'T1/3' if lang=='FR' else b'L1/3')
            m.tap(0x51);self.assertEqual(m.cpu.pc,RETURN)
            self.assertEqual((m.cpu.sp,m.cpu.ix,m.cpu.iy),(0x1ff2,0x1234,0x5678));m.check_memory()
    def test_maps_all_cells_and_outside(self):
        for index in range(2):
            m=self.machine(index);cells=track(index)
            for y in range(32):
                for x in range(48):
                    r=m.routine('tile_at',b=x,c=y)
                    self.assertEqual(r['af']>>8,cells[y*48+x],(index,x,y))
            for x,y in ((48,0),(255,0),(0,32),(0,255)):
                self.assertEqual(m.routine('tile_at',b=x,c=y)['af']>>8,4)
            m.check_memory()
    def test_tilemapper_against_independent_pixels(self):
        for index in range(2):
            m=self.machine(index);cells=track(index)
            for cx,cy in [(x,y) for x in range(4) for y in range(4)]+[(45,51),(92,100),(91,99)]:
                m.set_byte('camera_x',cx);m.set_byte('camera_y',cy);m.routine('render_terrain')
                expected=bytearray(480)
                for y in range(28):
                    for x in range(100):
                        wx,wy=cx+x,cy+y;tile=cells[(wy//4)*48+wx//4]
                        if PATTERNS[tile][wx%4]>>(wy%4)&1:expected[(y//7)*120+x]|=1<<(y%7)
                p=m.sym['frame_buffer'];self.assertEqual(bytes(m.cpu.memory[p:p+480]),expected,(index,cx,cy))
            m.check_memory()
    def test_simultaneous_steer_throttle_brake_and_coast(self):
        m=self.machine()
        m.position(1,164,84);m.position(2,164,104)
        for _ in range(32):m.poll(0x20)
        self.assertEqual(m.car()['speed'],7)
        old=m.car()['angle'];m.poll((0x22,0x20));m.poll((0x22,0x20))
        self.assertNotEqual(m.car()['angle'],old);self.assertEqual(m.byte('buttons'),6)
        for _ in range(5):m.poll((0x1e,0x1f))
        self.assertEqual(m.car()['speed'],0)
        self.assertEqual(m.outputs[-2:],[(0x11,0),(0x12,0)]);m.check_memory()
    def test_offroad_and_wall_stop(self):
        m=self.machine();m.position(0,88,64,angle=0,speed=7)
        m.routine('car_drive',ix=m.sym['cars']);self.assertLessEqual(m.car()['speed'],3)
        m.position(0,6,16,angle=8,speed=7)
        for _ in range(10):m.routine('car_drive',ix=m.sym['cars'])
        self.assertGreaterEqual(m.car()['x'],6);self.assertEqual(m.car()['speed'],0);m.check_memory()
    def test_ordered_checkpoints_and_finish(self):
        for index in range(2):
            m=self.machine(index);route=ROUTES[index]
            m.position(0,*route[0]);m.routine('pass_gate',ix=m.sym['cars'])
            self.assertEqual(m.car()['laps'],0)
            for lap in range(3):
                for i in list(range(1,len(route)))+[0]:
                    m.position(0,*route[i]);m.routine('pass_gate',ix=m.sym['cars'])
                self.assertEqual(m.car()['laps'],lap+1)
            self.assertEqual(m.car()['done'],1);m.routine('world_step')
            self.assertEqual(m.byte('phase'),3);m.check_memory()
    def test_ai_completes_both_circuits(self):
        for index in range(2):
            m=self.machine(index)
            for f in range(6500):
                m.frame()
                if m.car(1)['done'] and m.car(2)['done']:break
            self.assertTrue(m.car(1)['done'] and m.car(2)['done'],(index,f,m.car(1),m.car(2)))
            m.check_memory()
    def test_full_keyboard_races_both_tracks_and_languages(self):
        for index in range(2):
            for language in ('FR','EN'):
                m=self.machine(index,language)
                for _ in range(2500):
                    m.poll(reference_driver(m.car(),ROUTES[index]))
                    if m.byte('phase')==3:break
                self.assertEqual(m.byte('phase'),3,(index,language,m.car()))
                self.assertEqual(m.car()['laps'],3);self.assertTrue(m.car()['finish'])
                self.assertTrue(1<=m.byte('race_rank')<=3);m.check_memory()
    def test_finish_requires_crossing_the_line(self):
        m=self.machine();x,y=ROUTES[0][0]
        m.position(0,x-4,y,gate=0);m.routine('pass_gate',ix=m.sym['cars'])
        self.assertEqual(m.car()['laps'],0)
        m.position(0,x+1,y);m.routine('pass_gate',ix=m.sym['cars'])
        self.assertEqual(m.car()['laps'],1);m.check_memory()
    def test_timer_saturates(self):
        m=self.machine();m.set_word('race_ticks',9998);m.frame();self.assertEqual(m.word('race_ticks'),9999)
        m.frame();self.assertEqual(m.word('race_ticks'),9999);m.check_memory()
    def test_camera_easing_bounds(self):
        m=self.machine()
        for x,y,angle in ((12,12,8),(180,116,0),(96,64,4),(96,64,12)):
            m.position(0,x,y,angle=angle)
            for _ in range(60):
                before=m.byte('camera_x'),m.byte('camera_y');m.routine('update_camera')
                self.assertLessEqual(abs(m.byte('camera_x')-before[0]),2)
                self.assertLessEqual(abs(m.byte('camera_y')-before[1]),2)
                self.assertTrue(0<=m.byte('camera_x')<=92 and 0<=m.byte('camera_y')<=100)
        m.check_memory()
    def test_ranking_and_contact(self):
        m=self.machine();self.assertEqual(m.byte('race_rank'),3)
        m.position(0,100,24);m.routine('update_rank');self.assertEqual(m.byte('race_rank'),1)
        m.position(1,100,24);m.set_byte('hit_flash',0);m.routine('car_contact')
        self.assertEqual(m.car()['speed'],1);self.assertGreater(m.byte('hit_flash'),0);m.check_memory()
    def test_pause_help_restart_and_track_select(self):
        m=self.machine();m.tap(0x39);before=m.word('race_ticks')
        for _ in range(10):m.poll(0x20)
        self.assertEqual(m.word('race_ticks'),before)
        m.tap(0x39);m.tap(0x17);self.assertEqual(m.byte('phase'),4)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1)
        m.tap(0x0c);self.assertEqual(m.byte('auto_throttle'),1)
        m.tap(0x05);self.assertEqual(m.car()['laps'],0);self.assertEqual(m.byte('auto_throttle'),0)
        m.check_memory()
        m=self.machine_class();m.tap(0x16);self.assertEqual(m.byte('track_index'),1)
        self.assertIn(b'CHICANE',m.text[1]);m.check_memory()
    def test_interrupt_state_and_ui_lengths(self):
        for lang in ('FR','EN'):
            m=self.machine(lang=lang)
            for enabled in (0,1):
                m.cpu._Z80State__iff1[0]=enabled;m.cpu._Z80State__iff2[0]=enabled
                m.routine('sample_controls');self.assertEqual(m.cpu._Z80State__iff1[0],enabled)
            for name in ('title_text','track_name_0','track_name_1','start_text','title_help','help_1','help_2','help_3','help_4',
                         'pause_text','finish_text','position_text','time_text','restart_text'):
                p=m.sym[name];self.assertLessEqual(bytes(m.cpu.memory[p:p+64]).index(0),24,(lang,name))
            m.check_memory()

def main():
    parser=Parser('Verifier Pocket Rally sur CPU Z80.','Verify Pocket Rally on a Z80 CPU.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    (HERE/'build/cpu_validation.json').write_text(json.dumps({'tests':result.testsRun,'success':result.wasSuccessful()},indent=2)+'\n',encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()


