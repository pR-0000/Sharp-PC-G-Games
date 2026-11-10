"""FR/EN: gameplay scenarios for the distributed Star Lane Z80 programs."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_programs import Machine,RETURN
from cli_i18n import Parser

class StarMachine(Machine):
    def __init__(self,language='FR'):
        self.language=language
        super().__init__('star_lane_'+language,HERE/'build/g80x')

class StarChecks(unittest.TestCase):
    machine_class=StarMachine
    def game(self,language='FR'):
        m=self.machine_class(language);m.start();return m
    def test_manual_fire_destroys_rocks_and_two_hits_destroy_a_pirate(self):
        for language in ('FR','EN'):
            m=self.game(language);lane=m.byte('player_lane')
            m.set_tile(lane,5,1);m.tap(0x1e);m.next_world()
            self.assertEqual((m.word('score'),m.byte('shot_x')),(11,255))
            m.set_tile(lane,5,3);m.tap(0x1e);m.next_world()
            self.assertEqual(m.cpu.memory[m.sym['tiles']+lane*24+4],4)
            m.tap(0x1e);m.next_world();self.assertEqual(m.word('score'),63)
            m.check_memory()
    def test_autofire_keeps_running_while_changing_lane(self):
        m=self.game();m.tap(0x0c);self.assertEqual(m.byte('autofire'),1)
        m.next_world();self.assertLess(m.byte('shot_x'),24)
        m.tap(0x20);self.assertEqual(m.byte('autofire'),1)
        m.tap(0x0c);self.assertEqual(m.byte('autofire'),0);m.check_memory()
    def test_shield_absorbs_contacts_and_energy_cells_recharge_it(self):
        m=self.game();lane=m.byte('player_lane');m.tap(0x12)
        self.assertEqual((m.byte('charges'),m.byte('shield_time')),(2,6))
        m.set_tile(lane,3,1);m.next_world()
        self.assertEqual((m.byte('lives'),m.byte('invulnerable')),(3,0))
        m.set_tile(lane,3,6);m.next_world();self.assertEqual(m.byte('charges'),3)
        m.set_byte('shield_time',0);m.set_byte('charges',0);m.tap(0x12)
        self.assertEqual(m.byte('shield_time'),0);m.check_memory()
    def test_star_combo_caps_and_a_hit_resets_it(self):
        m=self.game();lane=m.byte('player_lane')
        for value in (26,77,153,254,355):
            m.set_tile(lane,3,2);m.next_world();self.assertEqual(m.word('score'),value)
        self.assertEqual(m.byte('combo'),4)
        m.set_tile(lane,3,1);m.next_world();self.assertEqual(m.byte('combo'),1)
        m.check_memory()
    def test_pirates_fire_and_difficulty_advances_with_safe_wave_gaps(self):
        m=self.game();m.set_byte('sector_steps',7);m.set_tile(0,12,3);m.next_world()
        self.assertEqual(m.cpu.memory[m.sym['tiles']+10],5)
        initial=m.byte('step_delay')
        for _ in range(600):
            m.set_byte('invulnerable',200);m.next_world()
            count=m.sym['LANES']*24
            tiles=bytes(m.cpu.memory[m.sym['tiles']:m.sym['tiles']+count])
            self.assertTrue(all(0<=value<=6 for value in tiles))
            self.assertTrue(any(value in (0,2,6) for value in tiles[23::24]))
        self.assertEqual(m.byte('sector'),9);self.assertLess(m.byte('step_delay'),initial)
        self.assertEqual(m.byte('phase'),1);m.check_memory()
    def test_photo_freezes_cleanly_pause_and_restart_release_it(self):
        m=self.game();m.tap(0x1d);score=m.word('score')
        for _ in range(200):m.poll()
        self.assertEqual(m.word('score'),score);self.assertEqual(m.byte('photo'),1)
        self.assertNotIn(b'PAUSE',bytes(m.text[2]))
        m.tap(0x1d);m.next_world();self.assertGreater(m.word('score'),score)
        m.tap(0x39);self.assertEqual(m.byte('paused'),1)
        m.tap(0x05);self.assertEqual((m.byte('paused'),m.byte('photo'),m.byte('combo')),(0,0,1))
        m.tap(0x02);self.assertEqual((m.cpu.pc,m.cpu.sp),(RETURN,m.stack+2));m.check_memory()
    def test_all_lanes_native_bands_and_caller_ram_are_safe(self):
        for language in ('FR','EN'):
            m=self.game(language)
            for _ in range(8):m.tap(0x1f)
            self.assertEqual(m.byte('player_lane'),m.sym['LANES']-1)
            self.assertTrue(any(row==m.rows-1 and len(data)==m.width for row,col,data in m.pattern_calls))
            for _ in range(8):m.tap(0x20)
            self.assertEqual(m.byte('player_lane'),0);m.check_memory()

if __name__=='__main__':
    Parser('Verifier Star Lane G80X.','Check Star Lane G80X.').parse_args()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(StarChecks)).wasSuccessful())
