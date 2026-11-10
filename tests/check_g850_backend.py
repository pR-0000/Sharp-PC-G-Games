"""FR/EN: assemble the G850 include and execute register-preserving IOCS wrappers.

Optional development check, using z80==1.2.0 and SjASMPlus, no Sharp ROM.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

import z80

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import read_symbols
from cli_i18n import Parser

ASSEMBLER=None
RETURN=0x7000


class G850BackendChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='sharp-g850-check-')
        cls.folder=Path(cls.temp.name)
        source=cls.folder/'backend.asm'
        source.write_text('''    org 0x100
    include "sharp-pc-g8xx.inc"
    include "sharp_pc_g850.inc"
    assert $ == 0x100
    assert PCG_LCD_ROWS * PCG_ROW_COLUMNS == 480
    ret
    include "pcg850_runtime.asm"
''',encoding='ascii')
        subprocess.run([ASSEMBLER,'--nologo','--color=off',
            f'--inc={(ROOT/"include").as_posix()}',f'--inc={(ROOT/"lib").as_posix()}',
            f'--raw={(cls.folder/"backend.bin").as_posix()}',
            f'--sym={(cls.folder/"backend.sym").as_posix()}',source.as_posix()],
            check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        cls.binary=(cls.folder/'backend.bin').read_bytes()
        cls.symbols=read_symbols(cls.folder/'backend.sym')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def run_wrapper(self,name,key=0):
        cpu=z80.Z80Machine()
        cpu.memory[:]=bytes([0xA5])*65536
        cpu.memory[0x100:0x100+len(self.binary)]=self.binary
        frame=bytes((x*41+255)&255 for x in range(864))
        cpu.memory[0x6000:0x6360]=frame
        cpu.pc=self.symbols[name];cpu.sp=0x7E00
        cpu.memory[0x7E00:0x7E02]=RETURN.to_bytes(2,'little')
        cpu.af=0x1234;cpu.bc=0x5678;cpu.de=0x9ABC;cpu.hl=0x6000;cpu.ix=0x1357;cpu.iy=0x2468
        registers={n:getattr(cpu,n) for n in ('af','bc','de','hl','ix','iy')}
        before=bytes(cpu.memory)
        calls=[]
        for address in (0xBE53,0xBE62,0xBFD0,0xBFEE,RETURN):cpu.set_breakpoint(address)
        for _ in range(100):
            cpu.ticks_to_stop=60000;cpu.run()
            if cpu.pc==RETURN:break
            if cpu.pc in (0xBE53,0xBE62,0xBFD0,0xBFEE):
                calls.append((cpu.pc,cpu.a,cpu.b,cpu.d,cpu.e,bytes(cpu.memory[cpu.hl:cpu.hl+cpu.b])))
                target=cpu.memory[cpu.sp]+256*cpu.memory[cpu.sp+1]
                cpu.sp+=2;cpu.pc=target
                for n in registers:setattr(cpu,n,0xCCCC)
                if calls[-1][0]==0xBE53:cpu.a=key
        else:self.fail('Wrapper CPU timeout')
        self.assertEqual(cpu.sp,0x7E02)
        for n,value in registers.items():
            if name!='pcg850_key_scan' or n!='af':self.assertEqual(getattr(cpu,n),value,n)
        self.assertEqual(bytes(cpu.memory[:0x7DA0]),before[:0x7DA0])
        self.assertEqual(bytes(cpu.memory[0x7E00:]),before[0x7E00:])
        return calls,cpu,frame

    def test_include_emits_no_bytes_and_coexists_with_the_g805_include(self):
        self.assertEqual(self.binary[0],0xC9)
        for name,value in [('PCG850_LCD_WIDTH',144),('PCG850_LCD_HEIGHT',48),
                           ('PCG850_FRAME_BYTES',864),('PCG850_PIXEL_MASK',255),
                           ('PCG850_PORT_LCD_COMMAND',0x40),('PCG850_PORT_LCD_DATA',0x41),
                           ('PCG850_PORT_ROM_BANK',0x69)]:
            self.assertEqual(self.symbols[name],value)
        self.assertNotIn('PCG850_RAM_ROM_BANK',self.symbols)
        self.assertNotIn('PCG850_IOCS_SIO_TX',self.symbols)

    def test_blit_sends_864_bytes_across_exactly_six_visible_rows(self):
        calls,cpu,frame=self.run_wrapper('pcg850_blit')
        self.assertEqual(len(calls),6)
        for row,call in enumerate(calls):
            self.assertEqual((call[0],call[2],call[3],call[4]),(0xBFD0,144,row,0))
            self.assertEqual(call[5],frame[row*144:(row+1)*144])

    def test_clear_uses_24_characters_per_row_and_preserves_registers(self):
        calls,_,_=self.run_wrapper('pcg850_clear')
        self.assertEqual([(c[0],c[1],c[2],c[3],c[4]) for c in calls],
                         [(0xBFEE,32,24,row,0) for row in range(6)])

    def test_scan_masks_shift_and_reports_no_key_with_z_flag(self):
        for value in (0,0xA0):
            calls,cpu,_=self.run_wrapper('pcg850_key_scan',value)
            self.assertEqual(len(calls),1)
            self.assertEqual(cpu.a,value&127)
            self.assertEqual(bool(cpu.f&64),not bool(value&127))

    def test_character_output_preserves_the_caller_registers(self):
        calls,_,_=self.run_wrapper('pcg850_putc')
        self.assertEqual(len(calls),1)
        self.assertEqual(calls[0][0],0xBE62)


if __name__=='__main__':
    parser=Parser('Verifier les definitions et wrappers IOCS G850.',
                  'Check G850 definitions and IOCS wrappers.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    args=parser.parse_args();ASSEMBLER=shutil.which(args.assembler)
    if not ASSEMBLER:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    unittest.main(argv=[sys.argv[0]],verbosity=2)
