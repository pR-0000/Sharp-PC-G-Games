"""FR/EN: G850 game, pixel clipping, simultaneous input and photo freeze."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from cli_i18n import Parser


class JumperG850(G850Machine):
    def __init__(self,language='FR'):
        super().__init__('jumper_g850_'+language,HERE/'build/g850')
    def position(self,x,y):
        self.set_word('player_x',x*16);self.set_word('player_y',y*16)
        self.set_byte('velocity_x',0);self.set_byte('velocity_y',0)
    def arena(self):
        p=self.sym['world'];self.cpu.memory[p:p+768]=bytes(672)+bytes([1])*96
        for i in range(4):self.cpu.memory[self.sym['enemies']+9*i+8]=0
        self.position(32,44);self.set_byte('grounded',1)


class G850Checks(unittest.TestCase):
    def test_both_languages_native_hud_six_pages_and_safe_return(self):
        for language in ('FR','EN'):
            m=JumperG850(language);self.assertIn(b'POCKET JUMPER',m.text[0]);m.start()
            self.assertEqual(bytes(m.text[0][:4]),b'0010')
            self.assertEqual(bytes(m.text[0][16:19]),b'N01' if language=='FR' else b'L01')
            self.assertEqual([row for row,_,_ in m.pattern_calls[-8:-2]],list(range(6)))
            m.tap(0x51);self.assertEqual(m.cpu.pc,RETURN);m.check_memory()
    def test_eight_bit_blitter_matches_independent_pixels_and_clips_all_edges(self):
        m=JumperG850();m.start();p=m.sym['frame_buffer'];source=m.sym['hero_a']
        columns=[int.from_bytes(m.cpu.memory[source+2*i:source+2*i+2],'little') for i in range(12)]
        for x in (-12,-11,-1,0,1,121,132,138,143,144,200):
            for y in (-12,-11,-1,0,1,6,7,8,15,16,27,31,32,38,39,40):
                m.cpu.memory[p:p+864]=bytes(864)
                m.set_word('draw_x',x&65535);m.set_word('draw_y',y&65535)
                m.routine('draw_sprite',hl=source,b=12)
                expected=bytearray(864)
                for col,bits in enumerate(columns):
                    for row in range(12):
                        if bits>>row&1 and 0<=x+col<144 and 0<=y+row<40:
                            px,py=x+col,y+row+8
                            expected[py//8*144+px]|=1<<(py%8)
                self.assertEqual(m.pixels(),expected,(x,y))
        m.check_memory()
    def test_simultaneous_movement_jump_and_photo_freeze(self):
        m=JumperG850();m.start();m.arena();old=m.word('player_x')
        m.poll((0x22,0x1E))
        self.assertGreater(m.word('player_x'),old);self.assertLess(m.word('player_y'),44*16)
        self.assertEqual(m.byte('input_buttons'),6)
        self.assertTrue(all(row in (4,8,16) for row in m.inputs))
        m.tap(0x0C);self.assertEqual(m.byte('paused'),1)
        state=(m.word('player_x'),m.word('player_y'),m.byte('frame_count'),m.pixels())
        for _ in range(16):m.poll(0x22)
        self.assertEqual(state,(m.word('player_x'),m.word('player_y'),m.byte('frame_count'),m.pixels()))
        m.tap(0x0C);self.assertEqual(m.byte('paused'),0);m.check_memory()
    def test_taller_level_camera_and_ground_collision(self):
        m=JumperG850();m.start();m.arena();m.routine('draw_game')
        self.assertEqual(m.byte('camera_y'),24)
        for _ in range(28):m.poll(0x12 if _==0 else 0x22)
        self.assertEqual(m.byte('grounded'),1);self.assertEqual(m.word('player_y'),44*16)
        for x in (0,50,500,756):
            m.position(x,44);m.routine('draw_game')
            self.assertTrue(0<=m.word('camera_x')<=624)
            self.assertTrue(0<=m.byte('camera_y')<=24)
        m.check_memory()
    def test_demo_advances_without_user_input_and_manual_control_can_resume(self):
        m=JumperG850();m.tap(0x0B)
        self.assertEqual(m.byte('demo_mode'),1)
        for _ in range(75):m.poll()
        self.assertGreater(m.word('player_x'),100*16)
        self.assertGreater(m.byte('lives'),0)
        m.tap(0x0B);self.assertEqual(m.byte('demo_mode'),0);m.check_memory()
    def test_all_strings_fit_native_cells(self):
        for language in ('FR','EN'):
            m=JumperG850(language)
            for name in ('subtitle','photo_text','demo_text','help_1','help_2','help_3','help_4','restart_text'):
                p=m.sym[name];self.assertLessEqual(bytes(m.cpu.memory[p:p+64]).index(0),24,(language,name))
    def test_demo_completes_the_taller_level_with_three_lives_in_both_languages(self):
        for language in ('FR','EN'):
            m=JumperG850(language);m.tap(0x0B)
            for _ in range(600):
                m.poll()
                if m.byte('phase')!=1:break
            self.assertEqual(m.byte('phase'),3)
            self.assertEqual(m.byte('lives'),3);m.check_memory()


if __name__=='__main__':
    parser=Parser('Verifier Pocket Jumper G850.','Check Pocket Jumper G850.');parser.parse_args()
    unittest.main(argv=[sys.argv[0]],verbosity=2)
