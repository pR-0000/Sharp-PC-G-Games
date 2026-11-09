"""FR/EN: execute real Z80 binaries, independently check runtime DDA."""
from pathlib import Path
import json
import math
import sys
import unittest
from collections import deque

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'))
sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser
CAMPAIGN_REPORTS=[]

def play_campaign(m):
    """Only normal keys after startup: defeat 3 sentries, find key, exit."""
    m.start()
    goals=[(3,11),(4,9),(12,12),(11,5),(13,3),(2,2)]
    def visible(x,y):
        px=m.word('player_x')/256;py=m.word('player_y')/256
        for i in range(1,257):
            u=px+(x+.5-px)*i/256;v=py+(y+.5-py)*i/256
            if m.tile(int(u),int(v)) in (1,2):return False
        return True
    def face(angle):
        old=m.byte('angle')
        if old==angle:return False
        m.tap(0x22 if (angle-old)&255<=128 else 0x21)
        return True
    for actions in range(1500):
        assert m.byte('phase') in (1,4),('Dead',actions,m.byte('health'))
        if m.byte('phase')==4:
            assert all(not m.actor(i)[2] for i in range(3))
            return {'actions':actions,'health':m.byte('health'),'ammo':m.byte('ammo'),'all_monsters_defeated':True}
        px=m.word('player_x')/256;py=m.word('player_y')/256
        threats=[]
        for i in range(3):
            x,y,hp=m.actor(i)
            d=math.hypot(x+.5-px,y+.5-py)
            if hp and d<3.7 and visible(x,y):threats.append((d,x,y))
        if threats:
            _,x,y=min(threats)
            angle=round(math.atan2(y+.5-py,x+.5-px)*16/math.pi)*8&255
            if not face(angle):m.tap(0x1e)
            continue
        if abs(px-goals[0][0]-.5)<.13 and abs(py-goals[0][1]-.5)<.13:
            goals.pop(0)
        assert goals
        start=(int(px),int(py));target=goals[0]
        queue=deque([(start,[])]);seen={start};path=None
        while queue:
            (x,y),route=queue.popleft()
            if (x,y)==target:path=route;break
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                cell=(x+dx,y+dy)
                if cell in seen or not (0<cell[0]<15 and 0<cell[1]<15) or m.tile(*cell)==1:continue
                seen.add(cell);queue.append((cell,route+[cell]))
        assert path is not None,('No path',start,target)
        nx,ny=path[0] if path else target
        # Align to the current cell centre before turning into a doorway.
        if nx!=start[0] and abs(py-start[1]-.5)>.13:nx,ny=start
        if ny!=start[1] and abs(px-start[0]-.5)>.13:nx,ny=start
        dx,dy=nx+.5-px,ny+.5-py
        angle=(0 if dx>0 else 128) if abs(dx)>abs(dy) else (64 if dy>0 else 192)
        if face(angle):continue
        if path and m.tile(*path[0])==2:
            # E only consumes a turn if a nearby door is actually opened.
            m.tap(0x04)
            if m.tile(*path[0])==0:continue
        before=(m.word('player_x'),m.word('player_y'))
        m.tap(0x20)
        assert before!=(m.word('player_x'),m.word('player_y')),('Stuck',start,(px,py),target,angle)
    raise AssertionError('Campaign action budget exceeded')

