"""CPU and game-flow checks for the G801 Quest port. Requires z80==1.2.0.

Sharp IOCS are mocked with deliberately clobbered registers, not a real ROM.
No alterations to the upstream Canon project are made.
"""
from pathlib import Path
from collections import deque
import hashlib
import json
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tests"))
from check_programs import Machine, IOCS, RETURN
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from cli_i18n import Parser, pick

KEYS = {
    "Q":2,"W":3,"E":4,"R":5,"T":6,"Y":7,"U":8,"A":9,"S":10,"D":11,"F":12,"G":13,"H":14,"J":15,
    "K":16,"Z":17,"X":18,"C":19,"V":20,"B":21,"N":22,"M":23,"L":41,"I":49,"O":50,"P":57,
}
DIRS = {(1,0):0x22, (-1,0):0x21, (0,1):0x1F, (0,-1):0x20}
TIMING_SAMPLES=[]


class QuestMachine(Machine):
    def __init__(self, language="FR"):
        self.text_writes=[]
        self.tstates=0
        super().__init__(f"quest_{language}", HERE / "build")
        self.cpu.set_input_callback(lambda port: (_ for _ in ()).throw(AssertionError(f"Unexpected IN {port}")))
        self.cpu.set_output_callback(lambda port, value: (_ for _ in ()).throw(AssertionError(f"Unexpected OUT {port}")))

    def rom_return(self, key=None):
        # Cout g800 PC-G801 / g800 PC-G801 costs, not physical ROM timings.
        self.tstates += {0xBE53:18000,0xBE62:1800,0xBFD0:100+170*self.cpu.b,
                         0xBFEE:100+1800*self.cpu.b}.get(self.cpu.pc,0)
        if self.cpu.pc == 0xBE62:
            self.text_writes.append((self.cpu.d,self.cpu.e,self.cpu.a))
        if self.cpu.pc == 0xBFD0:
            row, col, width = self.cpu.d, self.cpu.e, self.cpu.b
            self.text[row][col:col + (width + 4)//5] = b" " * ((width + 4)//5)
        super().rom_return(key)

    def seek_key(self):
        for _ in range(2000):
            self.cpu.ticks_to_stop=100000
            self.cpu.run()
            self.tstates += (100000-self.cpu.ticks_to_stop)&0xFFFFFFFF
            if self.cpu.pc in (0xBE53,RETURN):
                return
            if self.cpu.pc in IOCS:
                self.rom_return()
        raise AssertionError(f"CPU did not yield: PC={self.cpu.pc:04X}")

    def start(self):
        self.tap(0x28)           # Continue starts a new game without a save
        assert self.mode() == "confirm", self.mode()
        self.tap(0x28)           # intro
        assert self.mode() == "world", self.mode()

    def mode(self):
        if self.cpu.pc == RETURN:
            return "returned"
        assert self.cpu.pc == 0xBE53
        stack = [int.from_bytes(self.cpu.memory[p:p + 2], "little") for p in range(self.cpu.sp, self.cpu.sp + 24, 2)]
        if self.sym["quest_key_ascii"] + 3 in stack:
            return "typing"
        caller = stack[8]
        if caller == self.sym["main"] + 3:
            return "world"
        if caller == self.sym["menu_loop"] + 3:
            for name in ("menu_title", "menu_battle", "menu_objects", "menu_castle", "menu_village", "menu_castle_shop", "menu_village_shop", "menu_castle_inn"):
                if self.word("menu_jump_ptr") == self.sym[name] + 1:
                    return name
            return "menu_unknown"
        if caller == self.sym["quest_wait_confirm"] + 3:
            return "confirm"
        raise AssertionError(f"Unknown wait stack: {[hex(x) for x in stack]}")

    def coords(self):
        return self.byte("chunk_x") * 15 + self.byte("player_x")//8, self.byte("chunk_y")*4 + self.byte("player_y")//8

    def place(self, x, y):
        for name, value in (("chunk_x", x//15), ("chunk_y", y//4), ("player_x", (x%15)*8), ("player_y", (y%4)*8)):
            self.set_byte(name, value)

    def call(self, name, **registers):
        self.cpu.pc, self.cpu.sp = self.sym[name], 0x1FF0
        self.cpu.memory[0x1FF0:0x1FF2] = RETURN.to_bytes(2, "little")
        for name, value in registers.items():
            setattr(self.cpu, name, value)
        for _ in range(5000):
            self.cpu.ticks_to_stop = 100000
            self.cpu.run()
            if self.cpu.pc == RETURN:
                return
            if self.cpu.pc in IOCS:
                if self.cpu.pc == 0xBE53:
                    raise AssertionError("Routine unexpectedly waits for input")
                self.rom_return()
        raise AssertionError(f"No routine return at {self.cpu.pc:04X}")

    def handle_battle(self):
        for _ in range(100):
            mode = self.mode()
            if mode in ("world", "returned"):
                return
            if mode == "menu_battle":
                self.tap(0x28)   # Attack (first option)
            elif mode == "typing":
                ptr = self.word("typing_word_ptr")
                word = bytes(self.cpu.memory[ptr:ptr + self.byte("typing_word_len")]).decode("ascii")
                for letter in word:
                    self.tap(KEYS[letter])
                    # Completing a word can immediately change the mode.
                    if self.mode() != "typing":
                        break
            elif mode == "confirm":
                self.tap(0x28)
            else:
                raise AssertionError(f"Unexpected battle state {mode}")
        raise AssertionError("Battle did not finish")


class QuestChecks(unittest.TestCase):
    def test_both_languages_start_render_and_return(self):
        for language in ("FR", "EN"):
            m = QuestMachine(language)
            self.assertEqual(m.mode(), "menu_title")
            self.assertIn(b"QUEST", bytes(m.text[0]))
            m.start()
            self.assertEqual(m.coords(), (5, 13))
            self.assertEqual((m.byte("player_level"), m.byte("player_hp_cur")), (1, 28))
            self.assertTrue(any(len(data) == 120 for _, _, data in m.pattern_calls))
            self.assertTrue(bytes(m.text[0][15:]).startswith(b"PV28/28" if language=="FR" else b"HP28/28"))
            self.assertTrue(bytes(m.text[1][15:]).startswith(b"Niveau 1" if language=="FR" else b"Level 1"))
            self.assertTrue(bytes(m.text[2][15:]).startswith(b"Or 10" if language=="FR" else b"Gold 10"))
            m.tap(0x02)
            self.assertEqual((m.cpu.pc, m.cpu.sp, m.cpu.ix, m.cpu.iy), (RETURN, 0x1FF2, 0x1234, 0x5678))
            m.check_memory()

    def test_map_exact_and_all_tile_reads(self):
        m = QuestMachine()
        packed = bytes(m.cpu.memory[m.sym["map_packed"]:m.sym["map_packed"] + 240])
        self.assertEqual(len(packed), 240)
        for y in range(16):
            for x in range(30):
                expected = (packed[y*15+x//2] >> (0 if x & 1 else 4)) & 15
                m.call("world_get_map_tile_bc", b=y, c=x)
                self.assertEqual(m.cpu.a, expected, (x,y))
        m.check_memory()

    def test_movement_edges_walls_and_status(self):
        m = QuestMachine()
        m.start()
        m.set_byte("encounter_cooldown", 250)
        m.tap(0x22)
        self.assertEqual(m.coords(), (6,13))
        m.poll(0x22)
        self.assertEqual(m.coords(), (6,13))
        m.tap(0x20)
        self.assertEqual(m.coords(), (6,12))
        m.place(1,11)
        m.tap(0x21)
        self.assertEqual(m.coords(), (1,11))  # mountain wall at x=0
        m.place(14,13)
        m.tap(0x22)
        self.assertEqual(m.coords(), (15,13))
        self.assertEqual(m.byte("chunk_x"), 1)
        m.tap(0x17)  # M status
        self.assertEqual(m.mode(), "confirm")
        m.tap(0x28)
        self.assertEqual(m.mode(), "world")
        m.check_memory()

    def test_save_resume_and_new_game(self):
        m = QuestMachine()
        m.start()
        m.set_byte("encounter_cooldown", 250)
        m.set_byte("inventory_potions", 7)
        m.tap(0x22)
        self.assertEqual(m.byte("save_inventory_potions"), 7)
        m.tap(2)
        m.cpu.pc, m.cpu.sp = 0x100, 0x1FF0
        m.seek_key()
        m.tap(0x28)
        self.assertEqual(m.mode(), "world")
        self.assertEqual((m.coords(), m.byte("inventory_potions")), ((6,13),7))
        m.tap(2)
        m.cpu.pc, m.cpu.sp = 0x100, 0x1FF0
        m.seek_key()
        m.tap(0x1F)  # New game
        m.tap(0x28)
        self.assertEqual(m.mode(), "confirm")
        m.tap(0x28)
        self.assertEqual((m.coords(),m.byte("inventory_potions")), ((5,13),1))
        m.check_memory()

    def test_enemy_records_and_level_progression(self):
        m = QuestMachine()
        for enemy in range(10):
            m.call("progress_load_enemy_from_id", a=enemy)
            p = m.sym["enemy_slime"] + enemy*8
            original = bytes(m.cpu.memory[p:p+8])
            live = bytes(m.cpu.memory[m.sym["battle_enemy_tile"]:m.sym["battle_enemy_tile"]+8])
            self.assertEqual(original,live)
            self.assertEqual(m.byte("battle_enemy_hp_cur"),original[1])
        m.set_byte("player_level",1)
        m.set_word("player_exp",50)
        m.call("progress_check_level_up")
        self.assertEqual(m.byte("player_level"),4)
        self.assertEqual(m.byte("player_hp_cur"),m.byte("player_hp_max"))
        m.check_memory()

    def test_statistics_and_level_four_sword_damage(self):
        for language in ("FR","EN"):
            m=QuestMachine(language)
            for level in range(1,100):
                for equipment in (0,1,2):
                    for name,value in (("player_level",level),("player_atk_bonus",equipment),("player_def_bonus",equipment)):
                        m.set_byte(name,value)
                    m.call("progress_sync_player_stats_from_level")
                    expected=(min(255,26+2*level+level//2),3+level//4+level//8+equipment,
                              3+level//8+level//16+equipment,24+level//2+level//4)
                    actual=tuple(m.byte(name) for name in ("player_hp_max","player_atk","player_def","player_flee"))
                    self.assertEqual(actual,expected,(language,level,equipment))
            m.set_byte("player_level",4);m.set_byte("player_atk_bonus",1)
            m.call("progress_sync_player_stats_from_level")
            self.assertEqual(m.byte("player_atk"),5)
            for enemy,normal,fast in ((0,(4,1,5),(3,2,5)),(1,(5,1,6),(5,2,7)),(5,(4,1,5),(4,2,6))):
                for result,expected in ((1,normal),(2,fast)):
                    m.call("progress_load_enemy_from_id",a=enemy)
                    m.set_byte("battle_event_flag_mask",1 if enemy==5 else 0)
                    m.set_byte("typing_result",result)
                    hp=m.byte("battle_enemy_hp_cur")
                    m.call("battle_apply_player_attack")
                    self.assertEqual((m.byte("last_player_damage"),m.byte("last_player_bonus"),hp-m.byte("battle_enemy_hp_cur")),expected)
            m.check_memory()

    def test_equipment_plus_two_purchase_save_and_no_downgrade(self):
        for language in ("FR","EN"):
            m=QuestMachine(language);m.start()
            m.set_byte("player_level",4);m.set_byte("player_atk_bonus",1);m.set_byte("player_def_bonus",1)
            m.call("progress_sync_player_stats_from_level")
            # Revenir a la boucle par une nouvelle entree / re-enter using the RAM save.
            m.call("game_autosave")
            m.cpu.pc,m.cpu.sp=0x100,0x1FF0;m.seek_key();m.tap(0x28)
            m.set_word("player_gold",1000)
            m.place(11,6);m.tap(0x22)
            self.assertEqual(m.mode(),"menu_village")
            m.tap(0x1F);m.tap(0x1F);m.tap(0x28)
            self.assertEqual(m.mode(),"menu_village_shop")
            self.assertIn(b"+2",bytes(m.text[2]))
            self.assertNotIn(b"+3",bytes(m.text[2]))
            m.tap(0x1F);m.tap(0x1F);m.tap(0x28)
            self.assertEqual((m.byte("player_atk_bonus"),m.byte("save_player_atk_bonus"),m.byte("player_atk"),m.word("player_gold")),(2,2,6,856))
            m.tap(0x1F);m.tap(0x1F);m.tap(0x28)
            self.assertEqual((m.mode(),m.word("player_gold")),("confirm",856))
            m.tap(0x28)
            for _ in range(3):m.tap(0x1F)
            m.tap(0x28)
            self.assertEqual((m.byte("player_def_bonus"),m.byte("save_player_def_bonus"),m.byte("player_def"),m.word("player_gold")),(2,2,5,712))
            m.tap(0x3A);m.tap(0x3A)
            self.assertEqual(m.mode(),"world")
            m.place(5,13);m.tap(0x21)
            m.tap(0x1F);m.tap(0x1F);m.tap(0x28)
            self.assertEqual(m.mode(),"menu_castle_shop")
            m.tap(0x1F);m.tap(0x1F);m.tap(0x28)
            self.assertEqual((m.mode(),m.byte("player_atk_bonus"),m.word("player_gold")),("confirm",2,712))
            m.check_memory()

    def test_typing_success_error_timeout_and_repeated_letters(self):
        for behavior in ("perfect","wrong","timeout"):
            m = QuestMachine()
            m.start()
            m.set_byte("encounter_cooldown",0)
            # Enter a real battle by stepping onto the cemetery boss at (18,13).
            m.place(17,13)
            m.tap(0x22)
            self.assertEqual(m.mode(),"menu_battle")
            m.tap(0x28)
            self.assertEqual(m.mode(),"typing")
            if behavior=="perfect":
                ptr=m.word("typing_word_ptr")
                word=bytes(m.cpu.memory[ptr:ptr+m.byte("typing_word_len")]).decode()
                for letter in word:
                    m.tap(KEYS[letter])
                self.assertEqual(m.byte("typing_result"),2)
            elif behavior=="wrong":
                ptr=m.word("typing_word_ptr")
                wrong="Z" if m.cpu.memory[ptr]!=ord("Z") else "A"
                m.tap(KEYS[wrong])
                self.assertEqual(m.byte("typing_result"),0)
            else:
                for _ in range(1200):
                    if m.mode()!="typing":
                        break
                    m.poll()
                self.assertNotEqual(m.mode(),"typing")
                self.assertEqual(m.byte("typing_result"),0)
            m.check_memory()

    def test_boss_gates_all_stages_and_oasis_guard(self):
        m=QuestMachine()
        for mask, prerequisite in ((2,1),(4,2),(8,4),(16,8)):
            m.set_byte("world_event_mask",mask)
            m.set_byte("event_flags",0)
            m.call("world_boss_is_unlocked")
            self.assertEqual(m.cpu.a,0)
            m.set_byte("event_flags",prerequisite)
            m.call("world_boss_is_unlocked")
            self.assertNotEqual(m.cpu.a,0)
        m.set_byte("event_flags",0)
        for name,value in (("target_chunk_x",1),("target_chunk_y",1),("target_player_x",80),("target_player_y",8)):
            m.set_byte(name,value)  # global 25,5
        m.call("check_target_tile_event")  # must not enter the oasis battle yet
        m.check_memory()

    def test_all_story_regions_reachable(self):
        m=QuestMachine()
        p=m.sym["map_packed"]
        packed=m.cpu.memory[p:p+240]
        def tile(x,y):
            return (packed[y*15+x//2]>>(0 if x&1 else 4))&15
        reached={(5,13)}
        queue=deque(reached)
        while queue:
            x,y=queue.popleft()
            for dx,dy in DIRS:
                n=(x+dx,y+dy)
                if 0<=n[0]<30 and 0<=n[1]<16 and n not in reached and tile(*n)<9:
                    reached.add(n)
                    queue.append(n)
        for location in ((3,13),(12,6),(18,13),(3,6),(16,2),(26,5),(27,13)):
            self.assertIn(location,reached)

    def test_shops_inn_purchases_and_cancel(self):
        m=QuestMachine()
        m.start()
        m.set_word("player_gold",500)
        m.set_byte("player_hp_cur",10)
        m.tap(0x21)  # castle at x4,y13
        self.assertEqual(m.mode(),"menu_castle")
        m.tap(0x1F); m.tap(0x28)  # Inn
        self.assertEqual(m.mode(),"menu_castle_inn")
        m.tap(0x28)
        self.assertEqual((m.mode(),m.word("player_gold"),m.byte("player_hp_cur")),("menu_castle",492,28))
        m.tap(0x1F);m.tap(0x1F);m.tap(0x28)  # Shop
        self.assertEqual(m.mode(),"menu_castle_shop")
        m.tap(0x28)  # potion 14
        self.assertEqual((m.byte("inventory_potions"),m.word("player_gold")),(2,478))
        m.tap(0x1F);m.tap(0x1F);m.tap(0x28)  # sword 48
        self.assertEqual((m.byte("player_atk_bonus"),m.word("player_gold")),(1,430))
        for _ in range(3):m.tap(0x1F)
        m.tap(0x28)  # armour 48
        self.assertEqual((m.byte("player_def_bonus"),m.word("player_gold")),(1,382))
        m.tap(0x1F);m.tap(0x28)  # smoke 22
        self.assertEqual((m.byte("inventory_smokes"),m.word("player_gold")),(1,360))
        m.tap(0x3A)
        self.assertEqual(m.mode(),"menu_castle")
        m.tap(0x3A)
        self.assertEqual(m.mode(),"world")
        m.check_memory()

    def test_potion_at_255_hp_and_smoke_escape(self):
        m=QuestMachine()
        m.start()
        for name,value in (("player_level",99),("player_hp_max",255),("player_hp_cur",250),("player_def",24),("inventory_smokes",1)):
            m.set_byte(name,value)
        m.place(17,13);m.tap(0x22)
        m.tap(0x22);m.tap(0x28) # Objects
        self.assertEqual(m.mode(),"menu_objects")
        m.tap(0x28)            # Potion, capped before enemy turn
        self.assertEqual(m.mode(),"menu_battle")
        self.assertIn(m.byte("player_hp_cur"),(253,254))
        self.assertEqual(m.byte("inventory_potions"),0)
        m.tap(0x22);m.tap(0x28)
        m.tap(0x1F);m.tap(0x28) # Smoke
        self.assertEqual(m.mode(),"world")
        self.assertEqual((m.byte("inventory_smokes"),m.byte("event_flags")),(0,0))
        m.check_memory()

    def test_defeat_returns_home_without_stack_leak(self):
        m=QuestMachine()
        m.start()
        m.set_byte("player_hp_cur",1)
        m.place(17,13);m.tap(0x22);m.tap(0x28)
        ptr=m.word("typing_word_ptr")
        m.tap(KEYS["Z" if m.cpu.memory[ptr]!=ord("Z") else "A"])
        self.assertEqual(m.mode(),"confirm") # round damage
        m.tap(0x28)
        self.assertEqual(m.mode(),"confirm") # Game Over
        m.tap(0x28)
        self.assertEqual((m.mode(),m.coords(),m.byte("player_hp_cur")),("world",(5,13),28))
        m.tap(2)
        self.assertEqual(m.cpu.sp,0x1FF2)
        m.check_memory()

    def test_repeated_letters_need_release(self):
        m=QuestMachine()
        m.start()
        m.place(17,13);m.tap(0x22);m.tap(0x28)
        m.set_word("typing_word_ptr",m.sym["typing_word_assaut"])
        m.set_byte("typing_word_len",6)
        m.tap(KEYS["A"]);m.tap(KEYS["S"])
        m.poll(KEYS["S"])
        self.assertEqual(m.byte("typing_index"),2)
        for letter in "SAUT":m.tap(KEYS[letter])
        self.assertEqual(m.byte("typing_result"),2)

    def test_five_bosses_through_final_return(self):
        # A late-game character fixture exercises actual menus, typing, damage,
        # rewards, flags and the ending. It does not claim a natural grind.
        m=QuestMachine()
        m.start()
        for name,value in (("player_level",99),("player_hp_max",255),("player_hp_cur",255),("player_atk",42),("player_def",24)):
            m.set_byte(name,value)
        stages=(((17,13),0x22,1),((3,7),0x20,3),((16,3),0x20,7),((26,5),0x21,15),((26,13),0x22,31))
        for location,key,flags in stages:
            m.place(*location)
            m.set_byte("player_hp_cur",255)
            m.tap(key)
            self.assertEqual(m.mode(),"menu_battle")
            m.handle_battle()
            self.assertEqual(m.byte("event_flags"),flags)
            self.assertEqual(m.byte("save_event_flags"),flags)
        self.assertEqual(m.mode(),"returned")
        self.assertEqual((m.cpu.sp,m.cpu.ix,m.cpu.iy),(0x1FF2,0x1234,0x5678))
        m.check_memory()

    def test_natural_random_encounter_and_cooldown(self):
        m=QuestMachine()
        m.start()
        m.set_byte("rng_seed",16)  # next LFSR value 8 triggers the 1/8 roll
        m.tap(0x22)
        self.assertEqual(m.mode(),"menu_battle")
        self.assertEqual(m.byte("battle_enemy_tile"),16) # slime, home zone
        m.handle_battle()
        self.assertEqual((m.mode(),m.word("player_exp"),m.word("player_gold")),("world",4,17))
        m.set_byte("rng_seed",16)
        m.tap(0x22)
        self.assertEqual((m.mode(),m.byte("encounter_cooldown")),("world",3))
        m.check_memory()

    def test_break_inside_combat_and_unsigned_display(self):
        m=QuestMachine()
        m.start()
        m.place(17,13);m.tap(0x22);m.tap(0x28)
        self.assertEqual(m.mode(),"typing")
        m.tap(0x51)
        self.assertEqual((m.cpu.pc,m.cpu.sp,m.cpu.ix,m.cpu.iy),(RETURN,0x1FF2,0x1234,0x5678))
        for value in (0,1,9,10,99,100,255,1000,65535):
            m.set_word("cursor_xy",0x0101)
            m.text[0][:]=b" "*24
            m.call("quest_print_uint",hl=value)
            self.assertEqual(bytes(m.text[0]).strip(),str(value).encode())
        m.check_memory()

    def test_typing_deadline_and_late_success_in_both_languages(self):
        for language in ("FR","EN"):
            for level in (1,6,12,24,99):
                m=QuestMachine(language)
                m.start()
                m.set_byte("player_level",level)
                m.place(17,13);m.tap(0x22);m.tap(0x28)
                self.assertEqual(m.mode(),"typing")
                m.poll(0) # relacher ENTER et terminer l'affichage / release ENTER and finish drawing
                units=m.byte("typing_timeout")
                reload=json.loads((HERE/"build/manifest.json").read_text())["typing_reload"]
                remaining=m.byte("typing_tick_div")
                self.assertEqual(remaining,reload-1)
                start=m.tstates
                polls=0
                while m.mode()=="typing" and polls<5000:
                    m.poll();polls+=1
                self.assertNotEqual(m.mode(),"typing")
                self.assertEqual(polls,remaining+(units-1)*reload)
                seconds=(m.tstates-start)/4_000_000
                if reload==5:
                    self.assertGreater(seconds,1.0)
                    self.assertLess(seconds,1.9)
                if reload==6:
                    self.assertGreater(seconds,1.2)
                    self.assertLess(seconds,2.25)
                TIMING_SAMPLES.append({"language":language,"level":level,"polls":polls,"typing_reload":reload,
                                       "modeled_seconds_at_4MHz":round(seconds,4)})
                m.check_memory()
            m=QuestMachine(language)
            m.start();m.place(17,13);m.tap(0x22);m.tap(0x28)
            m.set_byte("typing_timeout",m.byte("typing_bonus_limit")-1)
            p=m.word("typing_word_ptr")
            for letter in bytes(m.cpu.memory[p:p+m.byte("typing_word_len")]).decode("ascii"):
                m.tap(KEYS[letter])
            self.assertEqual(m.byte("typing_result"),1)

    def test_long_words_allow_a_slower_normal_success(self):
        # Regression: ten letters at this pace exceed the old 5-poll deadline.
        # FR: dix lettres auparavant trop lentes ; EN: ten-letter word regression.
        reload=json.loads((HERE/"build/manifest.json").read_text())["typing_reload"]
        if reload != 6:
            self.skipTest("Reference pacing scenario requires the default reload=6")
        for language,label in (("FR","typing_word_bousculade"),("EN","typing_word_annihilate")):
            with self.subTest(language=language):
                m=QuestMachine(language)
                m.start();m.set_byte("player_level",24)
                m.place(17,13);m.tap(0x22);m.tap(0x28)
                self.assertEqual(m.mode(),"typing")
                p=m.sym[label]
                word=bytes(m.cpu.memory[p:p+16]).split(b"\0",1)[0]
                self.assertEqual(len(word),10)
                m.set_word("typing_word_ptr",p)
                m.set_byte("typing_word_len",len(word))
                m.poll(0)
                for letter in word.decode("ascii"):
                    for _ in range(36):
                        self.assertEqual(m.mode(),"typing")
                        m.poll(0)
                    self.assertEqual(m.mode(),"typing")
                    m.tap(KEYS[letter])
                self.assertNotEqual(m.mode(),"typing")
                self.assertEqual(m.byte("typing_result"),1)
                m.check_memory()

    def test_full_width_battle_status_and_maximum_values(self):
        for language in ("FR","EN"):
            m=QuestMachine(language);m.start()
            for label,value in (("player_hp_cur",255),("player_hp_max",255),("inventory_potions",255),
                                ("inventory_smokes",255),("player_level",99)):
                m.set_byte(label,value)
            m.set_word("player_gold",65535)
            m.call("world_redraw_map_with_player")
            self.assertEqual(bytes(m.text[0][15:]),b"PV255/255" if language=="FR" else b"HP255/255")
            self.assertEqual(bytes(m.text[1][15:]).strip(),b"Niveau 99" if language=="FR" else b"Level 99")
            m.call("pcg_clear");m.call("world_draw_status_screen")
            self.assertIn(b"65535",bytes(m.text[0]))
            self.assertIn(b"255/255",bytes(m.text[1]))
            self.assertIn(b"Potions 255",bytes(m.text[2]))
            self.assertIn(b"Fumees 255" if language=="FR" else b"Smoke 255",bytes(m.text[2]))
            m.call("progress_load_enemy_from_id",a=9)
            m.text_writes.clear()
            m.call("battle_draw_scene")
            self.assertEqual(bytes(m.text[1][2:12]),b"PV 255/255" if language=="FR" else b"HP 255/255")
            self.assertEqual(bytes(m.text[1][16:22]),b"PV 160" if language=="FR" else b"HP 160")
            self.assertFalse(any(row==1 and col in (0,13,14,15) for row,col,_ in m.text_writes))
            m.check_memory()

    def test_menu_and_dialogue_strings_fit_the_lcd(self):
        for language in ("FR","EN"):
            m=QuestMachine(language)
            for label in ("menu_battle","menu_objects","menu_village","menu_village_shop","menu_castle", "menu_castle_inn","menu_castle_shop","menu_title"):
                p=m.sym[label];count=m.cpu.memory[p];p+=1+2*count
                occupied=set()
                for _ in range(count):
                    x,y=m.cpu.memory[p:p+2];p+=2
                    end=bytes(m.cpu.memory[p:p+128]).index(0)
                    self.assertTrue(2<=x and x+end-1<=24 and 1<=y<=4,(language,label,x,y,end))
                    cells={(y,col) for col in range(x-1,x+end)} # cursor + text
                    self.assertFalse(occupied&cells,(language,label))
                    occupied|=cells;p+=end+1
            for label in ("intro_text","msg_king_1","msg_king_2","msg_king_3","msg_king_4","msg_village_0","msg_village_1"):
                p=m.sym[label]
                text=bytes(m.cpu.memory[p:p+128]).split(b"\0",1)[0]
                self.assertLessEqual(len(text.split(b"\r")),4)
                self.assertTrue(all(len(line)<=24 for line in text.split(b"\r")),(language,label,text))


if __name__ == "__main__":
    parser=Parser("Vérifier les scénarios CPU, la disposition et la temporisation de Quest (IOCS simulés).", "Check Quest CPU scenarios, layout and timing (mocked IOCS).")
    args=parser.parse_args()
    print(pick(args.lang,"Vérification CPU de Quest FR/EN ; aucun appareil connecté.","Quest FR/EN CPU checks; no hardware connected."),flush=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(QuestChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={"tests":result.testsRun,"passed":result.wasSuccessful(),"failures":len(result.failures),"errors":len(result.errors),"cpu":"z80 1.2.0","iocs":"mock contracts, NOT a Sharp ROM","physical_g801_tested":False,
            "timing_model":"Z80 instruction cycles + g800 0.11.4 IOCS costs at 4 MHz; NOT wall-clock or hardware measurement", "typing_samples":TIMING_SAMPLES}
    (HERE/"build/cpu_validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    raise SystemExit(not result.wasSuccessful())
