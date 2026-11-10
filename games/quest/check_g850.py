"""FR/EN: shared Quest gameplay scenarios and native G850 pixel/UI checks."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'));sys.path.insert(0,str(ROOT/'tools'))
from check_quest import QuestMachine,QuestChecks,KEYS,RETURN
from g850_machine import G850Machine
from cli_i18n import Parser
from bitmap import read_bmp


class QuestG850(QuestMachine):
    width=144;rows=6;cell_width=6;pixel_mask=255
    stack=0x76C0;stack_bottom=0x7600
    program_prefix='quest_g850_';build_dir=HERE/'build/g850'
    routine=G850Machine.routine
    pixels=G850Machine.pixels


class G850Checks(unittest.TestCase):
    machine=QuestG850

    def test_native_title_map_hud_and_monitor_return(self):
        for lang in ('FR','EN'):
            m=QuestG850(lang);self.assertIn(b'PC-G850 QUEST',bytes(m.text[1]))
            m.start();self.assertEqual(m.coords(),(5,13))
            self.assertIn(b'28/28',bytes(m.text[0]))
            self.assertEqual([r for r,_,d in m.pattern_calls if len(d)==144][-5:],list(range(1,6)))
            m.tap(0x02)
            self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,m.stack+2,0x1234,0x5678))
            m.check_memory()

    def test_camera_and_every_world_pixel_match_source_bitmap(self):
        m=QuestG850();m.start();_,_,atlas=read_bmp(HERE/'targets/g850/tiles.bmp')
        packed=bytes(m.cpu.memory[m.sym['map_packed']:m.sym['map_packed']+240])
        for x,y in ((0,0),(29,0),(0,15),(29,15),(5,13),(14,7),(15,8),(20,4)):
            m.place(x,y);m.routine('world_redraw_map_with_player')
            cx,cy=max(0,min(12,x-9)),max(0,min(11,y-2))
            self.assertEqual((m.byte('camera_x'),m.byte('camera_y')),(cx,cy))
            expected=bytearray(864)
            for py in range(40):
                for px in range(144):
                    tx,ty=cx+px//8,cy+py//8
                    tile=15 if (tx,ty)==(x,y) else (packed[ty*15+tx//2]>>(0 if tx&1 else 4))&15
                    if atlas[(tile*8+py%8)*8+px%8]==(0,0,0):expected[(py//8+1)*144+px]|=1<<(py%8)
            self.assertEqual(m.pixels(),expected,(x,y));m.check_memory()

    def test_battle_portraits_hp_and_actions_do_not_overlap(self):
        for lang in ('FR','EN'):
            m=QuestG850(lang);m.start();m.place(17,13);m.tap(0x22)
            self.assertEqual(m.mode(),'menu_battle')
            self.assertIn(b'SKELE' if lang=='EN' else b'SQUELETTE',bytes(m.text[0]))
            self.assertIn(b'28/28',bytes(m.text[3]))
            self.assertTrue(all(any(m.screen[y][12:28]) and any(m.screen[y][108:124]) for y in (1,2)))
            self.assertIn(b'Attack' if lang=='EN' else b'Attaque',bytes(m.text[5]))
            m.tap(0x28);self.assertEqual(m.mode(),'typing')
            m.poll(0)  # release ENTER: the word is drawn after the key flush
            self.assertTrue(any(c!=32 for c in m.text[4]));self.assertIn(ord('^'),m.text[5])
            m.tap(0x51);m.check_memory()

    def test_typing_duration_matches_g80x_at_each_default_clock(self):
        for level in (1,12,24,99):
            times=[]
            for machine,clock,reload in ((QuestMachine,4_000_000,6),(QuestG850,8_000_000,12)):
                m=machine();m.start();m.set_byte('player_level',level)
                m.place(17,13);m.tap(0x22);m.tap(0x28);m.poll(0)
                units=m.byte('typing_timeout');remaining=m.byte('typing_tick_div');start=m.tstates;polls=0
                while m.mode()=='typing':
                    last=m.tstates
                    m.poll(0);polls+=1
                self.assertEqual(polls,remaining+(units-1)*reload)
                times.append((last-start)/clock)  # exclude the following round's drawing
                m.check_memory()
            self.assertLess(abs(times[0]-times[1]),0.04)

    def test_ram_save_resume_and_new_game_on_the_native_stack(self):
        m=QuestG850();m.start();m.set_byte('inventory_potions',7);m.set_byte('encounter_cooldown',250)
        m.tap(0x22);m.tap(2);m.cpu.pc,m.cpu.sp=256,m.stack;m.seek_key();m.tap(0x28)
        self.assertEqual((m.mode(),m.coords(),m.byte('inventory_potions')),('world',(6,13),7))
        m.tap(2);m.cpu.pc,m.cpu.sp=256,m.stack;m.seek_key();m.tap(0x1F);m.tap(0x28);m.tap(0x28)
        self.assertEqual((m.coords(),m.byte('inventory_potions')),((5,13),1));m.check_memory()


# Run the same gameplay assertions against both model binaries.
for name in ('test_map_exact_and_all_tile_reads','test_movement_edges_walls_and_status',
    'test_enemy_records_and_level_progression','test_statistics_and_level_four_sword_damage',
    'test_typing_success_error_timeout_and_repeated_letters','test_boss_gates_all_stages_and_oasis_guard',
    'test_all_story_regions_reachable','test_shops_inn_purchases_and_cancel',
    'test_potion_at_255_hp_and_smoke_escape','test_defeat_returns_home_without_stack_leak',
    'test_repeated_letters_need_release','test_five_bosses_through_final_return',
    'test_natural_random_encounter_and_cooldown','test_menu_and_dialogue_strings_fit_the_lcd'):
    setattr(G850Checks,name,getattr(QuestChecks,name))


if __name__=='__main__':
    parser=Parser('Verifier Quest G850.','Check Quest G850.');parser.parse_args()
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(G850Checks))
    raise SystemExit(not result.wasSuccessful())