class Depths2Machine(Machine):
    def __init__(self,language='FR'):
        self.tstates=0
        self.iocs_tstates=0
        self.heart_states=[]
        super().__init__('depths2_'+language,HERE/'build')
        self.cpu.set_input_callback(lambda p: (_ for _ in ()).throw(AssertionError(f'Unexpected IN {p}')))
        self.cpu.set_output_callback(lambda p,v: (_ for _ in ()).throw(AssertionError(f'Unexpected OUT {p}')))
    def seek_key(self):
        for _ in range(5000):
            # z80 1.2.0 has a broken u32 getter above 65535; keep below it.
            self.cpu.ticks_to_stop=60000
            self.cpu.run()
            self.tstates+=60000-self.cpu.ticks_to_stop
            if self.cpu.pc in (0xBE53,RETURN):return
            if self.cpu.pc in IOCS:self.rom_return()
        raise AssertionError(f'CPU did not yield {self.cpu.pc:04X}')
    def rom_return(self,key=None):
        # g800 0.11.4 iocs.c timing MODEL, not measured Sharp ROM timings.
        if self.cpu.pc==0xBFD0:self.iocs_tstates+=100+170*self.cpu.b
        if self.cpu.pc==0xBE62:self.iocs_tstates+=1800
        if self.cpu.pc==0xBFD0:
            row,col,width=self.cpu.d,self.cpu.e,self.cpu.b
            self.text[row][col:col+(width+4)//5]=b' '*((width+4)//5)
        if self.cpu.d==3 and self.cpu.e==0:
            if self.cpu.pc==0xBE62 and self.cpu.a==32:self.heart_states.append(False)
            if self.cpu.pc==0xBFD0 and self.cpu.b==5:self.heart_states.append(True)
        super().rom_return(key)
    def routine(self,name,**registers):
        context={r:getattr(self.cpu,r) for r in ('pc','sp','af','bc','de','hl','ix','iy')}
        stack=bytes(self.cpu.memory[0x1e00:0x2000])
        try:
            self.cpu.pc,self.cpu.sp=self.sym[name],0x1ff0
            self.cpu.memory[0x1ff0:0x1ff2]=RETURN.to_bytes(2,'little')
            for key,value in registers.items():setattr(self.cpu,key,value)
            self.seek_key()
            assert self.cpu.pc==RETURN, name
            return {r:getattr(self.cpu,r) for r in ('af','bc','de','hl','ix','iy')}
        finally:
            self.cpu.memory[0x1e00:0x2000]=stack
            for r,v in context.items():setattr(self.cpu,r,v)
    def tile(self,x,y,value=None):
        p=self.sym['world']+y*16+x
        if value is not None:self.cpu.memory[p]=value
        return self.cpu.memory[p]
    def actor(self,i,x=None,y=None,hp=None):
        p=self.sym['actors']+i*3
        if x is not None:self.cpu.memory[p:p+3]=bytes((x,y,hp))
        return tuple(self.cpu.memory[p:p+3])
    def arena(self):
        for y in range(16):
            for x in range(16):self.tile(x,y,int(x in (0,15) or y in (0,15)))
        for i in range(3):self.actor(i,1,1,0)
        self.set_word('player_x',0x0780);self.set_word('player_y',0x0780)
        self.set_byte('angle',0)

def reference(m,angle):
    """Independent integer implementation of the documented Q8.8 DDA."""
    p=[m.word('player_x'),m.word('player_y')]
    cell=[v>>8 for v in p]
    side=[];delta=[];step=[]
    for i,a in enumerate(((angle+64)&255,angle)):
        component=round(127*math.sin(a*math.pi/128))
        d=min(32767,round(256*127/abs(component))) if component else 32767
        s=-1 if a&128 else 1
        f=(p[i]&255) if s<0 else 256-(p[i]&255)
        side.append(d*f//256 if component else 32767)
        delta.append(d);step.append(s)
    for _ in range(40):
        axis=0 if side[0]<side[1] else 1
        distance=side[axis]
        side[axis]=min(32767,side[axis]+delta[axis])
        cell[axis]+=step[axis]
        x,y=cell
        tile=m.tile(x,y) if 0<=x<16 and 0<=y<16 else 1
        if tile in (1,2):return x&255,y&255,axis,distance,tile
    raise AssertionError('Unbounded reference ray')

class DDA(unittest.TestCase):
    def test_integer_math(self):
        m=Depths2Machine();m.start()
        for x in (0,1,127,256,4096,16384,32767,65535):
            for y in (0,1,17,127,254,255):
                self.assertEqual(m.routine('mul_hi',hl=x,a=y)['hl'],x*y//256)
        for x in (0,7,256,4096,65535):
            for y in (1,3,19,256,4096):
                r=m.routine('divide16',hl=x,bc=y)
                self.assertEqual((r['hl'],r['de']),divmod(x,y))
        m.check_memory()
    def test_all_angles_fractional_origins_and_ties(self):
        m=Depths2Machine();m.start()
        for x,y in ((0x0380,0x0d80),(0x0311,0x0bfe),(0x0700,0x0380),(0x06ff,0x0800)):
            m.set_word('player_x',x);m.set_word('player_y',y)
            for angle in range(256):
                expected=reference(m,angle)
                m.routine('cast_ray',a=angle)
                got=(m.byte('map_x'),m.byte('map_y'),m.byte('hit_side'),m.word('hit_distance'),m.byte('hit_tile'))
                self.assertEqual(got,expected,(x,y,angle))
        m.check_memory()
    def test_projected_depths_and_rotations(self):
        m=Depths2Machine();m.start();m.arena()
        for angle in range(0,256,8):
            m.set_byte('angle',angle);m.routine('render')
            for i in range(40):
                offset=m.cpu.memory[m.sym['ray_offsets']+i]
                raw=reference(m,(angle+offset)&255)[3]
                cosine=m.cpu.memory[m.sym['ray_cosines']+i]
                actual=int.from_bytes(m.cpu.memory[m.sym['depth_buffer']+i*2:m.sym['depth_buffer']+i*2+2],'little')
                self.assertEqual(actual,max(1,raw*cosine//256))
            self.assertTrue(all(v<128 for row in m.screen for v in row))
        m.check_memory()
    def test_float_geometry_error(self):
        m=Depths2Machine();m.start();m.arena()
        for angle in range(256):
            x,y,axis,d,_=reference(m,angle)
            direction=(math.cos(angle*math.pi/128),math.sin(angle*math.pi/128))[axis]
            boundary=(x if axis==0 else y)+(direction<0)
            exact=(boundary-7.5)/direction
            self.assertLess(abs(d/256-exact),.13)

class Gameplay(unittest.TestCase):
    def test_languages_exit_and_native_hud(self):
        for language in ('FR','EN'):
            m=Depths2Machine(language);self.assertIn(b'POCKET DEPTHS 2',m.text[0]);m.start()
            self.assertEqual(bytes(m.text[3][1:4]),b'100')
            self.assertEqual(bytes(m.text[3][21:24]),b'024')
            for angle,char in ((0,b'E'),(64,b'S'),(128,b'W' if language=='EN' else b'O'),(192,b'N')):
                m.set_byte('angle',angle);m.routine('hud');self.assertEqual(bytes(m.text[3][5:6]),char)
            m.tap(0x51);self.assertEqual(m.cpu.pc,RETURN)
            self.assertEqual((m.cpu.sp,m.cpu.ix,m.cpu.iy),(0x1ff2,0x1234,0x5678));m.check_memory()
    def test_fractional_movement_and_held_keys(self):
        m=Depths2Machine();m.start();m.arena()
        x,y=m.word('player_x'),m.word('player_y')
        m.tap(0x20);self.assertEqual((m.word('player_x'),m.word('player_y')),(x+63,y))
        m.poll(0x20);self.assertEqual(m.word('player_x'),x+126)
        m.tap(0x18);self.assertEqual(m.word('player_y'),y-64)
        m.tap(0x2a);self.assertEqual(m.word('player_y'),y-1)
        m.tap(0x22);self.assertEqual(m.byte('angle'),8)
        m.tap(0x21);self.assertEqual(m.byte('angle'),0)
        m.check_memory()
    def test_corner_collision(self):
        m=Depths2Machine();m.start();m.arena();m.tile(8,8,1)
        m.set_word('test_x',8*256-16);m.set_word('test_y',8*256-16)
        self.assertFalse(m.routine('position_clear')['af']&1)
        m.set_word('test_x',8*256-33)
        self.assertTrue(m.routine('position_clear')['af']&1)
        m.check_memory()
    def test_walls_doors_and_radius(self):
        m=Depths2Machine();m.start();m.arena();m.tile(8,7,2)
        for _ in range(5):m.tap(0x20)
        self.assertLessEqual(m.word('player_x'),8*256-32)
        self.assertEqual(m.tile(8,7),2)
        m.tap(0x04);self.assertEqual(m.tile(8,7),0)
        for _ in range(4):m.tap(0x20)
        self.assertGreaterEqual(m.word('player_x'),8*256)
        m.check_memory()
    def test_pickups_and_exit(self):
        m=Depths2Machine();m.start();m.arena()
        for tile,label,want in ((3,'health',100),(4,'ammo',36),(5,'key_owned',1)):
            m.tile(7,7,tile);m.set_byte('health',10);m.routine('collect')
            self.assertEqual(m.byte(label),want);self.assertEqual(m.tile(7,7),0)
        m.tile(7,7,6);m.routine('collect');self.assertEqual(m.byte('phase'),4)
        m.check_memory()
    def test_shooting_occlusion_and_ammo(self):
        m=Depths2Machine();m.start();m.arena();m.actor(0,9,7,3)
        for hp in (2,1,0):m.tap(0x1e);self.assertEqual(m.actor(0)[2],hp)
        self.assertEqual(m.byte('ammo'),21)
        m.actor(0,9,7,3);m.tile(8,7,1);m.tap(0x1e);self.assertEqual(m.actor(0)[2],3)
        m.set_byte('ammo',0);m.tap(0x1e);self.assertEqual(m.byte('ammo'),0)
        m.check_memory()
    def test_los_and_damage_flash(self):
        m=Depths2Machine();m.start();m.arena();m.actor(0,9,7,3)
        m.set_byte('turn_clock',7);m.tap(0x21)
        self.assertEqual(m.byte('health'),92)
        self.assertEqual(m.heart_states[-4:],[False,True,False,True])
        m.tile(8,7,2);m.set_byte('turn_clock',7);m.tap(0x21);self.assertEqual(m.byte('health'),92)
        m.tile(8,7,0);m.set_byte('health',1);m.set_byte('turn_clock',7);m.tap(0x21)
        self.assertEqual(m.byte('phase'),3);self.assertEqual(m.byte('health'),0)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1);self.assertEqual(m.byte('health'),100)
        m.check_memory()
    def test_monster_projection_sign(self):
        m=Depths2Machine();m.start();m.arena();m.actor(0,10,8,3)
        m.routine('actor_transform',ix=m.sym['actors'])
        self.assertGreater(m.word('view_forward'),0);self.assertGreater(m.word('view_side'),0)
        m.routine('draw_actor',ix=m.sym['actors']);self.assertGreater(m.byte('sprite_x'),60)
        m.actor(0,10,6,3);m.routine('draw_actor',ix=m.sym['actors']);self.assertLess(m.byte('sprite_x'),60)
        m.check_memory()
    def test_complete_campaign_both_languages(self):
        for language in ('FR','EN'):
            m=Depths2Machine(language)
            report=play_campaign(m)
            CAMPAIGN_REPORTS.append({'language':language,**report})
            self.assertGreater(report['health'],0)
            self.assertEqual(m.byte('key_owned'),1)
            m.check_memory()
    def test_monster_hidden_by_wall(self):
        m=Depths2Machine();m.start();m.arena();m.tile(8,7,1)
        m.routine('render');before=bytes(m.cpu.memory[m.sym['frame_buffer']:m.sym['frame_buffer']+480])
        m.actor(0,9,7,3);m.routine('render')
        self.assertEqual(before,bytes(m.cpu.memory[m.sym['frame_buffer']:m.sym['frame_buffer']+480]))
        m.check_memory()

def main():
    parser=Parser('Verifier le DDA et le jeu Z80.','Check the DDA and Z80 game.')
    parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'engine':'runtime integer DDA, actual Z80 execution','tests':result.testsRun,
            'errors':len(result.errors),'failures':len(result.failures),'success':result.wasSuccessful(),
            'dda_rays_compared':1024,'projection_rays_compared':1280,'physical_hardware_tested_by_automated_suite':False}
    report['campaigns']=CAMPAIGN_REPORTS
    if result.wasSuccessful():
        frames=[]
        for name,x,y,angle in (('hall',0x0380,0x0d80,208),('door',0x0580,0x0c80,0),
                               ('combat',0x0d80,0x0580,128),('near_wall',0x06c0,0x0c80,0)):
            m=Depths2Machine();m.start()
            m.set_word('player_x',x);m.set_word('player_y',y);m.set_byte('angle',angle)
            before,io=m.tstates,m.iocs_tstates
            m.routine('render')
            cpu=m.tstates-before;io=m.iocs_tstates-io
            frames.append({'scene':name,'emulated_game_tstates_approx':cpu,'modeled_iocs_tstates':io,
                           'modeled_render_ms_at_4mhz':round((cpu+io)/4000,1)})
        report['frame_cost_model']={'source':'Z80 execution + g800 0.11.4 iocs.c; excludes key polling, AI and flash delays',
                                    'physical_measurement':False,'frames':frames}
    (HERE/'build/cpu_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit(1)

if __name__=='__main__':main()
