"""Execute the supplied Z80 binaries against strict mock IOCS contracts.

Requires z80==1.2.0 (verification only). Does not emulate a physical Sharp ROM.
IOCS entry points/column format are checked separately in g800 0.11.4.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

import z80

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build import read_symbols
from cli_i18n import Parser, pick

BUILD = ROOT / "build"
IOCS = (0xBE53, 0xBE62, 0xBFD0, 0xBFEE)
RETURN = 0x7000


class Machine:
    def __init__(self, name="star_lane", build_dir=BUILD):
        self.sym = read_symbols(build_dir / f"{name}.sym")
        self.cpu = z80.Z80Machine()
        self.cpu.memory[:] = bytes([0xA5]) * 65536
        binary = (build_dir / f"{name}.bin").read_bytes()
        self.cpu.memory[0x100:0x100 + len(binary)] = binary
        # Independently decode every HEX record, checksum and address.
        decoded = bytearray()
        address = 0x100
        for text in (build_dir / f"{name}.hex").read_text().splitlines():
            assert text.startswith(":")
            record = bytes.fromhex(text[1:])
            assert len(record) == record[0] + 5 and sum(record) % 256 == 0
            if record[3] == 1:
                assert record == bytes.fromhex("00000001FF")
                break
            assert record[3] == 0 and int.from_bytes(record[1:3], "big") == address
            decoded.extend(record[4:-1])
            address += record[0]
        assert bytes(decoded) == binary
        self.cpu.pc, self.cpu.sp = 0x100, 0x1FF0
        self.cpu.ix, self.cpu.iy = 0x1234, 0x5678
        self.cpu.memory[0x1FF0:0x1FF2] = RETURN.to_bytes(2, "little")
        self.baseline = bytes(self.cpu.memory)
        self.screen = [bytearray(120) for _ in range(4)]
        self.text = [bytearray(b" " * 24) for _ in range(4)]
        self.pattern_calls = []
        self.minimum_sp = self.cpu.sp
        for address in (*IOCS, RETURN):
            self.cpu.set_breakpoint(address)
        self.seek_key()

    def byte(self, name):
        return self.cpu.memory[self.sym[name]]

    def set_byte(self, name, value):
        self.cpu.memory[self.sym[name]] = value

    def word(self, name):
        p = self.sym[name]
        return int.from_bytes(self.cpu.memory[p:p + 2], "little")

    def set_word(self, name, value):
        p = self.sym[name]
        self.cpu.memory[p:p + 2] = value.to_bytes(2, "little")

    def rom_return(self, key=None):
        cpu = self.cpu
        if cpu.pc == 0xBE53:
            assert key is not None
        else:
            assert 0 <= cpu.d < 4 and 0 <= cpu.e < 24
            row, col = cpu.d, cpu.e
            if cpu.pc == 0xBE62:
                self.text[row][col] = max(cpu.a, 32)
            elif cpu.pc == 0xBFEE:
                assert 0 < cpu.b <= 24 - col  # this program must never scroll
                self.text[row][col:col + cpu.b] = bytes([cpu.a]) * cpu.b
                self.screen[row][col * 5:(col + cpu.b) * 5] = bytes(cpu.b * 5)
            elif cpu.pc == 0xBFD0:
                assert 0 < cpu.b <= 120 - col * 5
                data = bytes(cpu.memory[cpu.hl:cpu.hl + cpu.b])
                assert all(value < 128 for value in data)
                self.screen[row][col * 5:col * 5 + cpu.b] = data
                self.pattern_calls.append((row, col, data))
            else:
                raise AssertionError(f"Unexpected ROM call {cpu.pc:04X}")
        # Deliberately destroy more main registers than g800 does. Wrappers
        # must shield the game; alternate registers are never used.
        for register in ("af", "bc", "de", "hl", "ix", "iy"):
            setattr(cpu, register, 0xD3A7)
        if key is not None:
            cpu.a = key
        return_address = int.from_bytes(cpu.memory[cpu.sp:cpu.sp + 2], "little")
        self.minimum_sp = min(self.minimum_sp, cpu.sp)
        assert 0x100 <= return_address < self.sym["program_end"]
        cpu.pc = return_address
        cpu.sp += 2

    def seek_key(self):
        for _ in range(2000):
            self.cpu.ticks_to_stop = 100000
            self.cpu.run()
            if self.cpu.pc in (0xBE53, RETURN):
                return
            if self.cpu.pc in IOCS:
                self.rom_return()
        raise AssertionError(f"CPU did not yield: PC={self.cpu.pc:04X}")

    def poll(self, key=0):
        assert self.cpu.pc == 0xBE53
        self.rom_return(key)
        self.seek_key()

    def tap(self, key):
        self.poll(0)
        self.poll(key)

    def start(self):
        self.tap(0x28)
        assert self.byte("phase") == 1

    def next_world(self):
        self.set_byte("poll_count", 1)
        self.poll(0)

    def set_tile(self, lane, col, value):
        self.cpu.memory[self.sym["tiles"] + lane * 24 + col] = value

    def check_memory(self):
        # CPU writes are allowed only in emitted data/buffers and a generous
        # 512-byte monitor stack area. ROM effects themselves are mocked.
        mutable = self.sym.get("data_start", self.sym["program_end"])
        end = self.sym["program_end"]
        actual = bytes(self.cpu.memory)
        for lo, hi in ((0, mutable), (end, 0x1E00), (0x1FF2, 65536)):
            assert actual[lo:hi] == self.baseline[lo:hi], f"Write outside RAM {lo:04X}:{hi:04X}"
        assert self.minimum_sp >= 0x1E00


class ProgramChecks(unittest.TestCase):
    def test_french_and_english_variants(self):
        for name, title in (("glyph_demo_FR", b"TEST DE MOTIFS"), ("glyph_demo_EN", b"GLYPH TEST")):
            m=Machine(name)
            self.assertIn(title,bytes(m.text[0]))
            m.tap(0x51)
            m.check_memory()
        for name in ("star_lane_FR","star_lane_EN"):
            m=Machine(name)
            for label, maximum in (("instructions_1",24),("instructions_2",24),("instructions_3",24),("pause_text",21),("over_text",24)):
                p=m.sym[label]
                length=bytes(m.cpu.memory[p:p+64]).index(0)
                self.assertLessEqual(length,maximum,(name,label))
            m.start()
            m.tap(0x39)
            expected=b"PAUSE" if name.endswith("FR") else b"PAUSED"
            self.assertIn(expected,bytes(m.text[2]))
            m.tap(0x02)
            m.check_memory()

    def test_title_and_custom_glyphs(self):
        m = Machine()
        self.assertIn(b"STAR LANE", bytes(m.text[0]))
        m.start()
        self.assertTrue(any(len(p[2]) == 120 for p in m.pattern_calls))
        self.assertTrue(any(p[2] == bytes.fromhex("143E7F1C08") for p in m.pattern_calls))
        self.assertTrue(any(p[2] == bytes.fromhex("0E1F3E1F0E") for p in m.pattern_calls))
        m.check_memory()

    def test_key_edges_limits_and_shift(self):
        m = Machine()
        m.start()
        m.tap(0x20)
        self.assertEqual(m.byte("player_lane"), 0)
        m.poll(0x20)  # held key: no new edge
        self.assertEqual(m.byte("player_lane"), 0)
        m.tap(0x20)  # upper bound
        self.assertEqual(m.byte("player_lane"), 0)
        m.tap(0x9F)  # shifted Down is still Down
        self.assertEqual(m.byte("player_lane"), 1)
        m.poll(0x1F)  # held after stripping shift
        self.assertEqual(m.byte("player_lane"), 1)
        m.tap(0x0A)  # S
        m.tap(0x1F)  # lower bound
        self.assertEqual(m.byte("player_lane"), 2)
        m.check_memory()

    def test_hits_grace_and_game_over(self):
        m = Machine()
        m.start()
        for expected in (2, 1, 0):
            m.set_byte("invulnerable", 0)
            m.set_tile(1, 3, 1)  # next shift collides at col 2
            m.next_world()
            self.assertEqual(m.byte("lives"), expected)
            self.assertEqual(m.byte("invulnerable"), 8)
            if expected:
                m.set_tile(1, 3, 1)
                m.next_world()
                self.assertEqual(m.byte("lives"), expected)
        self.assertEqual(m.byte("phase"), 2)
        self.assertIn(b"GAME OVER", bytes(m.text[2]))
        score = m.word("score")
        for _ in range(100):
            m.poll()
        self.assertEqual(m.word("score"), score)
        m.tap(0x28)
        self.assertEqual((m.byte("phase"), m.byte("lives"), m.word("score")), (1, 3, 0))
        m.check_memory()

    def test_stars_decimal_and_score_cap(self):
        m = Machine()
        m.start()
        m.set_tile(1, 3, 2)
        m.next_world()
        self.assertEqual(m.word("score"), 26)
        self.assertEqual(bytes(m.text[0][10:14]), b"0026")
        for value, expected in ((98, b"0099"), (998, b"0999"), (9998, b"9999"), (9999, b"9999")):
            m.set_word("score", value)
            m.next_world()
            self.assertEqual(bytes(m.text[0][10:14]), expected)
        m.check_memory()

    def test_pause_restart_and_return(self):
        m = Machine()
        m.start()
        m.next_world()
        m.tap(0x39)  # P
        self.assertEqual(m.byte("paused"), 1)
        frozen = (m.word("score"), bytes(m.cpu.memory[m.sym["tiles"]:m.sym["tiles"] + 72]))
        for _ in range(120):
            m.poll()
        self.assertEqual(frozen, (m.word("score"), bytes(m.cpu.memory[m.sym["tiles"]:m.sym["tiles"] + 72])))
        m.tap(0x20)  # ignored while paused
        self.assertEqual(m.byte("player_lane"), 1)
        m.tap(0x39)
        self.assertEqual(m.byte("paused"), 0)
        m.tap(0x05)  # R
        self.assertEqual((m.word("score"), m.byte("lives")), (0, 3))
        m.tap(0x02)  # Q
        self.assertEqual((m.cpu.pc, m.cpu.sp, m.cpu.ix, m.cpu.iy), (RETURN, 0x1FF2, 0x1234, 0x5678))
        m.check_memory()

    def test_long_game_shift_and_spawns(self):
        m = Machine()
        m.start()
        for _ in range(400):
            m.set_byte("invulnerable", 200)
            m.next_world()
            tiles = bytes(m.cpu.memory[m.sym["tiles"]:m.sym["tiles"] + 72])
            self.assertTrue(all(t in (0, 1, 2) for t in tiles))
            self.assertEqual(m.byte("phase"), 1)
        self.assertTrue(any(p[2] == bytes.fromhex("3E7763773E") or bytes.fromhex("3E7763773E") in p[2] for p in m.pattern_calls))
        m.check_memory()

    def test_glyph_demo(self):
        m = Machine("glyph_demo")
        self.assertEqual(len(m.pattern_calls), 3)
        self.assertEqual([(r, c) for r, c, _ in m.pattern_calls], [(1, 3), (1, 6), (1, 9)])
        m.tap(0x51)
        self.assertEqual((m.cpu.pc, m.cpu.sp), (RETURN, 0x1FF2))
        m.check_memory()


if __name__ == "__main__":
    parser=Parser("Vérifier Star Lane et le test de motifs, FR/EN (IOCS simulés).", "Check Star Lane and the glyph demo, FR/EN (mocked IOCS).")
    args=parser.parse_args()
    print(pick(args.lang,"Vérification des programmes Z80 ; aucun appareil connecté.","Z80 program checks; no hardware connected."),flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProgramChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "cpu_emulator": "z80 1.2.0", "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "passed": result.wasSuccessful(),
        "iocs": "mock contracts; NOT a Sharp ROM",
        "physical_g801_tested": False,
        "programs": json.loads((BUILD / "manifest.json").read_text())["programs"],
    }
    (BUILD / "cpu_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not result.wasSuccessful():
        raise SystemExit(1)
