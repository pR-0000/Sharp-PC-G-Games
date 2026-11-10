"""FR/EN: native G850 renderer plus shared Pocket Depths rules."""
from pathlib import Path
import sys,unittest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from g850_machine import G850Machine
import check_depths as shared
LegacyDepths=shared.DepthsMachine
class DepthsG850(G850Machine):
    coords=LegacyDepths.coords
    tile=LegacyDepths.tile
    actor=LegacyDepths.actor
    peaceful=LegacyDepths.peaceful
    arena=LegacyDepths.arena
    def __init__(self,language='FR',lite=False):
        self.language=language;self.lite=False
        super().__init__('depths_g850_'+language,HERE/'build/g850')

class NativeChecks(unittest.TestCase):
    def test_native_render_uses_all_five_bands_and_rom_hud_in_both_languages(self):
        for language in ('FR','EN'):
            m=DepthsG850(language);m.start();m.arena()
            for x in range(1,15):m.tile(x,10,1)
            m.actor(0,[8,11,1,3,0]);m.routine('render')
            self.assertEqual(len(m.pixels()),864)
            self.assertTrue(all(any(m.pixels()[row*144:(row+1)*144]) for row in range(5)))
            self.assertEqual(bytes(m.text[5][1:4]),b'100')
            self.assertEqual(bytes(m.text[5][21:24]),b'024')
            self.assertTrue(any(row==4 and len(data)==144 for row,col,data in m.pattern_calls))
            m.check_memory()
    def test_native_call_preserves_registers_stack_and_firmware_memory(self):
        from check_programs import RETURN
        m=DepthsG850();m.cpu.pc=m.sym['entry'];m.cpu.sp=m.stack
        m.cpu.memory[m.stack:m.stack+2]=RETURN.to_bytes(2,'little')
        expected={'bc':0x2345,'de':0x3456,'hl':0x4567,'ix':0x1234,'iy':0x5678}
        for name,value in expected.items():setattr(m.cpu,name,value)
        m.seek_key();m.start();m.tap(0x02)
        self.assertEqual((m.cpu.pc,m.cpu.sp),(RETURN,m.stack+2))
        for name,value in expected.items():self.assertEqual(getattr(m.cpu,name),value)
        m.check_memory()
    def test_native_ray_depths_match_independent_grid_walk_all_headings(self):
        from build_depths import ray_steps
        m=DepthsG850();m.start();m.arena();m.tile(8,9,2)
        for heading in range(4):
            m.set_byte('direction',heading);m.routine('render')
            expected=[]
            for ray in range(48):
                value=63
                for offset,visual in ray_steps(23-ray if ray<24 else ray-24,24):
                    f,l=divmod(offset,8);l=l if ray>=24 else -l
                    dx,dy=((l,-f),(f,l),(-l,f),(-f,-l))[heading]
                    if m.tile(8+dx,12+dy) in (1,2,3,9):value=visual&63;break
                expected.append(value)
            p=m.sym['ray_depths'];self.assertEqual(list(m.cpu.memory[p:p+48]),expected)
        m.check_memory()
    def test_native_sprites_are_occluded_by_pillars(self):
        m=DepthsG850();m.start();m.arena();m.tile(8,10,2);m.routine('render');plain=m.pixels()
        m.actor(0,[8,9,0,3,0]);m.routine('render');self.assertEqual(m.pixels(),plain)
        m.actor(0,[8,11,0,3,0]);m.routine('render');self.assertNotEqual(m.pixels(),plain)
        m.check_memory()

for name in ('test_guard_spends_a_turn_halves_damage_and_expires_on_next_action',
    'test_beacons_resupply_once_with_health_and_ammunition_caps',
    'test_shotgun_staggers_and_pushes_a_survivor_but_respects_walls',
    'test_three_floor_campaign_and_held_enter_does_not_skip_results',
    'test_campaign_restart_restores_first_layout_and_enemy_health',
    'test_complete_level_in_both_languages_without_ram_fixtures',
    'test_weapons_ammunition_damage_and_occlusion','test_enemy_warning_cover_and_no_wall_crossing',
    'test_key_edges_turns_strafe_and_walls','test_title_help_and_game_help_return',
    'test_generated_levels_match_reference_and_all_objectives_are_reachable',
    'test_restart_reuses_layout_and_n_generates_another_only_in_full','test_texts_fit_and_idle_does_not_repaint'):
    def run(self,name=name):
        previous=shared.DepthsMachine;shared.DepthsMachine=DepthsG850
        try:getattr(shared.DepthsChecks,name)(self)
        finally:shared.DepthsMachine=previous
    setattr(NativeChecks,name,run)
if __name__=='__main__':
    from cli_i18n import Parser
    Parser('Verifier la version G850.','Check the G850 edition.').parse_args()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeChecks)).wasSuccessful())
