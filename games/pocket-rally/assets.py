"""FR/EN: original circuits, 4x4 tiles and 16-direction cars for Pocket Rally."""
from pathlib import Path
from math import sin,cos,pi,hypot
import sys,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT/'tools'))
from bitmap import read_bmp,write_bmp
W,H=48,32
ROUTES=(
    ((44,24),(144,24),(164,44),(164,84),(144,104),(44,104),(24,84),(24,44)),
    ((40,24),(140,24),(164,44),(164,88),(144,108),(108,108),(108,68),(72,68),(72,108),(40,108),(24,88),(24,40)),
)
PALETTE=((190,220,170),(255,255,255),(210,210,210),(170,170,170),(0,0,0),(240,80,60),(210,40,20),(255,210,0),(220,180,110),(60,150,220))
PATTERNS=((0,0,1,0),(0,0,0,0),(0,4,4,0),(0,0,6,0),(15,15,15,15),
          (5,10,5,10),(3,12,3,12),(5,10,5,10),(0,2,0,8),(4,5,4,5))

def segment_distance(x,y,p,q):
    dx,dy=q[0]-p[0],q[1]-p[1]
    t=max(0,min(1,((x-p[0])*dx+(y-p[1])*dy)/(dx*dx+dy*dy)))
    return hypot(x-p[0]-t*dx,y-p[1]-t*dy)

def default_track(index):
    route=ROUTES[index];cells=[]
    for y in range(H):
        for x in range(W):
            distances=[segment_distance(x*4+2,y*4+2,p,route[(i+1)%len(route)]) for i,p in enumerate(route)]
            distance=min(distances);i=distances.index(distance)
            horizontal=abs(route[(i+1)%len(route)][0]-route[i][0])>=abs(route[(i+1)%len(route)][1]-route[i][1])
            tile=1 if distance<10 else (5 if horizontal else 6) if distance<14 else 0
            if tile==1 and distance<1.5 and (x+y)%4==0:tile=2 if horizontal else 3
            if x in (0,W-1) or y in (0,H-1):tile=4
            elif distance>22 and ((x<12 and y<7) or (x>37 and y>25)):tile=9
            if abs(x*4+2-route[0][0])<=2 and abs(y*4+2-route[0][1])<10:tile=7
            cells.append(tile)
    return bytes(cells)

def track(index):
    path=HERE/f'track_{index+1:02}_layout.bmp'
    if not path.exists():write_bmp(path,W,H,[PALETTE[t] for t in default_track(index)])
    w,h,pixels=read_bmp(path)
    if (w,h)!=(W,H):raise ValueError('Circuit : BMP 48 x 32 requis / Track: 48 x 32 BMP required')
    try:return bytes(PALETTE.index(p) for p in pixels)
    except ValueError:raise ValueError('Circuit : couleurs de la palette uniquement / Track: palette colours only') from None

def car_patterns():
    # Nose points east. Original five-by-seven silhouette, rotated at build time.
    rows=('.......','.####..','#######','##.##.#','#######','.####..','.......')
    result=[]
    for angle in range(16):
        c,s=cos(angle*pi/8),sin(angle*pi/8);out=[]
        for x in range(7):
            value=0
            for y in range(7):
                xx=round((x-3)*c+(y-3)*s)+3;yy=round(-(x-3)*s+(y-3)*c)+3
                if 0<=xx<7 and 0<=yy<7 and rows[yy][xx]=='#':value|=1<<y
            out.append(value)
        result.append(out)
    return result

def generate():
    lines=['; FR/EN: original map and integer driving tables.']
    def emit(label,data,word=False):
        lines.append(label+':')
        for p in range(0,len(data),24):lines.append('    '+('dw ' if word else 'db ')+','.join(map(str,data[p:p+24])))
    for index in range(2):
        cells=track(index)
        lines.append(f'track_{index}: dw '+','.join(f'track_{index}_row_{y}' for y in range(H)))
        for y in range(H):
            row=cells[y*W:(y+1)*W];runs=[];x=0
            while x<W:
                end=x+1
                while end<W and end-x<16 and row[end]==row[x]:end+=1
                runs.append(((end-x-1)<<4)|row[x]);x=end
            emit(f'track_{index}_row_{y}',runs)
        emit(f'gates_{index}',[v for xy in ROUTES[index] for v in xy])
        lines.append(f'cars_initial_{index}:')
        x,y=ROUTES[index][0]
        for dx,dy in ((0,0),(8,-3),(16,3)):
            lines.extend((f'    dw {(x+dx)*16},{(y+dy)*16}','    db 0,0,1,0,0','    dw 0'))
        pixels=[(0,0,0) if PATTERNS[cells[(y//4)*W+x//4]][x%4]>>(y%4)&1 else (255,255,255) for y in range(H*4) for x in range(W*4)]
        write_bmp(HERE/f'track_{index+1:02}.bmp',W*4,H*4,pixels)
    columns=[v for tile in PATTERNS for v in tile]
    for phase in range(4):
        emit(f'tile_top_{phase}',[v>>phase for v in columns])
        emit(f'tile_mid_{phase}',[(v<<(4-phase))&127 for v in columns])
        if phase>=2:emit(f'tile_bot_{phase}',[(v<<(8-phase))&127 for v in columns])
    emit('tile_zero',[0]*40)
    lines.append('tile_phases:')
    for phase in range(4):lines.append(f'    dw tile_top_{phase},tile_mid_{phase},'+(f'tile_bot_{phase}' if phase>=2 else 'tile_zero'))
    emit('car_frames',[v for cols in car_patterns() for v in cols],True)
    outlines=[]
    for cols in car_patterns():
        for x,col in enumerate(cols):
            interior=col & (col<<1) & (col>>1) & (cols[x-1] if x else 0) & (cols[x+1] if x<6 else 0)
            outlines.append(col & ~interior)
    emit('rival_frames',outlines,True)
    emit('drive_table',[round(f(angle*pi/8)*speed*4)&255 for angle in range(16) for speed in range(8) for f in (cos,sin)])
    emit('look_x',[round(12*cos(a*pi/8))&255 for a in range(16)])
    emit('look_y',[round(10*sin(a*pi/8))&255 for a in range(16)])
    lines.extend(('track_maps: dw track_0,track_1','track_gates: dw gates_0,gates_1','track_starts: dw cars_initial_0,cars_initial_1',
                  'gate_counts: db 8,12','buffer_rows: dw frame_buffer,frame_buffer+120,frame_buffer+240,frame_buffer+360'))
    (HERE/'generated.inc').write_text('\n'.join(lines)+'\n',encoding='ascii')
    (HERE/'tracks.json').write_text(json.dumps({'tile_size':4,'width':W,'height':H,'palette':[{'id':i,'rgb':c} for i,c in enumerate(PALETTE)],
       'tracks':[{'fr':fr,'en':en,'checkpoints':r} for fr,en,r in zip(('Boucle cotiere','Chicane du port'),('Coast loop','Harbour chicane'),ROUTES)]},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':generate()
