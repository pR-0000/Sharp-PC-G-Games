"""FR/EN: common Runner gameplay plus native 140x40 tile/pixel checks."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from check_runner import RunnerMachine,RunnerChecks
from cli_i18n import Parser
from bitmap import read_bmp


class RunnerG850(G850Machine):
    def __init__(self,language='FR'):super().__init__('runner_g850_'+language,HERE/'build/g850')
    terrain=RunnerMachine.terrain
    tile=RunnerMachine.tile
    guard=RunnerMachine.guard
    arena=RunnerMachine.arena
    hole=RunnerMachine.hole


class G850Checks(unittest.TestCase):
    machine=RunnerG850

    def test_bilingual_title_hud_and_return(self):
        for lang in ('FR','EN'):
            m=RunnerG850(lang);m.start()
            self.assertEqual(bytes(m.text[0][:4]),b'0000')
            self.assertEqual(m.text[0][8],ord('3'));self.assertEqual(m.text[0][13],ord('8'))
            self.assertEqual([r for r,_,d in m.pattern_calls if len(d)==144][-6:],[1,2,3,4,5,0])
            m.tap(2);self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,m.stack+2,0x1234,0x5678))
            m.check_memory()

    def test_every_rendered_pixel_and_camera_position_against_the_editable_bmp(self):
        m=RunnerG850();m.start();_,_,art=read_bmp(HERE/'targets/g850/tiles.bmp')
        for row in range(12):
            m.set_byte('player_pos',row*20+10);m.routine('draw_game')
            camera=max(0,min(7,row-2));self.assertEqual(m.byte('camera_y'),camera)
            expected=bytearray(864)
            def stamp(pos,tile,overlay=False):
                x,y=pos%20,pos//20-camera
                if not 0<=y<5:return
                for dx in range(7):
                    col=sum((art[(tile*8+dy)*7+dx]==(0,0,0))<<dy for dy in range(8))
                    p=(y+1)*144+2+x*7+dx
                    expected[p]=(expected[p]|col) if overlay else col
            for pos,tile in enumerate(m.terrain()):stamp(pos,0 if tile==7 else tile)
            for i in range(8):
                if m.byte('gold_flags')&(1<<i):stamp(m.cpu.memory[m.sym['gold_positions']+i],5,True)
            for i in range(3):
                pos,trap,_=m.guard(i);stamp(pos,9 if trap else 8)
            pos=m.byte('player_pos');stamp(pos,11 if m.terrain()[pos]==4 else 6+m.byte('player_frame'))
            self.assertEqual(m.pixels(),expected,row);m.check_memory()

    def test_photo_freeze_keeps_the_frame_clean(self):
        m=RunnerG850();m.start();m.tap(0x0C);m.poll(0)
        before=(m.pixels(),m.byte('player_pos'),[m.guard(i) for i in range(3)])
        for _ in range(20):m.poll(0x22)
        self.assertEqual((m.pixels(),m.byte('player_pos'),[m.guard(i) for i in range(3)]),before)
        terrain=m.terrain();m.tap(0x11);m.tap(0x12)
        self.assertEqual(m.terrain(),terrain)
        m.tap(0x0C);self.assertEqual(m.byte('photo_frozen'),0);m.check_memory()


for name in unittest.defaultTestLoader.getTestCaseNames(RunnerChecks):
    if name not in ('test_camera_clipping_and_native_score','test_language_title_and_return'):
        setattr(G850Checks,name,getattr(RunnerChecks,name))


if __name__=='__main__':
    parser=Parser('Verifier Runner G850.','Check Runner G850.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(G850Checks))
    raise SystemExit(not result.wasSuccessful())
