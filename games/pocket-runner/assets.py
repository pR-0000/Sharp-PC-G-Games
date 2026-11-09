"""FR/EN: original Pocket Runner levels and 5x7 graphics, no imported assets."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
WIDTH,HEIGHT=20,12

def levels():
    result=[]
    for number,ladders in enumerate(((5,14,4),(14,5,15),(4,15,6))):
        cells=[0]*240
        for y in range(12):
            cells[y*20]=cells[y*20+19]=2
        for x in range(20):cells[220+x]=2
        for y in (2,5,8):
            for x in range(1,19):cells[y*20+x]=1
        for x,top,bottom in zip(ladders,(7,4,1),(10,7,4)):
            for y in range(top,bottom+1):cells[y*20+x]=3
        # Hanging routes / passages suspendus.
        for x in range(7,15):cells[3*20+x]=4
        for y in (3,4):cells[y*20+14]=3
        if number:
            for x in range(7,12):cells[4*20+x]=4
            for x in (8,9):cells[5*20+x]=0
        if number==2:
            for x in range(7,14):cells[7*20+x]=4
            for x in (9,10):cells[8*20+x]=0
            cells[9*20+10]=cells[9*20+11]=2
        for y in (0,1):cells[y*20+17]=7
        gold=[(3,10),(17,10),(3,7),(17,7),(3,4),(17,4),(10,3),(10,1)]
        if number==1:gold[6]=(10,4)
        if number==2:gold[2]=(10,7)
        guard=[17+20,17+4*20,17+7*20]
        spawn=2+10*20
        for x,y in gold:assert cells[y*20+x] not in (1,2),(number,x,y)
        result.append({'terrain':bytes(cells),'gold':[y*20+x for x,y in gold],
                       'guards':guard,'spawn':spawn,'exit':17})
    return result

def encode(data):
    pairs=[];i=0
    while i<len(data):
        j=i+1
        while j<len(data) and data[j]==data[i] and j-i<255:j+=1
        pairs.extend((j-i,data[i]));i=j
    return pairs+[0]

def generate():
    out=['; FR/EN: generated original levels, RLE count/value; zero terminator.',
         'level_table: dw level_0,level_1,level_2']
    for i,level in enumerate(levels()):
        out.extend((f'level_{i}:','    db '+','.join(map(str,[level['spawn'],level['exit'],*level['guards'],*level['gold']]))))
        data=encode(level['terrain'])
        for p in range(0,len(data),20):out.append('    db '+','.join(map(str,data[p:p+20])))
    sprites=[
        [0,0,0,0,0],                       # 0 air / vide
        [0x49,0x49,0x7f,0x49,0x49],         # 1 brick / brique
        [0x7f,0x55,0x6b,0x55,0x7f],         # 2 stone / pierre
        [0,0x7f,0x2a,0x7f,0],              # 3 ladder / echelle
        [2,2,2,2,2],                       # 4 rope / corde
        [8,28,62,28,8],                    # 5 gold / or
        [0x48,0x24,0x1f,0x24,0x48],         # 6 runner / coureur
        [8,100,31,36,72],                   # 7 running / course
        [0x52,0x6b,0x1f,0x6b,0x52],         # 8 guard / garde
        [0x70,0x5c,0x78,0x5c,0x70],         # 9 trapped / piege
        [14,31,62,31,14],                   # 10 heart / coeur
        [0x0a,0x24,0x1f,0x24,0x0a],         # 11 hanging / suspendu
    ]
    out.append('patterns:')
    for sprite in sprites:out.append('    db '+','.join(map(str,sprite)))
    out.extend(('bit_masks: db 1,2,4,8,16,32,64,128',
                'screen_rows: dw frame_buffer,frame_buffer+120,frame_buffer+240,frame_buffer+360'))
    (HERE/'generated.inc').write_text('\n'.join(out)+'\n',encoding='ascii')

if __name__=='__main__':generate()
