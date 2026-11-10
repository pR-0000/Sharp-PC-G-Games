"""Measure the real Z80 floor kernel and compare every pixel to the reference.

Requires SjASMPlus and z80==1.2.0. No Sharp ROM or firmware bytes are used.
Cycle counts exclude row-table preparation, LCD transfers, gameplay and IRQs.
"""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

import z80
import reference

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build import read_symbols
from cli_i18n import Parser,pick


def compile_kernel(assembler,folder,step,row_step=1):
    base=folder/f'floor_{step}x{row_step}'
    subprocess.run([assembler,'--nologo','--color=off',f'-DPIXEL_STEP={step}',f'-DROW_STEP={row_step}',
        f'--inc={(ROOT/"include").as_posix()}',f'--raw={base.as_posix()}.bin',
        f'--sym={base.as_posix()}.sym',(HERE/'floor_kernel.asm').as_posix()],check=True,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    return base.with_suffix('.bin').read_bytes(),read_symbols(base.with_suffix('.sym'))


def execute(binary,image,rows):
    cpu=z80.Z80Machine()
    cpu.memory[:]=bytes([0xA5])*65536
    cpu.memory[0x100:0x100+len(binary)]=binary
    cpu.memory[0x4000:0x4800]=image
    cpu.memory[0x4800:0x4808]=bytes([128,64,32,16,8,4,2,1])
    row_data=reference.packed_rows(rows)
    cpu.memory[0x5000:0x5000+len(row_data)]=row_data
    cpu.pc=0x100;cpu.sp=0x7E00
    cpu.memory[0x7E00:0x7E02]=bytes([0,0x70])
    before=bytes(cpu.memory)
    cpu.set_breakpoint(0x7000)
    def unexpected(*args):raise AssertionError('Kernel touched an I/O port')
    cpu.set_input_callback(unexpected);cpu.set_output_callback(unexpected)
    cycles=0
    for _ in range(100):
        cpu.ticks_to_stop=60000
        cpu.run()
        cycles+=60000-cpu.ticks_to_stop
        if cpu.pc==0x7000:break
    else:raise AssertionError(f'Kernel CPU timeout at {cpu.pc:04X}')
    assert cpu.sp==0x7E02
    # Only code-local loop state and the destination framebuffer may change.
    for first,last in ((0,0x100),(0x100+len(binary),0x6000),(0x6360,65536)):
        assert bytes(cpu.memory[first:last])==before[first:last],(first,last)
    return bytes(cpu.memory[0x6000:0x6360]),cycles


def main():
    parser=Parser('Mesurer le noyau Z80 de projection au sol.',
                  'Measure the Z80 planar floor-projection kernel.')
    parser.add_argument('--assembler',default=os.environ.get('SJASMPLUS','sjasmplus'))
    parser.add_argument('--output',type=Path,default=ROOT/'.local/pocket-vector')
    args=parser.parse_args()
    assembler=shutil.which(args.assembler)
    if not assembler:parser.error('SjASMPlus: --assembler / SJASMPLUS / PATH')
    args.output.mkdir(parents=True,exist_ok=True)
    texture,_=reference.build_track()
    report={'hardware_measured':False,'row_tables_prepared_on_host':True,
            'excluded':['row table generation','LCD transfer','gameplay','interrupts'],
            'framebuffer_bytes':864,'texture_bytes':2048,'modes':[]}
    for step,row_step in ((1,1),(2,1),(2,2)):
        binary,symbols=compile_kernel(assembler,args.output,step,row_step)
        counts=[]
        for index in range(0,320,20):
            rows=reference.rows_for(reference.camera(index),step,row_step)
            actual,cycles=execute(binary,texture,rows)
            expected=reference.reference_floor(texture,rows,step,row_step)
            assert actual==expected,(step,row_step,index)
            counts.append(cycles)
        # Exercise every heading, subpixel origins and negative coordinate steps.
        import math
        for phase in range(64):
            angle=phase*2*math.pi/64
            pose=(63.125,60.875,math.cos(angle),math.sin(angle))
            rows=reference.rows_for(pose,step,row_step)
            actual,_=execute(binary,texture,rows)
            assert actual==reference.reference_floor(texture,rows,step,row_step),(step,row_step,phase)
        mode={'sample_step':step,'row_step':row_step,'kernel_bytes':len(binary),'frames_checked':80,
              'samples_per_frame':144//step*(32//row_step),'cycles_min':min(counts),
              'cycles_max':max(counts),'cycles_mean':round(sum(counts)/len(counts))}
        report['modes'].append(mode)
        print(json.dumps(mode),flush=True)
        rows=reference.rows_for(reference.camera(20),step,row_step)
        actual,_=execute(binary,texture,rows)
        reference.save_png(args.output/f'z80_{step}x{row_step}.png',reference.compose(actual,20,args.lang))
    (args.output/'benchmark.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(pick(args.lang,'Projection Z80 conforme sur 240 images.','Z80 projection matches all 240 frames.'),flush=True)


if __name__=='__main__':main()
