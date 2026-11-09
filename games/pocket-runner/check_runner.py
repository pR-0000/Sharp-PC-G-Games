"""FR/EN: real Z80 CPU scenarios and independent movement/BFS reference."""
from pathlib import Path
from collections import deque
import hashlib,json,sys,unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser
from assets import levels

class RunnerMachine(Machine):
    def __init__(self,language='FR'):
        self.tstates=0
        super().__init__('runner_'+language,HERE/'build')
        self.cpu.set_input_callback(lambda p: (_ for _ in ()).throw(AssertionError(f'Unexpected IN {p}')))
        self.cpu.set_output_callback(lambda p,v: (_ for _ in ()).throw(AssertionError(f'Unexpected OUT {p}')))
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
    def terrain(self):
        p=self.sym['world'];return bytes(self.cpu.memory[p:p+240])
    def tile(self,x,y,value=None):
        p=self.sym['world']+y*20+x
        if value is not None:self.cpu.memory[p]=value
        return self.cpu.memory[p]
    def guard(self,i,pos=None,trap=0,spawn=None):
        p=self.sym['guards']+3*i
        if pos is not None:self.cpu.memory[p:p+3]=bytes((pos,trap,pos if spawn is None else spawn))
        return tuple(self.cpu.memory[p:p+3])
    def arena(self):
        for y in range(12):
            for x in range(20):self.tile(x,y,2 if x in (0,19) or y==11 else 0)
        for x in range(1,19):self.tile(x,5,1)
        for i in range(3):self.guard(i,21+i)
        self.set_byte('player_pos',88)
        self.set_byte('player_clock',0);self.set_byte('guard_clock',0)
    def hole(self,slot,pos,timer):
        p=self.sym['holes']+2*slot;self.cpu.memory[p:p+2]=bytes((pos,timer))

def effective(m,pos):
    value=m.cpu.memory[m.sym['world']+pos]
    return 3 if value==7 and m.byte('exit_active') else 0 if value==7 else value

def reference_move(m,pos,direction):
    if effective(m,pos) in (1,2):return None
    x,y=pos%20,pos//20
    dx,dy=((-1,0),(1,0),(0,-1),(0,1))[direction]
    nx,ny=x+dx,y+dy
    if not(0<=nx<20 and 0<=ny<12):return None
    dest=ny*20+nx
    if effective(m,dest) in (1,2):return None
    current=effective(m,pos)
    if direction==2 and current!=3:return None
    if direction<2:
        below=pos+20
        support=(current in (3,4) or below>=240 or effective(m,below) in (1,2,3)
                 or any(m.guard(i)[0]==below and m.guard(i)[1] for i in range(3)))
        if not support:return None
    return dest

def reference_distances(m):
    reverse=[[] for _ in range(240)]
    for pos in range(240):
        for direction in range(4):
            dest=reference_move(m,pos,direction)
            if dest is not None:reverse[dest].append(pos)
    distances=[255]*240;start=m.byte('player_pos');distances[start]=0
    queue=deque([start])
    while queue:
        pos=queue.popleft()
        for source in reverse[pos]:
            if distances[source]==255:distances[source]=distances[pos]+1;queue.append(source)
    return bytes(distances)

