"""FR/EN: actual 32 KiB G80X games, seven-bit LCD and independent pixel checks."""
from pathlib import Path
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'games/pocket-vector'),str(ROOT/'games/pocket-clash'),str(ROOT/'tools'),str(ROOT/'tests')]
from check_vector import VectorMachine
from check_clash import ClashG850
from bitmap import read_bmp
from cli_i18n import Parser


class Vector80X(VectorMachine):
    def __init__(self,language='FR'):super().__init__(language,'g80x-32k')


class Clash80X(ClashG850):
    width=120
    rows=4
    cell_width=5
    pixel_mask=127
    def __init__(self,language='FR'):super().__init__(language,'g80x-32k')
    def pixels(self):
        p=self.sym['frame_buffer'];return bytes(self.cpu.memory[p:p+480])


class PortsChecks(unittest.TestCase):
    def test_vector_floor_all_headings_matches_independent_2x2_projection(self):
        from assets import reference
        ref=reference();m=Vector80X();m.initialise()
        base=m.sym['texture_map'];texture=bytes(m.cpu.memory[base:base+2048])
        for angle in range(64):
            m.byte('heading',angle);m.call('prepare_camera');m.call('prepare_rows');m.call('floor_render')
            pose=(m.word('camera_x')/256,m.word('camera_y')/256,
                  ((m.byte('camera_cos')+128)%256-128)/127,
                  ((m.byte('camera_sin')+128)%256-128)/127)
            # Asset tables use true sin/cos rounded after quarter-turn rotation.
            import math
            pose=(pose[0],pose[1],math.cos(angle*math.pi/32),math.sin(angle*math.pi/32))
            rows=ref.rows_for(pose,2,2,bottom=48)
            self.assertEqual(m.native_frame(),bytes(ref.reference_floor(texture,rows,2,2)),angle)
        m.check_memory()

    def test_vector_sampler_repackages_all_21_scanlines_without_missing_cell_bits(self):
        m=Vector80X();m.initialise();base=m.sym['frame'];target=m.sym['lcd_frame']
        source=bytes(((i*37)^(i//7))&255 for i in range(864))
        m.cpu.memory[base:base+864]=source;m.cpu.memory[target:target+480]=bytes(480)
        m.call('g80x_sample_view');expected=bytearray(480)
        for y in range(21):
            sy=(2*y+1)*40//42
            for x in range(120):
                sx=(2*x+1)*144//240
                if source[sy//8*144+sx]&(1<<(sy%8)):
                    expected[(1+y//7)*120+x]|=1<<(y%7)
        self.assertEqual(bytes(m.cpu.memory[target:target+480]),expected)
        m.call('g80x_upload');self.assertEqual(m.display,expected);m.check_memory()

    def test_vector_native_menus_and_race_phases_both_languages(self):
        for language in ('FR','EN'):
            m=Vector80X(language);m.initialise()
            for phase in (0,5,3,4,6,7,8,9,1,2):
                m.byte('phase',phase);m.byte('pause_previous',1);m.call('show_frame')
                self.assertTrue(any(m.display));self.assertEqual(len(m.display),480)
                self.assertTrue(all(v<128 for v in m.display))
            m.check_memory()

    def test_vector_three_course_auto_cup_and_confirm_release(self):
        for language in ('FR','EN'):
            m=Vector80X(language);m.initialise();m.call('start_session',a=0)
            for race in range(3):
                m.byte('phase',1);m.byte('demo_mode',1)
                for tick in range(2500):
                    if m.byte('phase')!=1:break
                    m.call('race_tick')
                self.assertIn(m.byte('phase'),(3,4),(language,race,tick))
                m.call('show_frame');m.call('advance_result')
            self.assertEqual(m.byte('phase'),6);m.call('show_frame');m.check_memory()

    def test_vector_controls_simultaneous_and_preserve_interrupt_state(self):
        m=Vector80X();m.initialise()
        for enabled in (0,1):
            m.cpu._Z80State__iff1[0]=enabled;m.cpu._Z80State__iff2[0]=enabled
            m.raw_keys={0x22,0x20,0x12};m.call('poll_keyboard')
            self.assertEqual(m.byte('keys')&38,38)
            self.assertEqual(m.cpu.iff1,enabled)
        m.check_memory()

    def test_vector_full_size_player_matches_shared_editable_sprites(self):
        from graphics import read_sprite,FRAME_SPECS,DIRECTIONS
        m=Vector80X();m.initialise();base=m.sym['lcd_frame']
        cases=[(0,0,0),(0,1,1),(0,2,7)]+[(spin,0,((8-spin)*2)&7) for spin in range(8,0,-1)]
        for spin,controls,direction in cases:
            m.byte('spin_frames',spin);m.byte('control_keys',controls);m.byte('phase',1)
            m.cpu.memory[base:base+480]=bytes([85])*480
            m.call('g80x_player')
            name='player_'+DIRECTIONS[direction]
            record=read_sprite(ROOT/'games/pocket-vector/graphics'/(name+'.bmp'),FRAME_SPECS[name])
            w,h=record[:2];expected=bytearray([85])*480
            for y in range(h):
                for x in range(w):
                    v=record[2+y*w+x]
                    if not v:continue
                    index=(17+y)//7*120+48+x;bit=1<<((17+y)%7)
                    if v==1:expected[index]&=127^bit
                    else:expected[index]|=bit
            self.assertEqual(bytes(m.cpu.memory[base:base+480]),expected,(spin,controls,direction))
        m.check_memory()

    def test_clash_native_hud_title_all_fighters_and_four_row_standings(self):
        for language in ('FR','EN'):
            m=Clash80X(language);self.assertIn(b'POCKET CLASH',m.text[0])
            for selected in range(4):
                m.set_byte('selected',selected);m.routine('title_screen')
                m.routine('start_cup');m.set_byte('countdown',0)
                self.assertEqual(m.byte('zoom_n'),16)
                m.routine('finish_round')
                self.assertTrue(all(len(row)==24 for row in m.text))
            m.check_memory()

    def test_clash_repacking_preserves_each_source_view_pixel(self):
        m=Clash80X();m.live();start=m.sym['frame_buffer']
        source=bytes((i*29+i//17)&255 for i in range(480))
        # HUD already uses seven useful bits; scene is internally 8-bit packed.
        source=bytes(v&127 if i<120 else v for i,v in enumerate(source))
        m.cpu.memory[start:start+480]=source;m.routine('upload_frame')
        for y in range(21):
            for x in range(120):
                self.assertEqual(bool(m.screen[1+y//7][x]&(1<<(y%7))),
                                 bool(source[(1+y//8)*120+x]&(1<<(y%8))),(x,y))
        m.check_memory()

    def test_clash_scaler_clips_all_thirteen_sizes_and_mirrors(self):
        m=Clash80X();m.live();frame=m.sym['frame_buffer']
        _,_,pixels=read_bmp(ROOT/'games/pocket-clash/sprites.bmp')
        for sprite in (0,6,12,18,24):
            source={(x,y) for y in range(16) for x in range(16) if pixels[(sprite*16+y)*16+x]==(0,0,0)}
            for n in range(4,17):
                ink={(x,y) for y in range(n) for x in range(n) if ((2*x+1)*8//n,(2*y+1)*8//n) in source}
                mask=ink|{(x+dx,y+dy) for x,y in ink for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))}
                m.set_byte('zoom_n',n)
                for mirror in (0,1):
                    m.set_byte('sprite_mirror',mirror)
                    for x,y in ((-4,-4),(0,0),(3,7),(114,17),(120,21)):
                        m.cpu.memory[frame:frame+480]=bytes([165])*480
                        m.set_word('draw_x',x&65535);m.set_word('draw_y',y&65535)
                        m.routine('draw_sprite',a=sprite);expected=bytearray([165])*480
                        for py in range(n):
                            for px in range(n):
                                sx=n-1-px if mirror else px
                                if not (0<=x+px<120 and 0<=y+py<21):continue
                                index=(y+py+8)//8*120+x+px;bit=1<<((y+py)%8)
                                if (sx,py) in mask:expected[index]&=255^bit
                                if (sx,py) in ink:expected[index]|=bit
                        # Bits below the 21-pixel view are discarded on upload.
                        actual=m.pixels()
                        for i,(a,b) in enumerate(zip(actual,expected)):
                            valid=31 if i>=360 else 255
                            self.assertEqual(a&valid,b&valid,(sprite,n,mirror,x,y,i))
        m.check_memory()

    def test_clash_cup_completes_all_battles_and_camera_stays_inside_limits(self):
        for language in ('FR','EN'):
            m=Clash80X(language);m.tap(0x0b)
            for index in range(3):
                for frame in range(2600):
                    if m.byte('phase')!=1:break
                    m.routine('world_step');self.assertTrue(4<=m.byte('zoom_n')<=16)
                self.assertEqual(m.byte('phase'),3 if index==2 else 2)
                m.routine('standings_screen')
                if index<2:m.tap(0x28)
            m.check_memory()


if __name__=='__main__':
    Parser('Verifier les portages G80X 32 Kio.','Check the 32 KiB G80X ports.').parse_args()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PortsChecks)).wasSuccessful())
