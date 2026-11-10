"""FR/EN: G850 viewport, DDA, projection, clipping and complete campaigns."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from g850_machine import G850Machine,RETURN
from check_depths2 import Depths2Machine,reference,play_campaign
from cli_i18n import Parser


class DepthsG850(G850Machine):
    def __init__(self,language='FR'):
        self.heart_states=[]
        super().__init__('depths2_g850_'+language,HERE/'build/g850')
    tile=Depths2Machine.tile
    actor=Depths2Machine.actor
    arena=Depths2Machine.arena
    def rom_return(self,key=None):
        if self.cpu.d==0 and self.cpu.e==0:
            if self.cpu.pc==0xBE62 and self.cpu.a==32:self.heart_states.append(False)
            if self.cpu.pc==0xBFD0 and self.cpu.b==5:self.heart_states.append(True)
        super().rom_return(key)


class G850Checks(unittest.TestCase):
    def test_native_hud_is_above_the_view_and_all_six_pages_are_uploaded(self):
        for language in ('FR','EN'):
            m=DepthsG850(language);m.start()
            self.assertEqual(bytes(m.text[0][1:4]),b'100')
            self.assertEqual([row for row,_,data in m.pattern_calls if len(data)==144][-6:],list(range(6)))
            self.assertTrue(any(m.pixels()[144:]));m.tap(0x51)
            self.assertEqual(m.cpu.pc,RETURN);m.check_memory()
    def test_all_48_rendered_ray_distances_match_independent_dda(self):
        m=DepthsG850();m.start();m.arena()
        for angle in (0,32,64,96,128,160,192,224):
            m.set_byte('angle',angle);m.routine('render')
            p=m.sym['depth_buffer']
            for index in range(48):
                offset=m.cpu.memory[m.sym['ray_offsets']+index]
                ray=(angle+offset)&255
                expected=reference(m,ray)[3]
                cosine=m.cpu.memory[m.sym['ray_cosines']+index]
                actual=int.from_bytes(m.cpu.memory[p+index*2:p+index*2+2],'little')
                self.assertEqual(actual,max(1,expected*cosine//256),(angle,index))
        m.check_memory()
    def test_projection_has_72_pixel_focal_length_and_40_pixel_limit(self):
        m=DepthsG850();m.start()
        for distance in (0,1,255,256,500,768,2048,32767):
            result=m.routine('project_height',hl=distance)
            self.assertEqual(result['af']>>8,min(40,18432//distance) if distance else 40)
        m.check_memory()
    def test_pixel_plot_and_erase_use_eight_bits_and_keep_the_hud_clear(self):
        m=DepthsG850();m.start();p=m.sym['frame_buffer']
        m.cpu.memory[p:p+864]=bytes(864);expected=bytearray(864)
        for x in (0,1,71,72,120,143,144,255):
            for y in (0,1,6,7,8,15,23,31,38,39,40,255):
                m.routine('plot',bc=(y<<8)|x)
                if x<144 and y<40:expected[(y//8+1)*144+x]|=1<<(y%8)
                self.assertEqual(m.pixels(),expected,(x,y))
        for x in range(144):
            for y in range(40):
                if expected[(y//8+1)*144+x]&(1<<(y%8)):
                    m.routine('erase',bc=(y<<8)|x)
        self.assertFalse(any(m.pixels()));m.check_memory()
    def test_billboards_near_edges_remain_inside_user_ram(self):
        m=DepthsG850();m.start();m.arena();m.actor(0,8,7,3)
        for angle in range(0,256,8):
            m.set_byte('angle',angle);m.routine('render')
        m.check_memory()
    def test_damage_blinks_the_native_heart_in_its_new_location(self):
        m=DepthsG850();m.start();m.heart_states.clear()
        m.routine('hurt_flash')
        self.assertEqual(m.heart_states,[False,True,False,True]);m.check_memory()
    def test_entire_campaign_is_playable_in_both_languages(self):
        for language in ('FR','EN'):
            m=DepthsG850(language);result=play_campaign(m)
            self.assertTrue(result['all_monsters_defeated'])
            self.assertEqual(m.byte('phase'),4);m.check_memory()


if __name__=='__main__':
    parser=Parser('Verifier Pocket Depths 2 G850.','Check Pocket Depths 2 G850.');parser.parse_args()
    unittest.main(argv=[sys.argv[0]],verbosity=2)
