"""FR/EN: shared races, native 144x40 tilemapper, clipping and settled keys."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from check_rally import RallyMachine,RallyChecks,track,PATTERNS
from cli_i18n import Parser


class RallyG850(G850Machine):
    def __init__(self,language='FR'):super().__init__('rally_g850_'+language,HERE/'build/g850')
    car=RallyMachine.car
    position=RallyMachine.position
    frame=RallyMachine.frame


class G850Checks(unittest.TestCase):
    machine_class=RallyG850
    machine=RallyChecks.machine

    def test_bilingual_hud_six_pages_and_monitor_return(self):
        for language in ('FR','EN'):
            m=self.machine(lang=language)
            self.assertEqual(bytes(m.text[0][:4]),b'T1/3' if language=='FR' else b'L1/3')
            self.assertEqual(bytes(m.text[0][12:16]),b'P3/3')
            self.assertEqual([r for r,_,d in m.pattern_calls if len(d)==144][-6:],[1,2,3,4,5,0])
            m.tap(0x51);self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,m.stack+2,0x1234,0x5678))
            m.check_memory()

    def test_every_subtile_scroll_phase_matches_independent_pixels(self):
        for index in range(2):
            m=self.machine(index);cells=track(index)
            for cx,cy in [(x,y) for x in range(4) for y in range(4)]+[(45,51),(48,88),(47,87)]:
                m.set_byte('camera_x',cx);m.set_byte('camera_y',cy);m.routine('render_terrain')
                expected=bytearray(864)
                for y in range(40):
                    for x in range(144):
                        wx,wy=cx+x,cy+y;tile=cells[(wy//4)*48+wx//4]
                        if PATTERNS[tile][wx%4]>>(wy%4)&1:expected[(y//8+1)*144+x]|=1<<(y%8)
                self.assertEqual(m.pixels(),expected,(index,cx,cy))
            m.check_memory()

    def test_sprite_clipping_on_all_five_pages_preserves_hud_and_ram(self):
        m=self.machine();p=m.sym['frame_buffer'];source=m.sym['car_frames']
        glyph=[int.from_bytes(m.cpu.memory[source+i*2:source+i*2+2],'little') for i in range(7)]
        for x in (-8,-3,0,71,138,143,144):
            for y in range(-10,42):
                m.cpu.memory[p:p+864]=bytes(864);m.set_word('draw_x',x&65535);m.set_word('draw_y',y&65535)
                m.routine('draw_sprite',hl=source,bc=7<<8)
                expected=bytearray(864)
                for dx,col in enumerate(glyph):
                    for dy in range(7):
                        xx,yy=x+dx,y+dy
                        if col&(1<<dy) and 0<=xx<144 and 0<=yy<40:expected[(yy//8+1)*144+xx]|=1<<(yy%8)
                self.assertEqual(m.pixels(),expected,(x,y))
        m.check_memory()

    def test_camera_easing_respects_larger_viewport_and_world_edges(self):
        m=self.machine()
        for x,y,angle in ((12,12,8),(180,116,0),(96,64,4),(96,64,12)):
            m.position(0,x,y,angle=angle)
            for _ in range(60):
                before=m.byte('camera_x'),m.byte('camera_y');m.routine('update_camera')
                self.assertLessEqual(abs(m.byte('camera_x')-before[0]),2)
                self.assertLessEqual(abs(m.byte('camera_y')-before[1]),2)
                self.assertTrue(0<=m.byte('camera_x')<=48 and 0<=m.byte('camera_y')<=88)
        m.check_memory()

    def test_photo_freeze_preserves_the_entire_race_and_can_resume(self):
        m=self.machine();m.tap(0x39);self.assertEqual(m.byte('paused'),1)
        m.tap(0x1D);m.poll(0)
        self.assertEqual((m.byte('paused'),m.byte('photo_frozen')),(0,1))
        before=(m.pixels(),m.word('race_ticks'),[m.car(i) for i in range(3)])
        for _ in range(20):m.poll((0x22,0x1E))
        self.assertEqual((m.pixels(),m.word('race_ticks'),[m.car(i) for i in range(3)]),before)
        m.tap(0x1D);self.assertEqual(m.byte('photo_frozen'),0)
        m.tap(0x1D);m.tap(0x05)
        self.assertEqual((m.byte('photo_frozen'),m.byte('paused')),(0,0));m.check_memory()


for name in unittest.defaultTestLoader.getTestCaseNames(RallyChecks):
    if name not in ('test_languages_title_and_return','test_tilemapper_against_independent_pixels','test_camera_easing_bounds'):
        setattr(G850Checks,name,getattr(RallyChecks,name))


if __name__=='__main__':
    parser=Parser('Verifier Pocket Rally G850.','Check Pocket Rally G850.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(G850Checks))
    raise SystemExit(not result.wasSuccessful())