class RunnerChecks(unittest.TestCase):
    def test_language_title_and_return(self):
        for language in ('FR','EN'):
            m=RunnerMachine(language);self.assertIn(b'POCKET RUNNER',m.text[0]);m.start()
            self.assertEqual(bytes(m.text[0][20:24]),b'0000')
            self.assertEqual(bytes(m.text[3][20:24]),b'N 01' if language=='FR' else b'L 01')
            m.tap(0x51);self.assertEqual(m.cpu.pc,RETURN)
            self.assertEqual((m.cpu.sp,m.cpu.ix,m.cpu.iy),(0x1ff2,0x1234,0x5678));m.check_memory()
    def test_all_levels_decompress_exactly(self):
        m=RunnerMachine();m.start()
        for i,level in enumerate(levels()):
            m.set_byte('level_index',i);m.routine('load_level')
            self.assertEqual(m.terrain(),level['terrain'])
            self.assertEqual(m.byte('player_pos'),level['spawn'])
            self.assertEqual([m.guard(i)[0] for i in range(3)],level['guards'])
            self.assertEqual(m.byte('gold_flags'),255)
        m.check_memory()
    def test_movement_reference_all_cells_levels_exit_states(self):
        m=RunnerMachine();m.start()
        for level in range(3):
            m.set_byte('level_index',level);m.routine('load_level')
            for active in (0,1):
                m.set_byte('exit_active',active)
                for pos in range(240):
                    for direction in range(4):
                        expected=reference_move(m,pos,direction)
                        r=m.routine('can_move',a=pos,c=direction)
                        actual=r['af']>>8 if r['af']&1 else None
                        self.assertEqual(actual,expected,(level,active,pos,direction))
        m.check_memory()
    def test_bfs_independent_reference(self):
        m=RunnerMachine();m.start()
        for level in range(3):
            m.set_byte('level_index',level);m.routine('load_level')
            for pos in (m.byte('player_pos'),24,94,157):
                m.set_byte('player_pos',pos)
                expected=reference_distances(m)
                m.routine('build_distances')
                p=m.sym['ai_dist'];self.assertEqual(bytes(m.cpu.memory[p:p+240]),expected,(level,pos))
                self.assertLessEqual(m.byte('bfs_tail'),240)
        m.check_memory()
    def test_all_gold_and_exit_reachable(self):
        m=RunnerMachine();m.start()
        for i,level in enumerate(levels()):
            m.set_byte('level_index',i);m.routine('load_level')
            # Forward directed graph: inspect topology without enemy collision.
            queue=deque([level['spawn']]);seen={level['spawn']}
            while queue:
                pos=queue.popleft()
                for direction in range(4):
                    dest=reference_move(m,pos,direction)
                    if dest is not None and dest not in seen:seen.add(dest);queue.append(dest)
            self.assertTrue(set(level['gold'])<=seen,(i,seen))
            m.set_byte('exit_active',1);queue=deque(seen)
            while queue:
                pos=queue.popleft()
                for direction in range(4):
                    dest=reference_move(m,pos,direction)
                    if dest is not None and dest not in seen:seen.add(dest);queue.append(dest)
            self.assertIn(level['exit'],seen)
        m.check_memory()
    def test_gravity_ladder_rope_and_drop(self):
        m=RunnerMachine();m.start();m.arena();m.set_byte('player_pos',68)
        m.set_byte('held_key',0);m.routine('player_step');self.assertEqual(m.byte('player_pos'),88)
        m.routine('player_step');self.assertEqual(m.byte('player_pos'),88)
        m.tile(8,4,3);m.set_byte('held_key',0x20);m.routine('player_step');self.assertEqual(m.byte('player_pos'),68)
        m.tile(8,3,4);m.set_byte('held_key',0);m.routine('player_step');self.assertEqual(m.byte('player_pos'),68)
        m.set_byte('held_key',0x1f);m.routine('player_step');self.assertEqual(m.byte('player_pos'),88)
        m.check_memory()
    def test_dig_left_right_stone_and_four_hole_limit(self):
        m=RunnerMachine();m.start();m.arena()
        m.routine('dig',c=0);self.assertEqual(m.tile(7,5),0)
        m.routine('dig',c=1);self.assertEqual(m.tile(9,5),0)
        for x in (11,14):m.set_byte('player_pos',x+80);m.routine('dig',c=0)
        m.set_byte('player_pos',97);m.routine('dig',c=0);self.assertEqual(m.tile(16,5),1)
        m.tile(16,5,2);m.hole(0,107,0);m.routine('dig',c=0);self.assertEqual(m.tile(16,5),2)
        m.check_memory()
    def test_hole_closes_and_kills_player(self):
        m=RunnerMachine();m.start();m.arena();m.tile(7,5,0);m.hole(0,107,2)
        m.routine('holes_tick');self.assertEqual(m.tile(7,5),0)
        m.routine('holes_tick');self.assertEqual(m.tile(7,5),1)
        m.tile(7,5,0);m.hole(0,107,1);m.set_byte('player_pos',107)
        m.routine('holes_tick');self.assertEqual(m.byte('lives'),2);self.assertEqual(m.byte('died'),1)
        m.check_memory()
    def test_guard_trap_escape_and_respawn(self):
        m=RunnerMachine();m.start();m.arena();m.tile(7,5,0);m.hole(0,107,96);m.guard(0,87,spawn=37)
        m.routine('build_distances');m.routine('guards_step')
        self.assertEqual(m.guard(0)[:2],(107,4))
        for _ in range(4):m.routine('guards_step')
        self.assertEqual(m.guard(0)[:2],(87,0))
        m.guard(0,107,3,37);m.hole(0,107,1);m.routine('holes_tick')
        self.assertEqual(m.guard(0),(37,0,37));self.assertEqual(m.word('score'),25)
        m.check_memory()
    def test_trapped_guard_supports_player(self):
        m=RunnerMachine();m.start();m.arena();m.tile(7,5,0);m.guard(0,107,3)
        r=m.routine('supported',a=87);self.assertTrue(r['af']&1)
        m.guard(0,107,0);self.assertFalse(m.routine('supported',a=87)['af']&1)
        m.check_memory()
    def test_respawn_avoids_an_occupied_start(self):
        m=RunnerMachine();m.start();m.arena()
        m.guard(0,107,3,37);m.guard(1,37);m.guard(2,38)
        m.routine('respawn_guard',ix=m.sym['guards'])
        positions=[m.guard(i)[0] for i in range(3)]
        self.assertEqual(len(set(positions)),3)
        self.assertEqual(m.guard(0)[0]//20,1);m.check_memory()
    def test_guards_take_ladder_route(self):
        m=RunnerMachine();m.start();m.arena()
        for y in range(4,11):m.tile(3,y,3)
        m.set_byte('player_pos',95);m.guard(0,215)
        m.routine('build_distances');m.routine('guards_step')
        self.assertEqual(m.guard(0)[0],214)
        m.check_memory()
    def test_gold_unlocks_exit_and_cannot_score_twice(self):
        m=RunnerMachine();m.start();level=levels()[0]
        for i,pos in enumerate(level['gold']):
            m.set_byte('player_pos',pos);m.routine('collect_gold');m.routine('collect_gold')
            self.assertEqual(m.byte('gold_left'),7-i)
            self.assertEqual(m.word('score'),10*(i+1))
        self.assertEqual(m.byte('exit_active'),1)
        m.routine('draw_game');self.assertEqual(bytes(m.text[1][20:24]),b'SORT')
        m.check_memory()
    def test_guards_remain_in_distinct_cells(self):
        m=RunnerMachine();m.start();m.arena();m.set_byte('player_pos',85)
        for i in range(3):m.guard(i,87+i)
        for _ in range(2):
            m.routine('build_distances');m.routine('guards_step')
            positions=[m.guard(i)[0] for i in range(3)]
            self.assertEqual(len(set(positions)),3)
        m.check_memory()
    def test_lives_game_over_and_restart(self):
        m=RunnerMachine();m.start()
        for lives in (2,1,0):m.routine('lose_life');self.assertEqual(m.byte('lives'),lives)
        self.assertEqual(m.byte('phase'),2);self.assertIn(b'PARTIE TERMINEE',m.text[1])
        m.tap(0x28);self.assertEqual((m.byte('phase'),m.byte('lives')),(1,3));m.check_memory()
    def test_level_progression_and_victory(self):
        for lang in ('FR','EN'):
            m=RunnerMachine(lang);m.start()
            for stage in range(3):
                m.set_byte('player_pos',m.byte('exit_pos'));m.set_byte('exit_active',1)
                m.set_byte('held_key',0);m.set_byte('player_clock',2)
                m.routine('world_step')
                self.assertEqual(m.byte('level_index'),stage+1)
            self.assertEqual(m.byte('phase'),3);self.assertEqual(m.word('score'),300);m.check_memory()
    def test_pause_help_and_continuous_movement(self):
        m=RunnerMachine();m.start();m.tap(0x39)
        before=bytes(m.cpu.memory[m.sym['data_start']:m.sym['program_end']])
        for _ in range(20):m.poll(0)
        after=bytes(m.cpu.memory[m.sym['data_start']:m.sym['program_end']])
        # Input fields change on release; clocks, terrain and actor state freeze.
        self.assertEqual(m.byte('player_clock'),before[m.sym['player_clock']-m.sym['data_start']])
        self.assertEqual(m.terrain(),before[m.sym['world']-m.sym['data_start']:m.sym['world']-m.sym['data_start']+240])
        m.tap(0x39);m.tap(0x17);self.assertEqual(m.byte('phase'),4)
        m.tap(0x28);self.assertEqual(m.byte('phase'),1)
        m.arena();pos=m.byte('player_pos')
        for _ in range(6):m.poll(0x22)
        self.assertGreater(m.byte('player_pos'),pos);m.check_memory()
    def test_camera_clipping_and_native_score(self):
        m=RunnerMachine();m.start()
        for row in range(12):
            m.set_byte('player_pos',row*20+2);m.routine('draw_game')
            self.assertEqual(m.byte('camera_y'),max(0,min(8,row-1)))
        for score in (0,9,99,999,9999):
            m.set_word('score',score);m.routine('draw_game')
            self.assertEqual(bytes(m.text[0][20:24]),f'{score:04}'.encode())
        m.routine('add_score',hl=100);self.assertEqual(m.word('score'),9999)
        m.check_memory()
    def test_all_ui_strings_fit(self):
        for lang in ('FR','EN'):
            m=RunnerMachine(lang)
            for name in ('title_text','subtitle','start_text','title_help','help_1','help_2','help_3','help_4',
                         'pause_text','over_text','win_text','restart_text'):
                p=m.sym[name];self.assertLessEqual(bytes(m.cpu.memory[p:p+64]).index(0),24,(lang,name))

def main():
    parser=Parser('Verifier Pocket Runner sur CPU Z80.','Verify Pocket Runner on a Z80 CPU.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    report={'tests':result.testsRun,'success':result.wasSuccessful(),'failures':len(result.failures),'errors':len(result.errors),
            'movement_cases':5760,'bfs_maps':12,'source':'actual Z80 binaries with strict simulated IOCS',
            'physical_hardware_tested':False,'full_keyboard_campaign_completed':False,
            'note':'Level topology is checked independently; victory transitions use explicit RAM fixtures.'}
    (HERE/'build/cpu_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit(1)
if __name__=='__main__':main()
