"""FR: vérifier une ROM G805 privée. EN: check a private G805 ROM.

Executes the supplied ROM, never distributes ROM bytes. LCD/connector are
software models, not electrical validation. Font lookup is intercepted only
for reset/text tests when bank 04 was not dumped; this is reported explicitly.
Requires z80==1.2.0. Run with --rom-dir PATH [--lang fr|en].
"""
from pathlib import Path
import hashlib
import json
import sys
import unittest

import z80

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from cli_i18n import Parser, pick

HASHES = (
    'ad26e4b417efd2b98e47f60bca495690ab2ff888a81568f31183bd74df790777',
    'c2a23ed2dde5f68d13b802cbc1d1a0aa0e6f698cacd3b1bb18e2b658bb7e48de',
    '401fc14d4f500fadfbdcb710416088512cbaf958fcd9811aaa3f22b3edd36ea7',
    '11014385883a4373c6de464943eb07dd3b0eb1ae26a1a9698b15fadcee3a9078',
)
ROM_DIR = None


class RomMachine:
    RETURN = 0x0080

    def __init__(self):
        self.banks = [(ROM_DIR / f'banks/bank{i:02x}.bin').read_bytes() for i in range(4)]
        self.fixed = (ROM_DIR / 'fixed.bin').read_bytes()
        for data, digest in zip(self.banks, HASHES):
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Unknown ROM profile / Profil ROM inconnu')
        assert self.fixed == self.banks[0]
        extra = ROM_DIR / 'banks/bank04.bin'
        if extra.exists():
            data = extra.read_bytes()
            assert len(data) == 16384
            self.banks.append(data)
        self.cpu = z80.Z80Machine()
        self.ram = bytearray(8192)
        self.bank = 3
        self.ports = {0x15: 0, 0x18: 0}
        self.outputs = []
        self.inputs = []
        self.connector = lambda: 0x02  # CS ready, no BREAK, receive idle
        self.lcd = [bytearray(64) for _ in range(8)]
        self.x = self.y = 0
        self.latch = False
        self.text = []
        self.cpu.memory[0x8000:0xc000] = self.fixed
        self.cpu.set_read_callback(self.read)
        self.cpu.set_write_callback(self.write)
        self.cpu.mark_addrs(0, 0x8000, self.cpu.READ_MARK | self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0x8000, 0x8000, self.cpu.WRITE_MARK)
        self.cpu.mark_addrs(0xc000, 0x4000, self.cpu.READ_MARK)
        self.cpu.set_input_callback(self.input)
        self.cpu.set_output_callback(self.output)
        self.cpu.set_breakpoint(self.RETURN)
        self.write(0x7900, self.bank)

    def read(self, address):
        if address < 0x8000:
            return self.ram[address & 0x1fff]
        if address < 0xc000:
            return self.fixed[address - 0x8000]
        if self.bank >= len(self.banks):
            raise ValueError(f'Missing bank / Banque absente : {self.bank:02X}')
        return self.banks[self.bank][address - 0xc000]

    def write(self, address, value):
        assert address < 0x8000, f'ROM write {address:04X}'
        self.ram[address & 0x1fff] = value

    def block(self, address, data):
        for i, value in enumerate(data):
            self.write(address + i, value)

    def input(self, port):
        port &= 255
        self.inputs.append((port, self.cpu.pc))
        if port == 0x59:
            return 0  # LCD ready
        if port == 0x5b:
            if not self.latch:
                self.latch = True
                return 0  # mandatory dummy read after address selection
            value = self.lcd[self.y][self.x]
            self.x = (self.x + 1) & 63
            return value
        if port == 0x19:
            return self.bank
        if port == 0x1f:
            return self.connector()
        return self.ports.get(port, 0)

    def output(self, port, value):
        port &= 255
        self.outputs.append((port, value))
        self.ports[port] = value
        if port == 0x19:
            self.bank = value & 15  # never guess modulo aliases for missing ROM
        elif port == 0x58:
            self.latch = False
            if value & 0xc0 == 0x40:
                self.x = value & 63
            elif value & 0xc0 == 0x80:
                self.y = value & 7
        elif port == 0x5a:
            self.lcd[self.y][self.x] = value & 0x7f
            self.x = (self.x + 1) & 63
            self.latch = False

    def ret(self):
        c = self.cpu
        c.pc = self.read(c.sp) | self.read(c.sp + 1) << 8
        c.sp += 2

    def call(self, address, capture_chars=False, **registers):
        c = self.cpu
        c.sp = 0x1ee0
        self.block(c.sp, self.RETURN.to_bytes(2, 'little'))
        for register, value in registers.items():
            setattr(c, register, value)
        c.pc = address
        if capture_chars:
            c.set_breakpoint(0x8468)
        for _ in range(200):
            c.ticks_to_stop = 100000
            c.run()
            if c.pc == self.RETURN:
                if capture_chars:
                    c.clear_breakpoint(0x8468)
                assert c.sp == 0x1ee2
                return
            if capture_chars and c.pc == 0x8468:
                self.text.append((c.d, c.e, c.a))
                self.ret()  # only font rendering; all callers execute actual ROM
        raise AssertionError(f'Routine timeout / Délai dépassé : {c.pc:04X}')

    def row(self, row):
        # Logical row -> two halves, right half stored backwards.
        return bytes(self.lcd[row][:60]) + bytes(reversed(self.lcd[row + 4][:60]))


