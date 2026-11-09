"""FR/EN: Z80 gameplay and pixel-blitter checks, simulated IOCS only."""
from pathlib import Path
import json
import sys
import unittest
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,IOCS,RETURN
from cli_i18n import Parser,pick

class InvadersMachine(Machine):
    def __init__(self,language='FR'):
        super().__init__('invaders_'+language,HERE/'build')
        self.cpu.set_input_callback(lambda p: (_ for _ in ()).throw(AssertionError(f'Unexpected IN {p}')))
        self.cpu.set_output_callback(lambda p,v: (_ for _ in ()).throw(AssertionError(f'Unexpected OUT {p}')))
    def rom_return(self,key=None):
        if self.cpu.pc==0xBFD0:
            row,col,width=self.cpu.d,self.cpu.e,self.cpu.b
            self.text[row][col:col+(width+4)//5]=b' '*((width+4)//5)
        super().rom_return(key)
    def routine(self,name,**registers):
        saved={r:getattr(self.cpu,r) for r in ('pc','sp','af','bc','de','hl','ix','iy')}
        stack=bytes(self.cpu.memory[0x1e00:0x2000])
        self.cpu.pc=self.sym[name];self.cpu.sp=0x1ff0
        self.cpu.memory[0x1ff0:0x1ff2]=RETURN.to_bytes(2,'little')
        for key,value in registers.items():setattr(self.cpu,key,value)
        self.seek_key()
        assert self.cpu.pc==RETURN,(name,self.cpu.pc)
        result={r:getattr(self.cpu,r) for r in ('af','bc','de','hl')}
        self.cpu.memory[0x1e00:0x2000]=stack
        for key,value in saved.items():setattr(self.cpu,key,value)
        return result
    def step(self):self.poll(0)
    def remove_shields(self):
        p=self.sym['shields'];self.cpu.memory[p:p+3]=bytes(3)

class InvadersChecks(unittest.TestCase):
    def test_bilingual_titles_and_monitor_return(self):
        for lang in ('FR','EN'):
            m=InvadersMachine(lang);self.assertIn(b'POCKET INVADERS',bytes(m.text[0]))
            m.start();self.assertEqual(m.byte('remaining'),16)
            self.assertEqual(bytes(m.text[0][20:24]),b'0000')
            self.assertEqual(m.text[1][19],ord('V' if lang=='FR' else 'W'))
            m.tap(0x02)
            self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,0x1ff2,0x1234,0x5678))
            m.check_memory()
    def test_pixel_blitter_matches_reference_for_all_shifts_and_clipped_edges(self):
        m=InvadersMachine();m.start()
        for x in (0,53,85,89,90,119):
            for y in range(28):
                p=m.sym['screen_buffer'];m.cpu.memory[p:p+480]=bytes(480)
                glyph=bytes(m.cpu.memory[m.sym['glyph_alien_a']:m.sym['glyph_alien_a']+7])
                m.routine('draw_sprite',hl=m.sym['glyph_alien_a'],de=(y<<8)|x,bc=7<<8)
                expected=bytearray(480)
                for dx,column in enumerate(glyph):
                    for bit in range(7):
                        if column&(1<<bit) and x+dx<m.sym['PLAY_WIDTH'] and y+bit<28:
                            yy=y+bit;expected[(yy//7)*120+x+dx]|=1<<(yy%7)
                self.assertEqual(bytes(m.cpu.memory[p:p+480]),bytes(expected),(x,y))
        m.check_memory()
    def test_held_movement_and_edges(self):
        m=InvadersMachine();m.start()
        m.set_byte('player_x',1);m.poll(0x21);m.poll(0x21)
        self.assertEqual(m.byte('player_x'),0)
        m.set_byte('player_x',m.sym['PLAYER_LIMIT']-1);m.poll(0x22);m.poll(0x22)
        self.assertEqual(m.byte('player_x'),m.sym['PLAYER_LIMIT'])
        m.check_memory()
    def test_shot_kills_one_alien_updates_score_and_explosion(self):
        m=InvadersMachine();m.start();m.remove_shields()
        m.set_byte('shot_x',m.byte('formation_x')+3)
        m.set_byte('shot_y',m.byte('formation_y')+6+5)
        m.routine('step_shot')
        self.assertEqual(m.byte('remaining'),15)
        self.assertEqual(m.cpu.memory[m.sym['aliens']+8],0)
        self.assertEqual((m.word('score'),m.byte('shot_y'),m.byte('explosion_timer')),(10,255,3))
        m.check_memory()
    def test_shot_misses_column_gap_and_does_not_hit_dead_alien(self):
        m=InvadersMachine();m.start()
        m.set_byte('probe_x',m.byte('formation_x')+8);m.set_byte('probe_y',m.byte('formation_y'))
        self.assertEqual(m.routine('find_alien')['af']>>8,0)
        m.set_byte('probe_x',m.byte('formation_x')+3)
        self.assertEqual(m.routine('find_alien')['af']>>8,1)
        m.cpu.memory[m.sym['aliens']]=0
        self.assertEqual(m.routine('find_alien')['af']>>8,0)
        m.check_memory()
    def test_both_sides_bounce_and_invade_only_when_living_rows_reach_ship(self):
        m=InvadersMachine();m.start()
        for x,direction,next_direction in ((m.sym['FORMATION_LIMIT'],1,255),(0,255,1)):
            m.set_byte('formation_x',x);m.set_byte('formation_dir',direction);m.set_byte('move_timer',1)
            old=m.byte('formation_y');m.routine('move_formation')
            self.assertEqual((m.byte('formation_x'),m.byte('formation_dir'),m.byte('formation_y')),(x,next_direction,old+1))
        m.set_byte('formation_y',12);m.set_byte('formation_x',m.sym['FORMATION_LIMIT']);m.set_byte('formation_dir',1);m.set_byte('move_timer',1)
        m.routine('move_formation');self.assertEqual(m.byte('phase'),2)
        m.routine('new_game')
        m.cpu.memory[m.sym['aliens']+8:m.sym['aliens']+16]=bytes(8)
        m.set_byte('formation_y',12);m.set_byte('formation_x',m.sym['FORMATION_LIMIT']);m.set_byte('formation_dir',1);m.set_byte('move_timer',1)
        m.routine('move_formation');self.assertEqual(m.byte('phase'),1)
        m.check_memory()
    def test_shields_erode_under_both_projectiles(self):
        m=InvadersMachine();m.start()
        m.set_byte('probe_x',11);m.set_byte('probe_y',20)
        for remaining in (2,1,0):
            self.assertEqual(m.routine('shield_collision')['af']>>8,1)
            self.assertEqual(m.byte('shields'),remaining)
        self.assertEqual(m.routine('shield_collision')['af']>>8,0)
        m.cpu.memory[m.sym['shields']]=3
        m.set_byte('shot_x',11);m.set_byte('shot_y',23);m.routine('step_shot')
        self.assertEqual((m.byte('shields'),m.byte('shot_y')),(2,255))
        p=m.sym['bombs'];m.cpu.memory[p:p+2]=bytes((11,19));m.set_byte('tick_count',0)
        m.routine('step_bombs');self.assertEqual((m.byte('shields'),m.cpu.memory[p+1]),(1,255))
        m.check_memory()
    def test_bombs_lives_protection_game_over_and_record(self):
        m=InvadersMachine();m.start();m.remove_shields();m.set_word('score',120)
        p=m.sym['bombs']
        for lives in (2,1,0):
            m.set_byte('grace',0);m.set_byte('tick_count',0)
            m.cpu.memory[p:p+2]=bytes((m.byte('player_x')+3,23))
            m.routine('step_bombs')
            self.assertEqual((m.byte('lives'),m.byte('grace')),(lives,40))
            if lives:
                m.cpu.memory[p:p+2]=bytes((m.byte('player_x')+3,23))
                m.routine('step_bombs');self.assertEqual(m.byte('lives'),lives)
        self.assertEqual((m.byte('phase'),m.word('best_score')),(2,120))
        m.routine('new_game');self.assertEqual((m.byte('lives'),m.word('score'),m.word('best_score')),(3,0,120))
        m.check_memory()
    def test_wave_clear_resets_formation_and_keeps_lives_score(self):
        m=InvadersMachine();m.start();m.set_byte('remaining',0);m.set_byte('lives',2);m.set_word('score',160)
        m.routine('world_step')
        self.assertEqual((m.byte('wave'),m.byte('remaining'),m.byte('lives'),m.word('score')),(2,16,2,160))
        m.set_byte('wave',99);m.routine('next_wave');self.assertEqual(m.byte('wave'),99)
        m.set_word('score',9998);m.routine('add_score');self.assertEqual(m.word('score'),9999)
        m.check_memory()
    def test_pause_help_auto_fire_and_restart(self):
        m=InvadersMachine();m.start();m.tap(0x39)
        frozen=bytes(m.cpu.memory[m.sym['aliens']:m.sym['aliens']+16]),m.byte('tick_count')
        for _ in range(8):m.step()
        self.assertEqual((bytes(m.cpu.memory[m.sym['aliens']:m.sym['aliens']+16]),m.byte('tick_count')),frozen)
        m.tap(0x17);self.assertEqual(m.byte('phase'),4)
        m.tap(0x17);self.assertEqual((m.byte('phase'),m.byte('paused')),(1,1))
        m.tap(0x39);m.tap(0x0c)
        self.assertEqual(m.byte('auto_fire'),1)
        shots=[]
        for _ in range(8):
            m.step();shots.append(m.byte('shot_y'))
        self.assertTrue(any(y!=255 for y in shots))
        m.tap(0x05);self.assertEqual((m.byte('wave'),m.byte('lives'),m.word('score')),(1,3,0))
        m.check_memory()
    def test_enemy_fire_and_faster_formation_as_aliens_die(self):
        m=InvadersMachine();m.start();m.routine('launch_bomb')
        self.assertNotEqual(m.cpu.memory[m.sym['bombs']+1],255)
        for n,speed in ((16,5),(7,2),(1,1)):
            m.set_byte('remaining',n);m.set_byte('move_timer',1);m.routine('move_formation')
            self.assertEqual(m.byte('move_timer'),speed)
        m.check_memory()
    def test_all_four_rows_are_playable_and_sidebar_survives_help_and_game_over(self):
        for lang in ('FR','EN'):
            m=InvadersMachine(lang);m.start()
            p=m.sym['screen_buffer']
            self.assertTrue(any(m.cpu.memory[p:p+90]))
            for row in range(4):
                edge=bytes(m.cpu.memory[p+row*120+90:p+row*120+120])
                self.assertEqual(edge,bytes((0,0,127))+bytes(27))
            for key in (0x17,0x17):m.tap(key)
            self.assertEqual(bytes(m.text[0][20:24]),f'{m.word("score"):04d}'.encode())
            self.assertEqual(m.text[2][20],ord('3'))
            m.routine('game_over');m.routine('draw_game')
            self.assertEqual(m.text[1][19],ord('V' if lang=='FR' else 'W'))
            self.assertEqual(m.text[2][20],ord('3'))
            m.check_memory()
    def test_upper_row_can_be_hit_above_the_old_hud(self):
        m=InvadersMachine();m.start();m.remove_shields()
        m.set_byte('shot_x',m.byte('formation_x')+3)
        m.set_byte('shot_y',6);m.routine('step_shot')
        self.assertEqual((m.cpu.memory[m.sym['aliens']],m.byte('remaining')),(0,15))
        m.set_byte('shot_x',0);m.set_byte('shot_y',1);m.routine('step_shot')
        self.assertEqual(m.byte('shot_y'),255)
        m.check_memory()
    def test_initial_invasion_budget_increases_despite_narrower_arena(self):
        m=InvadersMachine();m.routine('new_game')
        ticks=0
        while m.byte('phase')==1 and ticks<2000:
            m.routine('move_formation');ticks+=1
        self.assertEqual(ticks,1210)
        self.assertGreater(ticks,1.8*665)  # v0.1 geometry: 665 movement ticks
        m.check_memory()
    def test_long_attract_combat_keeps_buffers_and_stack_in_reservation(self):
        for language in ('FR','EN'):
            m=InvadersMachine(language);m.start();m.set_byte('auto_fire',1)
            for i in range(160):
                if m.byte('phase')!=1:break
                m.set_byte('grace',40)
                m.poll(0x21 if (i//35)%2 else 0x22)
            self.assertTrue(m.word('score')>0)
            m.check_memory()

if __name__=='__main__':
    parser=Parser('Verifier Pocket Invaders, IOCS simules.','Check Pocket Invaders with simulated IOCS.');args=parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(InvadersChecks))
    (HERE/'build/cpu_validation.json').write_text(json.dumps({'tests':result.testsRun,'passed':result.wasSuccessful(),'physical_hardware_tested':False},indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
