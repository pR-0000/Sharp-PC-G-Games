"""FR/EN: native 108x48 arena, pixel clipping, collisions and matrix controls."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from check_invaders import InvadersMachine
from cli_i18n import Parser


class InvadersG850(G850Machine):
    def __init__(self,language='FR'):super().__init__('invaders_g850_'+language,HERE/'build/g850')
    remove_shields=InvadersMachine.remove_shields


class G850Checks(unittest.TestCase):
    def test_both_languages_and_all_six_pages(self):
        for lang in ('FR','EN'):
            m=InvadersG850(lang);m.start()
            self.assertEqual(bytes(m.text[0][20:24]),b'0000')
            self.assertEqual([r for r,_,d in m.pattern_calls if len(d)==144][-6:],list(range(6)))
            self.assertTrue(any(m.pixels()[5*144:5*144+108]))
            for row in range(6):self.assertEqual(m.pixels()[row*144+110],255)
            m.tap(2);self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,m.stack+2,0x1234,0x5678))
            m.check_memory()

    def test_all_pixel_shifts_and_clipped_edges(self):
        m=InvadersG850();m.start();p=m.sym['screen_buffer']
        glyph=bytes(m.cpu.memory[m.sym['glyph_alien_a']:m.sym['glyph_alien_a']+9])
        for x in (0,53,100,107,108,143,255):
            for y in range(49):
                m.cpu.memory[p:p+864]=bytes(864)
                m.routine('draw_sprite',hl=m.sym['glyph_alien_a'],de=y*256+x,bc=9<<8)
                expected=bytearray(864)
                for dx,col in enumerate(glyph):
                    for bit in range(7):
                        if col&(1<<bit) and x+dx<108 and y+bit<48:
                            yy=y+bit;expected[yy//8*144+x+dx]|=1<<(yy%8)
                self.assertEqual(m.pixels(),expected,(x,y))
        m.check_memory()

    def test_simultaneous_direction_and_fire_and_photo_freeze(self):
        m=InvadersG850();m.start();m.inputs.clear();m.remove_shields()
        x=m.byte('player_x');m.poll((0x22,0x1E))
        self.assertEqual(m.byte('player_x'),x+1);self.assertNotEqual(m.byte('shot_y'),255)
        self.assertTrue({2,8,16}<=set(m.inputs));self.assertEqual(m.outputs[-2:],[(0x11,0),(0x12,0)])
        m.set_byte('player_x',1);m.poll(0x21);m.poll(0x21);self.assertEqual(m.byte('player_x'),0)
        m.tap(0x1D);m.poll(0);state=(m.pixels(),m.byte('tick_count'),m.byte('remaining'))
        for _ in range(20):m.poll((0x22,0x1E))
        self.assertEqual((m.pixels(),m.byte('tick_count'),m.byte('remaining')),state)
        m.tap(0x1D);self.assertEqual(m.byte('photo_frozen'),0);m.check_memory()

    def test_native_formation_collision_and_bomb_origins(self):
        m=InvadersG850();m.start();m.remove_shields()
        for row in range(2):
            for col in range(8):
                m.set_byte('probe_x',m.byte('formation_x')+col*12+4)
                m.set_byte('probe_y',m.byte('formation_y')+row*9+3)
                result=m.routine('find_alien')
                self.assertEqual(result['hl'],m.sym['aliens']+row*8+col);self.assertEqual(result['af']>>8,1)
                m.set_byte('probe_x',m.byte('formation_x')+col*12+10)
                self.assertEqual(m.routine('find_alien')['af']>>8,0)
        m.routine('launch_bomb');x,y=m.cpu.memory[m.sym['bombs']:m.sym['bombs']+2]
        self.assertEqual((x-m.byte('formation_x')-4)%12,0);self.assertEqual(y,m.byte('formation_y')+9+7)
        m.set_byte('shot_x',m.byte('formation_x')+4);m.set_byte('shot_y',m.byte('formation_y')+9+7)
        m.routine('step_shot');self.assertEqual((m.byte('remaining'),m.word('score')),(15,10));m.check_memory()

    def test_shields_and_bombs_use_the_native_height(self):
        m=InvadersG850();m.start();m.set_byte('probe_x',13);m.set_byte('probe_y',35)
        for left in (2,1,0):
            self.assertEqual(m.routine('shield_collision')['af']>>8,1);self.assertEqual(m.byte('shields'),left)
        m.remove_shields();m.set_byte('grace',0);m.set_byte('tick_count',0)
        p=m.sym['bombs'];m.cpu.memory[p:p+2]=bytes((m.byte('player_x')+4,42))
        m.routine('step_bombs');self.assertEqual(m.byte('lives'),2)
        m.set_byte('grace',0);m.cpu.memory[p:p+2]=bytes((m.byte('player_x')+4,24))
        m.routine('step_bombs');self.assertEqual(m.byte('lives'),2)
        self.assertEqual(m.cpu.memory[p+1],25);m.check_memory()

    def test_wave_reset_and_long_combat_preserve_user_memory(self):
        for lang in ('FR','EN'):
            m=InvadersG850(lang);m.start();m.set_byte('auto_fire',1)
            for i in range(220):
                m.set_byte('grace',40);m.poll(0x21 if (i//30)%2 else 0x22)
            self.assertGreater(m.word('score'),0)
            score=m.word('score');m.set_byte('remaining',0);m.poll(0)
            self.assertEqual((m.byte('wave'),m.byte('remaining'),m.word('score')),(2,16,score));m.check_memory()

    def test_invasion_budget_and_only_living_rows_reach_the_ship(self):
        m=InvadersG850();m.routine('new_game');ticks=0
        while m.byte('phase')==1 and ticks<3000:m.routine('move_formation');ticks+=1
        self.assertEqual(ticks,1885)
        m.routine('new_game');m.cpu.memory[m.sym['aliens']+8:m.sym['aliens']+16]=bytes(8)
        for y,phase in ((26,1),(35,2)):
            m.set_byte('formation_x',m.sym['FORMATION_LIMIT']);m.set_byte('formation_dir',1)
            m.set_byte('formation_y',y);m.set_byte('move_timer',1);m.routine('move_formation')
            self.assertEqual(m.byte('phase'),phase)
        m.check_memory()


if __name__=='__main__':
    parser=Parser('Verifier Invaders G850.','Check Invaders G850.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(G850Checks))
    raise SystemExit(not result.wasSuccessful())
