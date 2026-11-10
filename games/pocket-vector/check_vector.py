"""FR/EN: execute the actual Z80 racer, with a G850 keyboard and IOCS model."""
from pathlib import Path
import json
import math
import struct
import hashlib
import tempfile
import shutil
import sys
import unittest

import z80
from assets import reference

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import read_symbols
from cli_i18n import Parser

RETURN=0x7F00
STACK=0x76C0


class VectorMachine:
    def __init__(self,language='FR',target='g850'):
        native=target=='g850'
        base=HERE/'build'/('g850' if native else 'g80x-32k')/('vector_'+('' if native else 'g80x_32k_')+language)
        self.width,self.rows,self.pixel_mask=(144,6,255) if native else (120,4,127)
        self.binary=base.with_suffix('.bin').read_bytes()
        self.sym=read_symbols(base.with_suffix('.sym'))
        assert self.sym['program_end']<=0x7000,'Game exceeds its firmware-safe memory budget'
        self.cpu=z80.Z80Machine();self.cpu.memory[:]=bytes([0xA5])*65536
        self.cpu.memory[256:256+len(self.binary)]=self.binary
        self.raw_keys=set();self.strobe=0;self.pending=0;self.strobe_time=-1000
        self.ticks=0;self.quantum=60000;self.display=bytearray(self.width*self.rows);self.uploads=[]
        self.cpu.set_input_callback(self.input_port);self.cpu.set_output_callback(self.output_port)
        self.cpu.set_breakpoint(RETURN);self.cpu.set_breakpoint(0xBFD0)
        self.initial=bytes(self.cpu.memory)
    def byte(self,name,value=None):
        p=self.sym[name]
        if value is not None:self.cpu.memory[p]=value&255
        return self.cpu.memory[p]
    def word(self,name,value=None):
        p=self.sym[name]
        if value is not None:self.cpu.memory[p:p+2]=(value&65535).to_bytes(2,'little')
        return int.from_bytes(self.cpu.memory[p:p+2],'little')
    def now(self):return self.ticks+self.quantum-self.cpu.ticks_to_stop
    def settled(self):
        if self.now()-self.strobe_time>=130:self.strobe=self.pending
    def output_port(self,port,value):
        port&=255
        assert port in (0x11,0x12),('Unexpected OUT',port,value)
        self.settled();self.pending=value if port==0x11 else value<<8
        self.strobe|=self.pending;self.strobe_time=self.now()
    def input_port(self,port):
        port&=255
        if port==0x1F:return 128 if 0x51 in self.raw_keys else 0
        assert port==0x10,('Unexpected IN',port)
        self.settled();result=0
        for code in self.raw_keys:
            if code>0x50:continue
            group,bit=divmod(code-1,8)
            if self.strobe&(1<<group):result|=1<<bit
        return result
    def rom_return(self):
        cpu=self.cpu;row,col,width=cpu.d,cpu.e,cpu.b
        assert 0<=row<self.rows and col==0 and width==self.width,(row,col,width)
        data=bytes(cpu.memory[cpu.hl:cpu.hl+width]);assert all(v<=self.pixel_mask for v in data)
        self.display[row*self.width:(row+1)*self.width]=data
        self.uploads.append((row,data))
        target=cpu.memory[cpu.sp]+256*cpu.memory[cpu.sp+1]
        cpu.sp+=2;cpu.pc=target
        for r in ('af','bc','de','hl','ix','iy'):setattr(cpu,r,0xCCCC)
    def run_to(self,target=RETURN,budget=300):
        self.cpu.set_breakpoint(target)
        for _ in range(budget):
            self.quantum=60000;self.cpu.ticks_to_stop=self.quantum;self.cpu.run()
            self.ticks+=self.quantum-self.cpu.ticks_to_stop
            if self.cpu.pc in (target,RETURN):return
            if self.cpu.pc==0xBFD0:self.rom_return()
        raise AssertionError(f'CPU timeout {self.cpu.pc:04X} -> {target:04X}')
    def call(self,name,**registers):
        self.cpu.pc=self.sym[name];self.cpu.sp=STACK
        self.cpu.memory[STACK:STACK+2]=RETURN.to_bytes(2,'little')
        for reg,value in registers.items():setattr(self.cpu,reg,value)
        before=self.ticks;self.run_to()
        assert self.cpu.sp==STACK+2,(name,self.cpu.sp)
        return self.ticks-before
    def initialise(self,demo=0):self.call('new_game',a=demo)
    def start(self):
        self.cpu.pc=self.sym['entry'];self.cpu.sp=STACK
        self.cpu.memory[STACK:STACK+2]=RETURN.to_bytes(2,'little')
        self.run_to(self.sym['main_loop'])
    def step(self,raw=()):
        self.raw_keys=set(raw);loop=self.sym['main_loop']
        self.cpu.clear_breakpoint(loop)
        self.run_to(loop+3)
        self.cpu.clear_breakpoint(loop+3)
        self.run_to(loop)
    def wait_for_go(self):
        for _ in range(80):
            if self.byte('phase')==1:return
            assert self.byte('phase') in (7,8,9),self.byte('phase')
            self.step()
        raise AssertionError('Starting sequence did not reach GO')
    def release_confirm(self):
        for _ in range(3):self.step()
    def check_memory(self):
        end=self.sym['program_end']
        assert bytes(self.cpu.memory[:256])==self.initial[:256]
        assert bytes(self.cpu.memory[end:STACK-128])==self.initial[end:STACK-128]
        assert bytes(self.cpu.memory[STACK+2:0x8000])==self.initial[STACK+2:0x8000]
        assert bytes(self.cpu.memory[0x8000:])==self.initial[0x8000:]
        # Assets and code are immutable apart from the floor bit immediate.
        bit=self.sym['floor_bit']+1;state=self.sym['state_begin']
        for first,last in ((256,bit),(bit+1,state)):
            assert bytes(self.cpu.memory[first:last])==self.initial[first:last],(first,last)
    def native_frame(self):return bytes(self.cpu.memory[self.sym['frame']:self.sym['frame']+864])