class NativeRomTests(unittest.TestCase):
    def setUp(self):
        self.m = RomMachine()

    def test_ram_is_mirrored_and_unknown_banks_are_not_fabricated(self):
        m = self.m
        m.write(0x78ed, 16)
        self.assertEqual(m.read(0x18ed), 16)
        self.assertEqual(m.read(0x38ed), 16)
        m.bank = 15
        with self.assertRaises(ValueError):
            m.read(0xc000)

    def test_all_reset_changes_characters_not_a_contrast_port(self):
        m = self.m
        m.write(0x7964, 0x80)
        m.block(0x7ffd, b'\0\0')
        m.block(0x7f40, bytes(range(45)))
        m.call(0xbd39, capture_chars=True)
        self.assertEqual(sum(a == 0x87 for d, e, a in m.text), 50)
        self.assertEqual(bytes(a for d, e, a in m.text if a != 0x87), b'ALL RESET')
        self.assertFalse(m.outputs)  # glyph lookup is intercepted, no other I/O
        m.text.clear()
        m.call(0xbd39, capture_chars=True)
        self.assertEqual(len(m.text), 96)
        self.assertEqual({a for d, e, a in m.text}, {32})
        self.assertEqual(m.row(1)[35:80], bytes(range(45)))
        self.assertEqual({p for p, v in m.outputs}, {0x58, 0x5a})
        self.assertTrue(all(v & 0xc0 in (0x40, 0x80) for p, v in m.outputs if p == 0x58))

    def test_pattern_round_trip_full_width_and_right_half(self):
        m = self.m
        pattern = bytes(i % 128 for i in range(120))
        m.block(0x0200, pattern)
        m.call(0xbfd0, hl=0x200, b=120, de=0x0200)
        self.assertEqual(m.row(2), pattern)
        m.call(0xbd00, hl=0x300, b=120, de=0x0200)
        self.assertEqual(bytes(m.ram[0x300:0x378]), pattern)
        m.call(0xbfd0, hl=0x200, b=25, de=0x0313)
        self.assertEqual(m.row(3)[95:], pattern[:25])

    def test_counted_string_wraps_using_real_callers(self):
        m = self.m
        m.block(0x200, b'ABCDE')
        m.call(0xbff1, capture_chars=True, hl=0x200, b=5, de=0x0016)
        self.assertEqual(m.text, [(0,22,65),(0,23,66),(1,0,67),(1,1,68),(1,2,69)])

    def test_repeat_stops_at_bottom_without_scrolling(self):
        m = self.m
        m.call(0xbfee, capture_chars=True, a=65, b=5, de=0x0316)
        self.assertEqual(m.text, [(3,22,65),(3,23,65)])

    def test_lcd_start_line_and_enable_do_not_write_pixels(self):
        m = self.m
        m.write(0x790d, 3)
        m.call(0xbfd3)
        self.assertEqual(m.outputs, [(0x58, 0xd8),(0x58,0x3f)])
        self.assertEqual(m.read(0x790d), 3)

    def test_serial_open_close(self):
        m = self.m
        m.ports[0x15] = 0x41
        m.call(0xbce8, af=0x5a45, bc=0x1234)
        self.assertEqual(m.cpu.af, 0x5a45)
        self.assertEqual(m.cpu.bc, 0x1234)
        self.assertEqual(m.outputs, [(0x18,0),(0x18,2),(0x15,0xc0)])
        m.call(0xbceb)
        self.assertEqual(m.outputs[-2:], [(0x15,0x40),(0x18,0)])

    def test_transmit_7_and_8_bits_and_parity(self):
        for bits in (7,8):
            for parity in ('N','E','O'):
                with self.subTest(bits=bits, parity=parity):
                    m = RomMachine()
                    m.write(0x78ed, 0x10)  # 4800 baud
                    m.write(0x78ee, (0x80 if bits==8 else 0) | {'N':0,'E':0x60,'O':0x40}[parity])
                    m.call(0xbfaf, a=0xa5, bc=0x1234, de=0x5678, hl=0xabcd)
                    values = [v for p,v in m.outputs if p==0x18]
                    data = 0xa5 & ((1 << bits)-1)
                    expected = [0x82]+[2 | (0x80 if not (data >> bit & 1) else 0) for bit in range(bits)]
                    if parity!='N':
                        bit = data.bit_count() % 2 ^ (parity=='O')
                        expected.append(2 | (0 if bit else 0x80))
                    expected.append(2)
                    self.assertEqual(values, expected)
                    self.assertFalse(m.cpu.f & 1)
                    self.assertEqual((m.cpu.bc,m.cpu.de,m.cpu.hl),(0x1234,0x5678,0xabcd))

    def test_receive_formats_parity_error_and_raw_bytes(self):
        for bits in (7,8):
            for parity in ('N','E','O'):
                for bad_parity in ((False,) if parity=='N' else (False,True)):
                    with self.subTest(bits=bits,parity=parity,bad=bad_parity):
                        m = RomMachine()
                        value = 0xa5 & ((1 << bits)-1)
                        m.write(0x78ed,0x10)
                        m.write(0x78ee,(0x80 if bits==8 else 0) | {'N':0,'E':0x60,'O':0x40}[parity])
                        m.write(0x78ec,0x10)
                        samples = [4,4,4]+[0 if value >> i & 1 else 4 for i in range(bits)]
                        if parity!='N':
                            bit = value.bit_count() % 2 ^ (parity=='O') ^ bad_parity
                            samples.append(0 if bit else 4)
                        samples = iter(samples)
                        m.connector = lambda: next(samples,0)
                        m.call(0xbce2,bc=0x1234,de=0x5678,hl=0xabcd)
                        self.assertEqual((m.cpu.a,m.cpu.f & 1),(2,1) if bad_parity else (value,0))
                        self.assertEqual((m.cpu.bc,m.cpu.de,m.cpu.hl),(0x1234,0x5678,0xabcd))
        for value in (0,10,13,26,255):
            m = RomMachine()
            m.write(0x78ed,0x10);m.write(0x78ee,0x80);m.write(0x78ec,0x10);m.write(0x78ef,26)
            samples = iter([4,4,4]+[0 if value >> i & 1 else 4 for i in range(8)])
            m.connector = lambda: next(samples,0)
            m.call(0xbce2)
            self.assertEqual((m.cpu.a,m.cpu.f & 1),(value,0))
            self.assertEqual(bool(m.read(0x78ec) & 0x80),value==26)

    def test_receive_invalid_stop_returns_error_one(self):
        m = self.m
        m.write(0x78ed,0x10);m.write(0x78ee,0x80);m.write(0x78ec,0x10)
        m.connector = lambda: 4  # line never returns to idle
        m.call(0xbce2)
        self.assertEqual((m.cpu.a,m.cpu.f & 1),(1,1))

    def test_new_include_matches_verified_native_entry_points(self):
        import re
        text = (ROOT/'include/sharp-pc-g8xx.inc').read_text(encoding='utf-8')
        defs = {name:int(value,16) for name,value in re.findall(r'^(\w+)\s+EQU\s+0x([0-9a-fA-F]+)',text,re.M)}
        targets = {'PATTERN_READ':0x8620,'SIO_OPEN':0x8db9,'SIO_CLOSE':0x8dd7,
                   'SIO_RX':0x8fb6,'SIO_RX_NEXT':0x8fba,'SIO_TX':0x8f9c,
                   'SIO_PUTS':0x8e94,'SIO_NEWLINE':0x9211,'LCD_ENABLE':0x86ec,
                   'PATTERN':0x8687,'PUTC':0x8468,'PUTC_CTRL':0x843a,'STRING':0x84cd,'REPEAT':0x86b3}
        for name,target in targets.items():
            address = defs['PCG_IOCS_'+name]
            self.assertEqual(self.m.read(address),0xc3)
            self.assertEqual(self.m.read(address+1) | self.m.read(address+2) << 8,target)

    def test_serial_break_and_wait_for_cs(self):
        m = self.m
        polls = iter((0,0,0,0x80))
        m.connector = lambda: next(polls,0x80)
        m.call(0xbfaf, a=65)
        self.assertEqual((m.cpu.a,m.cpu.f & 1),(0,1))
        self.assertFalse(m.outputs)
        self.assertEqual(m.read(0x7f35) & 0x20, 0x20)
        m.call(0xbce2)
        self.assertEqual((m.cpu.a,m.cpu.f & 1),(0,1))
        self.assertEqual(m.outputs[-1], (0x18,0))

    def test_serial_newline_builder(self):
        m = self.m
        for flags, expected in ((0,b'\r\n'),(1,b'\n'),(4,b'\r')):
            m.write(0x78ee, flags)
            m.call(0xbcee, hl=0x200)
            self.assertEqual(bytes(m.ram[0x200:m.cpu.hl]), expected)

    def test_banked_beep_and_break_restore_bank_stack_and_registers(self):
        for count, pitch, cycles, brk in ((0,7,4,False),(1,7,4,False),(2,20,3,False),(2,7,0,False),(1,7,4,True)):
            with self.subTest(count=count,pitch=pitch,cycles=cycles,brk=brk):
                m = RomMachine()
                # A callable six-byte trampoline: the gate returns to its CALLER,
                # not to the inline bank/address descriptor.
                m.block(0x200, bytes.fromhex('cd4992011fe7'))
                m.ports[0x18] = 3
                m.connector = lambda: 0x80 if brk else 0
                m.call(0x200,a=pitch,bc=cycles,de=count,hl=0xabcd)
                sound = [v for p,v in m.outputs if p==0x18]
                self.assertEqual(sound[-1], 3)
                self.assertEqual(sum(v==0xc3 for v in sound), count*cycles if not brk else 1)
                self.assertEqual((m.cpu.bc,m.cpu.de,m.cpu.hl),(cycles,count,0xabcd))
                self.assertEqual((m.bank,m.read(0x7900)),(3,3))
                # The outer BEEP cleanup executes AND 3F, clearing carry even
                # when BREAK aborted the inner tone. Do not expose carry as status.
                self.assertFalse(m.cpu.f & 1)


def main():
    global ROM_DIR
    parser = Parser('Vérifier les routines de la ROM G805 privée.', 'Check routines in a private G805 ROM.')
    parser.add_argument('--rom-dir', type=Path, required=True)
    args = parser.parse_args()
    ROM_DIR = args.rom_dir
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeRomTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    note = pick(args.lang,
                'ROM exécutée ; LCD et signaux série simulés. ALL RESET : rendu des glyphes intercepté, branchement ROM réel.',
                'ROM executed; LCD and serial signals modeled. ALL RESET: glyph rendering intercepted, real ROM control flow.')
    print(note)
    raise SystemExit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
