"""G850 public IOCS and settled keyboard matrix for actual distributed Z80 code."""
from check_programs import Machine,IOCS,RETURN


class G850Machine(Machine):
    width=144
    rows=6
    cell_width=6
    pixel_mask=255
    stack=0x76C0
    stack_bottom=0x7600

    def __init__(self,name,build_dir):
        self.tstates=0;self.keys=();self.strobe=self.pending=0;self.strobe_at=-1000
        self.inputs=[];self.outputs=[]
        super().__init__(name,build_dir)
        assert self.sym['program_end']<=0x7000
        self.cpu.set_input_callback(self.input_port)
        self.cpu.set_output_callback(self.output_port)

    def now(self):return self.tstates+60000-self.cpu.ticks_to_stop
    def settle(self):
        if self.now()-self.strobe_at>=130:self.strobe=self.pending
    def input_port(self,port):
        if port&255==0x1F:return 128 if 0x51 in self.keys else 0
        assert port&255==0x10,('Unexpected IN',port)
        self.settle();self.inputs.append(self.strobe)
        value=0
        for key in self.keys:
            if 1<=key<=80 and self.strobe&(1<<((key-1)//8)):value|=1<<((key-1)%8)
        return value
    def output_port(self,port,value):
        port&=255;assert port in (0x11,0x12),('Unexpected OUT',port,value)
        self.outputs.append((port,value));self.settle()
        self.pending=value if port==0x11 else value<<8
        self.strobe|=self.pending;self.strobe_at=self.now()

    def seek_key(self):
        for _ in range(1000):
            self.cpu.ticks_to_stop=60000;self.cpu.run()
            self.tstates+=60000-self.cpu.ticks_to_stop
            if self.cpu.pc in (0xBE53,RETURN):return
            if self.cpu.pc in IOCS:self.rom_return()
        raise AssertionError(f'CPU did not yield {self.cpu.pc:04X}')
    def poll(self,key=0):
        self.keys=tuple(key) if isinstance(key,(tuple,list,set)) else (key,) if key else ()
        raw=0x51 if 0x51 in self.keys else 0x52 if len(self.keys)>1 else self.keys[0] if self.keys else 0
        super().poll(raw)
    def rom_return(self,key=None):
        if self.cpu.pc==0xBFD0:
            row,col,width=self.cpu.d,self.cpu.e,self.cpu.b
            cells=(width+self.cell_width-1)//self.cell_width
            self.text[row][col:col+cells]=b' '*cells
        super().rom_return(key)
    def routine(self,name,**registers):
        context={r:getattr(self.cpu,r) for r in ('pc','sp','af','bc','de','hl','ix','iy')}
        stack=bytes(self.cpu.memory[self.stack_bottom:self.stack+2])
        try:
            self.cpu.pc,self.cpu.sp=self.sym[name],self.stack
            self.cpu.memory[self.stack:self.stack+2]=RETURN.to_bytes(2,'little')
            for key,value in registers.items():setattr(self.cpu,key,value)
            self.seek_key();assert self.cpu.pc==RETURN,name
            return {r:getattr(self.cpu,r) for r in ('af','bc','de','hl','ix','iy')}
        finally:
            self.cpu.memory[self.stack_bottom:self.stack+2]=stack
            for key,value in context.items():setattr(self.cpu,key,value)

    def pixels(self):
        p=self.sym['frame_buffer'];return bytes(self.cpu.memory[p:p+864])