class VectorChecks(unittest.TestCase):
    def test_grid_is_behind_the_line_and_first_crossing_does_not_complete_a_lap(self):
        for track in range(3):
            m=VectorMachine();m.byte('track_index',track);m.initialise()
            p=m.sym['path_nodes'];x,y,heading=m.cpu.memory[p:p+3]
            self.assertEqual((heading,m.byte('heading')),(0,0))
            self.assertEqual(m.word('player_y'),y*256)
            self.assertEqual(len(set(m.cpu.memory[p+i*4+1] for i in (*range(120,128),*range(5)))),1)
            m.call('prepare_camera')
            self.assertEqual(m.word('camera_y'),m.word('player_y'))
            self.assertEqual(m.byte('camera_sin'),0)
            angle=heading*math.pi/32
            for ship in ('player','rival1','rival2'):
                dx=m.word(ship+'_x')/256-x;dy=m.word(ship+'_y')/256-y
                self.assertLess(dx*math.cos(angle)+dy*math.sin(angle),-1,(track,ship))
                self.assertEqual(m.byte(ship+'_started'),0)
            self.assertEqual(m.byte('rank'),3)
            m.byte('old_section',127);m.byte('section',0);m.call('update_laps')
            self.assertEqual((m.byte('player_started'),m.byte('lap'),m.byte('checkpoint')),(1,1,0))
            m.call('update_rank');self.assertEqual(m.byte('rank'),1)
            for rival in ('rival1','rival2'):
                m.word(rival+'_progress',0x7FC0)
                m.call('rival_tick',ix=m.sym[rival+'_progress'],bc=224)
                self.assertEqual((m.byte(rival+'_started'),m.byte(rival+'_lap')),(1,1))
                m.word(rival+'_progress',0x0200)
            m.call('update_rank');self.assertEqual(m.byte('rank'),3)
            m.check_memory()

    def test_opponents_brake_in_corners_boost_from_lap_two_and_stay_retired(self):
        m=VectorMachine();m.initialise()
        nodes=m.sym['path_nodes']
        headings=list(m.cpu.memory[nodes+2:nodes+512:4])
        turns=[abs(((headings[(i+3)&127]-headings[i]+32)&63)-32) for i in range(128)]
        straight=next(i for i,turn in enumerate(turns) if turn<2)
        curve=next(i for i,turn in enumerate(turns) if turn>=6)
        for rival,normal,boost in (('rival1',224,244),('rival2',232,252)):
            p=m.sym[rival+'_progress']
            m.word(rival+'_progress',straight*256);m.byte(rival+'_lap',1)
            m.call('rival_target',ix=p);self.assertEqual(m.cpu.b,normal)
            m.byte(rival+'_lap',2);m.word('frame_counter',0)
            m.call('rival_target',ix=p);self.assertEqual(m.cpu.b,boost)
            self.assertEqual(m.byte(rival+'_energy'),47)
            m.word(rival+'_progress',curve*256)
            m.call('rival_target',ix=p);self.assertEqual(m.cpu.b,148)
            m.byte(rival+'_energy',0);m.word(rival+'_progress',47*256)
            for _ in range(8):m.call('update_rivals')
            self.assertEqual(m.byte(rival+'_energy'),0)
            self.assertEqual(m.word(rival+'_progress'),47*256)
        m.check_memory()

    def test_opponent_collision_slows_the_entire_fixed_point_progress_step(self):
        m=VectorMachine();m.initialise();p=m.sym['rival1_progress']
        m.word('rival1_progress',0x0200);m.byte('rival1_stun',4)
        m.call('rival_tick',ix=p,bc=400)
        self.assertEqual(m.word('rival1_progress'),0x0200+100)
        m.check_memory()

    def test_orbit_and_countdown_freeze_the_grid_until_a_shared_go(self):
        for language in ('FR','EN'):
            m=VectorMachine(language);m.start();m.step({0x28})
            self.assertEqual(m.byte('phase'),7)
            def grid():
                return tuple(m.word(k) for k in ('player_x','player_y','rival1_x','rival1_y',
                    'rival2_x','rival2_y','rival1_progress','rival2_progress','frame_counter'))+tuple(
                    m.byte(k) for k in ('heading','lap','energy','speed','rival1_speed','rival2_speed'))
            initial=grid();camera=[]
            for tick in range(32):
                self.assertEqual(m.byte('phase'),7)
                camera.append((m.word('camera_x'),m.word('camera_y')))
                m.step({0x20,0x12})
                self.assertEqual(grid(),initial)
            self.assertEqual(len(set(camera)),32);self.assertEqual(m.byte('phase'),9)
            for tick in range(12):
                m.step({0x20,0x12});self.assertEqual(grid(),initial)
            self.assertEqual(m.byte('phase'),8)
            for stage in range(3):
                for tick in range(7):
                    self.assertEqual((m.byte('phase'),m.byte('countdown_stage')),(8,stage))
                    m.step({0x20,0x12});self.assertEqual(grid(),initial)
            self.assertEqual((m.byte('phase'),m.byte('go_frames')),(1,6))
            m.step({0x20})
            self.assertEqual((m.byte('speed'),m.byte('rival1_speed'),m.byte('rival2_speed')),(8,8,8))
            self.assertGreater(m.word('rival1_progress'),initial[6])
            self.assertEqual(m.word('frame_counter'),1);m.check_memory()
    def test_skip_orbit_never_skips_countdown_and_photo_preserves_the_start_phase(self):
        m=VectorMachine();m.start();m.step({0x28});m.step()
        m.step({0x0C});self.assertEqual(m.byte('phase'),2)
        angle=m.byte('intro_angle');timer=m.byte('start_timer')
        for _ in range(4):m.step()
        self.assertEqual((m.byte('intro_angle'),m.byte('start_timer')),(angle,timer))
        m.step({0x28});self.assertEqual(m.byte('phase'),7)
        m.step();m.step({0x28});self.assertEqual(m.byte('phase'),9)
        for _ in range(12):m.step({0x28})
        self.assertEqual(m.byte('phase'),8)
        for _ in range(6):m.step({0x28})
        self.assertEqual(m.byte('phase'),8);self.assertEqual(m.byte('countdown_stage'),0)
        m.wait_for_go();self.assertEqual(m.word('frame_counter'),0);m.check_memory()
    def test_orbit_contains_no_ships_and_grid_arrives_from_the_bottom(self):
        m=VectorMachine();m.initialise();m.call('begin_start');heading=m.byte('heading')
        for angle in range(0,64,8):
            m.byte('intro_angle',angle);m.call('render');image=m.native_frame()
            m.byte('rival1_energy',0);m.byte('rival2_energy',0)
            m.byte('control_keys',3);m.byte('spin_frames',8);m.call('render')
            self.assertEqual(m.native_frame(),image)
            self.assertEqual(m.byte('heading'),heading)
        m.call('new_game',a=0);m.call('begin_arrival')
        offsets=[]
        for _ in range(12):
            m.call('arrival_offset');offsets.append(m.cpu.a);m.call('start_tick')
        self.assertEqual(offsets,list(range(36,0,-3)))
        self.assertEqual(m.byte('phase'),8);m.call('arrival_offset');self.assertEqual(m.cpu.a,0)
        m.check_memory()
    def test_acceleration_reaches_the_higher_cap_and_manual_steering_is_responsive(self):
        m=VectorMachine();m.initialise();x=m.word('player_x');y=m.word('player_y');heading=m.byte('heading')
        m.byte('control_keys',4)
        for _ in range(24):
            m.word('player_x',x);m.word('player_y',y);m.call('drive_player')
        self.assertEqual(m.byte('speed'),192)
        m.byte('control_keys',6);m.call('drive_player')
        self.assertEqual(m.byte('heading'),(heading+2)&63)
        self.assertNotEqual(m.word('velocity_x'),0)
        m.byte('lap',2);m.byte('control_keys',20)
        for _ in range(7):
            m.word('player_x',x);m.word('player_y',y);m.call('drive_player')
        self.assertEqual(m.byte('speed'),240);m.check_memory()
    def test_spin_bounces_without_damage_and_preserves_tangent_motion_and_heading(self):
        m=VectorMachine();m.initialise();m.byte('section',4)
        p=m.sym['path_nodes']+16;x,y=m.cpu.memory[p:p+2]
        m.word('player_x',x*256);m.word('player_y',(y-5)*256)
        m.word('velocity_x',256);m.word('velocity_y',-768)
        m.byte('speed',150);m.byte('spin_frames',8);heading=m.byte('heading');old_x=m.word('player_x')
        m.call('move_player')
        self.assertEqual((m.byte('energy'),m.byte('hurt_frames'),m.byte('speed'),m.byte('heading')),(100,0,150,heading))
        self.assertGreater(m.word('player_x'),old_x)
        self.assertTrue(0<m.word('velocity_y')<32768)
        nx=((m.byte('bounce_nx')+128)&255)-128
        ny=((m.byte('bounce_ny')+128)&255)-128
        tangent_before=(-256*ny-768*nx)/127
        vx=((m.word('velocity_x')+32768)&65535)-32768
        vy=((m.word('velocity_y')+32768)&65535)-32768
        tangent_after=(-vx*ny+vy*nx)/127
        self.assertLess(abs(tangent_after-tangent_before),24)
        m.byte('spin_frames',0);m.call('border_bounce');self.assertLess(m.byte('energy'),100)
        m.check_memory()
    def test_spin_reflection_preserves_tangent_momentum_at_every_wall_orientation(self):
        m=VectorMachine();m.initialise();p=m.sym['path_nodes']+16
        for heading in range(64):
            angle=heading*math.pi/32;c=math.cos(angle);s=math.sin(angle)
            m.cpu.memory[p+2]=heading;m.byte('section',4);m.byte('spin_frames',8)
            m.byte('energy',100);m.byte('speed',150);m.byte('heading',heading)
            vx=round((1.75*c-.9*s)*256);vy=round((1.75*s+.9*c)*256)
            m.byte('bounce_nx',round(s*127));m.byte('bounce_ny',round(-c*127))
            m.word('velocity_x',vx);m.word('velocity_y',vy);m.call('reflect_velocity')
            x=((m.word('velocity_x')+32768)&65535)-32768
            y=((m.word('velocity_y')+32768)&65535)-32768
            self.assertLess(abs((x*c+y*s)-(vx*c+vy*s)),40,heading)
            self.assertLess(-x*s+y*c,-150,heading)
            self.assertEqual((m.byte('energy'),m.byte('speed'),m.byte('heading')),(100,150,heading))
        m.check_memory()
    def test_start_grid_uses_larger_perspective_sprites_and_distance_shrinks_them(self):
        m=VectorMachine();m.initialise();m.call('prepare_camera')
        for i in (1,2):
            m.call('project_rival',ix=m.sym[f'rival{i}_progress'],iy=m.sym[f'projection{i}'])
            p=m.sym[f'projection{i}'];self.assertEqual(m.cpu.memory[p],1)
            sprite=int.from_bytes(m.cpu.memory[p+4:p+6],'little')
            self.assertEqual(m.cpu.memory[sprite],15 if i==1 else 11)
        m.word('camera_x',40*256);m.word('camera_y',64*256)
        m.byte('camera_cos',127);m.byte('camera_sin',0)
        widths=[];feet=[]
        for distance in (8,12,16,20,28,40,55):
            m.word('rival1_x',(40+distance)*256);m.word('rival1_y',64*256)
            m.call('project_rival',ix=m.sym['rival1_progress'],iy=m.sym['projection1'])
            p=m.sym['projection1'];self.assertEqual(m.cpu.memory[p],1)
            sprite=int.from_bytes(m.cpu.memory[p+4:p+6],'little')
            widths.append(m.cpu.memory[sprite]);feet.append(m.cpu.memory[p+3]+m.cpu.memory[sprite+1])
        self.assertEqual(widths,sorted(widths,reverse=True));self.assertGreater(widths[0],widths[-1])
        self.assertEqual(feet,sorted(feet,reverse=True));m.check_memory()

    def test_real_mask_normal_and_rebound_survive_the_next_throttle_ticks(self):
        m=VectorMachine();m.initialise();p=m.sym['road_map']
        road=bytearray(2048)
        for y in range(20,100):
            for x in range(20,100):road[y*16+x//8]|=128>>(x%8)
        m.cpu.memory[p:p+2048]=road
        m.word('player_x',20*256+128);m.word('player_y',60*256+128)
        m.word('velocity_x',-512);m.word('velocity_y',128);m.byte('heading',32);m.byte('speed',150)
        m.call('move_player')
        self.assertEqual((m.byte('bounce_nx'),m.byte('bounce_ny')),(127,0))
        self.assertEqual(m.word('velocity_y'),128);self.assertTrue(400<m.word('velocity_x')<600)
        self.assertEqual(m.byte('rebound_frames'),10)
        m.byte('keys',4);m.byte('rival1_energy',0);m.byte('rival2_energy',0)
        x=m.word('player_x')
        for _ in range(2):m.call('race_tick')
        self.assertGreater(m.word('player_x'),x);self.assertTrue(0<m.word('velocity_x')<32768)
        self.assertEqual(m.byte('heading'),32);m.check_memory()

    def test_ship_collision_reflects_normal_velocity_and_pushes_both_ships(self):
        for spin in (0,8):
            m=VectorMachine();m.initialise();m.word('player_x',60*256);m.word('player_y',60*256)
            m.word('rival1_x',62*256);m.word('rival1_y',60*256)
            m.word('velocity_x',512);m.word('velocity_y',128);m.byte('spin_frames',spin)
            heading=m.byte('heading');m.call('contact_rival',ix=m.sym['rival1_progress'])
            vx=((m.word('velocity_x')+32768)&65535)-32768
            self.assertTrue(-550<vx<-450);self.assertEqual(m.word('velocity_y'),128)
            self.assertEqual(m.word('rival1_x'),64*256)
            self.assertEqual(m.byte('energy'),100 if spin else 97)
            self.assertEqual(m.byte('rival1_energy'),32 if spin else 44)
            self.assertEqual(m.byte('heading'),heading);m.check_memory()

    def test_stationary_contacts_separate_and_outgoing_ships_are_not_pulled_back(self):
        m=VectorMachine();m.initialise();x,y=m.word('player_x'),m.word('player_y')
        for vx in (0,-512):
            m.word('rival1_x',x+256);m.word('rival1_y',y);m.byte('rival1_hit',0)
            m.word('velocity_x',vx);m.word('velocity_y',0)
            m.call('contact_rival',ix=m.sym['rival1_progress'])
            actual=((m.word('velocity_x')+32768)&65535)-32768
            self.assertLess(actual,0)
            if vx:self.assertEqual(actual,vx)
        m.check_memory()

    def test_mask_normals_and_elastic_response_on_eight_independent_half_planes(self):
        m=VectorMachine();m.initialise();p=m.sym['road_map']
        for nx,ny in ((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)):
            road=bytearray(2048)
            for y in range(128):
                for x in range(128):
                    if nx*(x-64)+ny*(y-64)>=0:road[y*16+x//8]|=128>>(x%8)
            m.cpu.memory[p:p+2048]=road
            m.word('player_x',64*256+128);m.word('player_y',64*256+128)
            m.call('road_normal');scale=90 if nx and ny else 127
            self.assertEqual((m.byte('bounce_nx'),m.byte('bounce_ny')),(nx*scale&255,ny*scale&255))
            length=math.hypot(nx,ny);ux,uy=nx/length,ny/length
            vx,vy=round((-ux-.5*uy)*256),round((-uy+.5*ux)*256)
            m.word('velocity_x',vx);m.word('velocity_y',vy);m.call('reflect_velocity')
            x=((m.word('velocity_x')+32768)&65535)-32768
            y=((m.word('velocity_y')+32768)&65535)-32768
            self.assertGreater(x*ux+y*uy,230)
            self.assertLess(abs((-x*uy+y*ux)-(-vx*uy+vy*ux)),24)
        m.check_memory()

    def test_projected_rivals_remain_visible_while_their_edges_leave_the_screen(self):
        m=VectorMachine();m.initialise();m.word('camera_x',40*256);m.word('camera_y',64*256)
        m.byte('camera_cos',127);m.byte('camera_sin',0);m.word('rival1_x',50*256)
        for y in (54,55,56,73,74):
            m.word('rival1_y',y*256);m.call('project_rival',ix=m.sym['rival1_progress'],iy=m.sym['projection1'])
            p=m.sym['projection1'];self.assertEqual(m.cpu.memory[p],1,y)
            sprite=int.from_bytes(m.cpu.memory[p+4:p+6],'little')
            left,top=m.cpu.memory[p+2:p+4];left=left-256 if left>=241 else left
            width,height=m.cpu.memory[sprite:sprite+2]
            expected=bytearray([0xAA])*864
            for dy in range(height):
                for dx in range(width):
                    i=dy*width+dx;v=(m.cpu.memory[sprite+2+i//4]>>(2*(i%4)))&3
                    x,yy=left+dx,top+dy
                    if v and 0<=x<144 and 0<=yy<48:
                        offset=yy//8*144+x;mask=1<<(yy%8)
                        if v==1:expected[offset]&=255^mask
                        if v==2:expected[offset]|=mask
            m.cpu.memory[m.sym['frame']:m.sym['frame']+864]=bytes([0xAA])*864
            m.call('draw_projection',hl=p);self.assertEqual(m.native_frame(),expected,y)
        m.check_memory()
    def test_spin_knocks_both_rivals_away_and_push_survives_the_next_ai_tick(self):
        for rival in ('rival1','rival2'):
            m=VectorMachine();m.initialise();m.word(rival+'_x',m.word('player_x')+256)
            m.word(rival+'_y',m.word('player_y'));m.byte('spin_frames',8)
            before=m.word(rival+'_x');p=m.sym[rival+'_progress']
            m.call('contact_rival',ix=p)
            self.assertEqual((m.byte('energy'),m.byte(rival+'_energy')),(100,32))
            self.assertEqual(m.word(rival+'_x'),before+512)
            self.assertEqual(m.word(rival+'_push_x'),512)
            m.call('contact_rival',ix=p);self.assertEqual(m.byte(rival+'_energy'),32)
            reference=VectorMachine();reference.initialise()
            reference.call('rival_tick',ix=reference.sym[rival+'_progress'],bc=0)
            m.call('rival_tick',ix=p,bc=0)
            self.assertEqual(m.word(rival+'_x')-reference.word(rival+'_x'),448)
            self.assertEqual(m.word(rival+'_push_x'),448);m.check_memory()
    def test_all_three_compressed_tracks_load_exactly_and_complete(self):
        expected=json.loads((HERE/'assets_manifest.json').read_text(encoding='utf-8'))['tracks']
        for track in range(3):
            m=VectorMachine();m.byte('track_index',track);m.initialise(1)
            for label,length,key in [('texture_map',2048,'visual_sha256'),('road_map',2048,'road_sha256'),
                                     ('path_nodes',512,'path_sha256'),('skyline',144,'sky_sha256')]:
                p=m.sym[label]
                self.assertEqual(hashlib.sha256(bytes(m.cpu.memory[p:p+length])).hexdigest(),expected[track][key])
            for frame in range(1800):
                m.call('race_tick')
                if m.byte('phase')!=1:break
            self.assertEqual(m.byte('phase'),3,(track,frame,m.byte('energy')))
            self.assertEqual(m.byte('lap'),4)
            # Ordinary automatic driving must no longer lap the opponents easily.
            self.assertGreaterEqual(min(m.byte('rival1_lap'),m.byte('rival2_lap')),3)
            self.assertGreaterEqual(m.byte('player_finish'),2)
            m.check_memory()
    def test_full_cup_keeps_points_between_races_and_returns_to_menu_without_stack_leaks(self):
        m=VectorMachine();m.start();m.step({0x28})
        self.assertEqual(m.byte('session_mode'),0)
        expected_sp=m.cpu.sp
        expected_total=[0,0,0]
        for track in range(3):
            self.assertEqual(m.byte('track_index'),track)
            self.assertEqual(m.byte('cup_round'),track)
            m.step({0x0B})
            m.wait_for_go()
            for frame in range(1800):
                m.step()
                if m.byte('phase')!=1:break
            self.assertEqual(m.byte('phase'),3,(track,frame))
            self.assertEqual(m.cpu.sp,expected_sp)
            total=list(m.cpu.memory[m.sym['cup_points']:m.sym['cup_points']+3])
            points=list(m.cpu.memory[m.sym['race_points']:m.sym['race_points']+3])
            places=list(m.cpu.memory[m.sym['race_places']:m.sym['race_places']+3])
            self.assertEqual(points,[[10,7,5][place-1] for place in places])
            expected_total=[old+new for old,new in zip(expected_total,points)]
            self.assertEqual(total,expected_total)
            # Held ENTER advances only once, including after loading the next track.
            m.release_confirm();m.step({0x28});m.step({0x28})
        self.assertEqual(m.byte('phase'),6)
        self.assertEqual(sorted(m.cpu.memory[m.sym['cup_places']:m.sym['cup_places']+3]),[1,2,3])
        m.release_confirm();m.step({0x28});self.assertEqual(m.byte('phase'),0)
        self.assertEqual(m.cpu.sp,expected_sp);m.check_memory()
    def test_menu_selects_single_race_and_cup_results_are_awarded_once(self):
        m=VectorMachine();m.start();m.step({0x1F});m.step();m.step({0x22});m.step({0x28})
        self.assertEqual((m.byte('session_mode'),m.byte('track_index')),(1,1))
        m.byte('lap',4);m.byte('phase',3);m.call('finish_race')
        self.assertEqual(list(m.cpu.memory[m.sym['cup_points']:m.sym['cup_points']+3]),[0,0,0])
        m.call('advance_result');self.assertEqual(m.byte('phase'),0)
        m.byte('session_mode',0);m.call('new_game',a=0);m.byte('lap',4);m.byte('phase',3)
        m.call('finish_race');first=bytes(m.cpu.memory[m.sym['cup_points']:m.sym['cup_points']+3])
        m.call('finish_race');self.assertEqual(bytes(m.cpu.memory[m.sym['cup_points']:m.sym['cup_points']+3]),first)
    def test_cup_ties_use_the_last_race_order_and_retired_ships_score_zero(self):
        m=VectorMachine();m.initialise();m.byte('energy',0);m.byte('rival1_energy',0)
        m.byte('phase',4);m.call('finish_race')
        self.assertEqual(list(m.cpu.memory[m.sym['race_points']:m.sym['race_points']+3]),[0,0,10])
        m.byte('cup_round',2)
        m.cpu.memory[m.sym['cup_points']:m.sym['cup_points']+3]=bytes([20,20,15])
        m.cpu.memory[m.sym['race_places']:m.sym['race_places']+3]=bytes([2,1,3])
        m.call('advance_result')
        self.assertEqual(list(m.cpu.memory[m.sym['cup_places']:m.sym['cup_places']+3]),[2,1,3])
        self.assertEqual(m.byte('phase'),6)
    def test_finished_opponent_keeps_its_place_and_cannot_be_hit_after_the_line(self):
        m=VectorMachine();m.initialise();m.word('rival1_progress',0x7FC0);m.byte('rival1_lap',3)
        m.byte('rival1_started',1)
        m.call('rival_tick',ix=m.sym['rival1_progress'],bc=224)
        self.assertEqual(m.byte('rival1_lap'),4);self.assertEqual(m.byte('rival1_finish'),1)
        progress=m.word('rival1_progress');m.call('rival_tick',ix=m.sym['rival1_progress'],bc=224)
        self.assertEqual(m.word('rival1_progress'),progress)
        m.word('player_x',m.word('rival1_x'));m.word('player_y',m.word('rival1_y'));m.byte('spin_frames',8)
        m.call('contact_rival',ix=m.sym['rival1_progress']);self.assertEqual(m.byte('rival1_energy'),48)
        m.byte('rival2_energy',0);m.byte('player_finish',2);m.byte('lap',4);m.byte('section',0)
        m.call('finish_race');self.assertEqual(list(m.cpu.memory[m.sym['race_places']:m.sym['race_places']+3]),[2,1,3])
    def test_editable_sprite_bmp_pixels_are_preserved_and_match_the_binary(self):
        from graphics import read_sprite,load_frames,COLORS,FRAME_SPECS,packed_sprite,mirrored,DIRECTIONS
        from bitmap import read_bmp,write_bmp
        m=VectorMachine()
        for name,size in FRAME_SPECS.items():
            path=HERE/'graphics'/(name+'.bmp');w,h,_=read_bmp(path);data=read_sprite(path,(w,h))
            flip=0;p=m.sym[name]
            if name.startswith('player_'):
                q=m.sym['player_sprites']+3*DIRECTIONS.index(name[7:])
                p=int.from_bytes(m.cpu.memory[q:q+2],'little');flip=m.cpu.memory[q+2]
            packed=packed_sprite(mirrored(data) if flip else data)
            self.assertEqual(bytes(m.cpu.memory[p:p+len(packed)]),packed,name)
            # Actual Z80 unpack/mirror/alpha drawing must reproduce every source pixel.
            m.cpu.memory[m.sym['frame']:m.sym['frame']+864]=b'\xAA'*864
            expected=bytearray(m.native_frame())
            for y in range(h):
                for x in range(w):
                    value=data[2+y*w+x];offset=(y+17)//8*144+x+40;mask=1<<((y+17)&7)
                    if value==1:expected[offset]&=255^mask
                    if value==2:expected[offset]|=mask
            m.call('draw_sprite_flags',hl=p,de=0x2811,a=flip)
            self.assertEqual(m.native_frame(),bytes(expected),name)
        m.check_memory()
        with tempfile.TemporaryDirectory(prefix='vector-bmp-') as folder:
            root=Path(folder);out=root/'docs';ref=reference()
            shutil.copytree(HERE/'graphics',root/'graphics')
            frames=load_frames(root/'graphics',out,ref.FONT)
            path=root/'graphics/player_north.bmp';w,h,pixels=read_bmp(path)
            pixels[0]=COLORS[2];write_bmp(path,w,h,pixels);before=path.read_bytes()
            changed=load_frames(root/'graphics',out,ref.FONT)
            self.assertEqual(path.read_bytes(),before)
            self.assertNotEqual(frames['player_north'],changed['player_north'])
            self.assertEqual(changed['player_north'][2],2)
    def test_spin_completes_two_cardinal_turns_in_half_the_previous_time(self):
        m=VectorMachine();m.initialise();m.byte('keys',32);m.byte('pressed',32);m.call('race_tick')
        heading=m.byte('heading');sequence=[]
        for tick in range(8):
            self.assertEqual(m.byte('spin_frames'),8-tick)
            m.call('select_player_sprite');sequence.append((m.cpu.hl,m.cpu.a))
            q=m.sym['player_sprites']+((tick*2)%8)*3
            self.assertEqual(sequence[-1],(int.from_bytes(m.cpu.memory[q:q+2],'little'),m.cpu.memory[q+2]))
            self.assertEqual(m.byte('heading'),heading)
            m.byte('keys',0);m.byte('pressed',0);m.call('race_tick')
        self.assertEqual(sequence[:4],sequence[4:]);self.assertEqual(m.byte('spin_frames'),0)
        self.assertEqual(m.byte('spin_cooldown'),40);m.check_memory()

    def test_final_results_cup_and_menu_each_require_a_stable_enter_release(self):
        for language in ('FR','EN'):
            m=VectorMachine(language);m.start()
            m.byte('phase',3);m.byte('cup_round',2);m.byte('race_awarded',1)
            m.byte('confirm_release',0)
            m.release_confirm();m.step({0x28})
            self.assertEqual(m.byte('phase'),6)
            for expected,next_phase in ((6,0),(0,7)):
                for _ in range(8):m.step({0x28});self.assertEqual(m.byte('phase'),expected)
                for _ in range(5):
                    m.step();m.step({0x28})
                    self.assertEqual(m.byte('phase'),expected)
                m.release_confirm()
                for _ in range(8):m.step();self.assertEqual(m.byte('phase'),expected)
                m.step({0x28});self.assertEqual(m.byte('phase'),next_phase)
            m.check_memory()
    def test_race_keeps_the_skyline_clear_and_floor_visible_behind_compact_hud(self):
        m=VectorMachine();m.initialise();m.byte('rival1_energy',0);m.byte('rival2_energy',0)
        m.call('prepare_camera');m.call('prepare_rows');m.call('floor_render');m.call('draw_skyline')
        world=m.native_frame();m.call('render');image=m.native_frame()
        # No course name or DEMO banner obscures the distant road and skyline.
        self.assertEqual(image[:144*3],world[:144*3])
        self.assertTrue(any(world[720:864]),'The floor must reach the last LCD page')
        # Clear gaps between HUD islands must be exactly the original floor.
        for x in (33,34,53,54,55,56,76,77,78,79,99,107,108,109,110,111,142,143):
            self.assertEqual(image[720+x],world[720+x],x)
        m.check_memory()
    def test_minimap_projects_world_positions_and_draws_blinking_player(self):
        m=VectorMachine();m.initialise();m.byte('rival1_energy',0);m.byte('rival2_energy',0)
        m.word('player_x',64*256);m.word('player_y',64*256)
        frames=[]
        for tick in (0,4):
            m.call('clear_frame');m.byte('frame_counter',tick);m.call('draw_minimap');frames.append(m.native_frame())
        def pixel(data,x,y):return bool(data[y//8*144+x]&(1<<(y&7)))
        self.assertFalse(pixel(frames[0],16,40));self.assertTrue(pixel(frames[1],16,40))
        self.assertNotEqual(frames[0],frames[1])
        m.call('map_position',de=0x7F7F);self.assertEqual(m.cpu.de,0x1F2F)
        m.check_memory()
    def test_full_ui_demo_pause_photo_help_restart_and_caller_return(self):
        for language in ('FR','EN'):
            m=VectorMachine(language)
            original={'af':0x1234,'bc':0x5678,'de':0x9ABC,'hl':0x2468,'ix':0x1357,'iy':0x3579}
            for r,v in original.items():setattr(m.cpu,r,v)
            m.start();self.assertEqual(m.byte('phase'),0)
            m.step({0x0B});self.assertEqual(m.byte('demo_mode'),1)
            m.step({0x0B});self.assertEqual(m.byte('demo_mode'),1)
            m.wait_for_go()
            m.step();m.step({0x39});self.assertEqual(m.byte('phase'),2)
            count=m.word('frame_counter');m.step();m.step();self.assertEqual(m.word('frame_counter'),count)
            m.step({0x0C});self.assertEqual(m.byte('photo_mode'),1)
            m.step();m.step({0x17});self.assertEqual(m.byte('phase'),5)
            m.step();m.step({0x28});self.assertEqual(m.byte('phase'),2)
            m.step();m.step({0x39});self.assertEqual(m.byte('phase'),1)
            m.step({0x05});self.assertEqual(m.byte('demo_mode'),0)
            m.step({0x05});self.assertEqual(m.word('frame_counter'),0)
            self.assertEqual(m.byte('phase'),7);m.wait_for_go()
            m.step({0x20,0x21,0x1E});self.assertGreater(m.byte('speed'),0)
            m.step({0x02});self.assertEqual(m.cpu.pc,RETURN)
            self.assertEqual(m.cpu.sp,STACK+2)
            for r,v in original.items():self.assertEqual(getattr(m.cpu,r),v,r)
            m.check_memory()
    def test_multi_key_matrix_and_130_tstate_settling(self):
        m=VectorMachine()
        for raw,keys,aux in [({0x20,0x21,0x1E,0x12},53,0),({0x1F,0x22},10,0),
                             ({0x39,0x02},192,0),({0x28,0x0B,0x05,0x0C,0x17},0,31),({0x51},128,0)]:
            m.raw_keys=raw;m.call('poll_keyboard')
            self.assertEqual((m.byte('keys'),m.byte('aux_keys')),(keys,aux),raw)
        m.check_memory()
    def test_signed_multiply_and_division(self):
        m=VectorMachine()
        for d in (-127,-12,-1,0,1,7,127):
            for e in (0,1,127,164,224,255):
                m.call('mul_signed',d=d&255,e=e)
                self.assertEqual(m.cpu.hl,(d*e)&65535)
        for numerator,divisor in ((210,7),(7000,61),(1023,3),(65535,127)):
            m.call('divide_hl_c',hl=numerator,c=divisor)
            self.assertEqual(m.cpu.hl,numerator//divisor)
    def test_boost_locked_on_lap_one_and_energy_floor_on_lap_two(self):
        m=VectorMachine();m.initialise();m.byte('control_keys',20)
        m.byte('speed',160);m.byte('lap',1);m.call('drive_player')
        self.assertEqual(m.byte('boosting'),0);self.assertEqual(m.byte('energy'),100)
        m.byte('lap',2);m.call('drive_player')
        self.assertEqual(m.byte('boosting'),1);self.assertEqual(m.byte('energy'),99)
        m.byte('energy',12);m.call('drive_player')
        self.assertEqual(m.byte('energy'),12);self.assertEqual(m.byte('boosting'),0)
        m.byte('energy',80);m.byte('control_keys',16);m.byte('speed',80);m.call('drive_player')
        self.assertEqual(m.byte('speed'),88);self.assertEqual(m.byte('boosting'),1)
        m.byte('control_keys',24);m.byte('speed',100);m.byte('energy',80);m.call('drive_player')
        self.assertEqual(m.byte('speed'),88);self.assertEqual(m.byte('energy'),80)
        self.assertEqual(m.byte('boosting'),0)
    def test_spin_keeps_velocity_and_blocks_steering_and_boost(self):
        m=VectorMachine();m.initialise();m.byte('control_pressed',32);m.call('start_spin')
        m.word('velocity_x',120);m.word('velocity_y',50);m.byte('control_keys',22);m.byte('lap',2)
        heading=m.byte('heading');energy=m.byte('energy');m.call('drive_player')
        self.assertEqual((m.byte('heading'),m.byte('energy')),(heading,energy))
        self.assertEqual((m.word('velocity_x'),m.word('velocity_y')),(120,50))
        self.assertEqual(m.byte('boosting'),0)
        m.byte('spin_frames',0);m.call('start_spin');self.assertEqual(m.byte('spin_frames'),0)
    def test_border_rebound_keeps_ship_inside_and_applies_damage_cooldown(self):
        m=VectorMachine();m.initialise();m.byte('section',4)
        node=m.sym['path_nodes']+4*4;x,y=m.cpu.memory[node:node+2]
        m.word('player_x',x*256);m.word('player_y',(y-5)*256)
        m.word('velocity_x',0);m.word('velocity_y',-768);m.byte('speed',100)
        old=(m.word('player_x'),m.word('player_y'));m.call('move_player')
        self.assertEqual((m.word('player_x'),m.word('player_y')),old)
        self.assertLess(m.byte('energy'),100);self.assertTrue(0<m.word('velocity_y')<32768)
        health=m.byte('energy');m.call('border_bounce');self.assertEqual(m.byte('energy'),health)
        m.check_memory()
    def test_ordered_checkpoints_prevent_finish_line_shortcuts_and_reverse_laps(self):
        m=VectorMachine();m.initialise();m.byte('old_section',127);m.byte('section',0)
        m.call('update_laps');self.assertEqual(m.byte('lap'),1)
        for section in (34,66,98):m.byte('section',section);m.call('update_laps')
        self.assertEqual(m.byte('checkpoint'),3)
        m.byte('old_section',0);m.byte('section',127);m.call('update_laps')
        self.assertEqual(m.byte('lap'),1)
        m.byte('old_section',127);m.byte('section',0);m.call('update_laps')
        self.assertEqual(m.byte('lap'),2);self.assertEqual(m.byte('checkpoint'),0)
        m.byte('lap',3);m.byte('checkpoint',3);m.call('update_laps');self.assertEqual(m.byte('phase'),3)
    def test_recharge_and_spin_damage_to_opponents(self):
        m=VectorMachine();m.initialise();m.byte('energy',70);m.byte('section',47);m.call('update_laps')
        self.assertEqual(m.byte('energy'),72)
        m.word('rival1_x',m.word('player_x'));m.word('rival1_y',m.word('player_y'))
        m.byte('spin_frames',8);m.call('contact_rival',ix=m.sym['rival1_progress'])
        self.assertEqual(m.byte('energy'),72);self.assertEqual(m.byte('rival1_energy'),32)
        m.call('contact_rival',ix=m.sym['rival1_progress']);self.assertEqual(m.byte('rival1_energy'),32)
    def test_opponent_retirement_rank_and_player_destruction(self):
        m=VectorMachine();m.initialise();m.byte('rival1_energy',16)
        m.word('rival1_x',m.word('player_x'));m.word('rival1_y',m.word('player_y'))
        m.byte('spin_frames',8);m.call('contact_rival',ix=m.sym['rival1_progress'])
        self.assertEqual(m.byte('rival1_energy'),0);m.call('update_rank')
        self.assertEqual(m.byte('rank'),2)
        m.byte('energy',0);m.call('race_tick');self.assertEqual(m.byte('phase'),4)
        m.check_memory()
    def test_distant_ships_remain_visible_and_edge_clipping_preserves_memory(self):
        m=VectorMachine();m.initialise()
        for width in (3,5,7,9,11,15):
            m.call('clear_frame');m.call('draw_sprite',hl=m.sym['rival_sprite_'+str(width)],de=0x0A0A)
            self.assertTrue(any(m.native_frame()),width)
        m.call('draw_sprite',hl=m.sym['ship_straight'],de=0x8C26)
        m.check_memory()
    def test_real_floor_matches_reference_at_all_64_headings(self):
        m=VectorMachine();m.initialise();ref=reference()
        texture=bytes(m.cpu.memory[m.sym['texture_map']:m.sym['texture_map']+2048])
        for angle in range(64):
            m.byte('heading',angle);m.call('prepare_camera');m.call('prepare_rows')
            p=m.sym['row_table'];rows=[struct.unpack('<4H',bytes(m.cpu.memory[p+i*8:p+i*8+8])) for i in range(40)]
            expected=ref.rows_for((m.word('camera_x')/256,m.word('camera_y')/256,
                                  math.cos(angle*math.pi/32),math.sin(angle*math.pi/32)),2,1,bottom=48)
            for actual,wanted in zip(rows,expected):
                self.assertTrue(all(abs(((a-b+32768)&65535)-32768)<=1 for a,b in zip(actual,wanted)),angle)
            m.call('floor_render');self.assertEqual(m.native_frame(),bytes(ref.reference_floor(texture,rows,2,1)),angle)
        m.check_memory()
    def test_both_languages_upload_six_exact_native_pages(self):
        for language in ('FR','EN'):
            m=VectorMachine(language);m.initialise();m.call('show_frame')
            self.assertEqual([row for row,_ in m.uploads],list(range(6)))
            self.assertEqual(bytes(m.display),m.native_frame());m.check_memory()
    def test_demo_completes_three_laps_without_memory_damage(self):
        m=VectorMachine();m.initialise(demo=1)
        history=[]
        for frame in range(1600):
            m.call('race_tick')
            if frame%100==0:history.append((frame,m.byte('section'),m.byte('lap'),m.byte('energy')))
            if m.byte('phase')!=1:break
        self.assertEqual(m.byte('phase'),3,history)
        self.assertEqual(m.byte('lap'),4);m.check_memory()


if __name__=='__main__':
    parser=Parser('Verifier le vrai programme Z80 Pocket Vector.','Check the actual Pocket Vector Z80 program.')
    parser.parse_args();unittest.main(argv=[sys.argv[0]],verbosity=2)
