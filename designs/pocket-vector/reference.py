"""Original planar track renderer; concept artwork, not a complete Sharp game.

FR/EN: 128x128 1bpp world, Q8.8 scanline coordinates, native G850 page packing.
Only standard Python is required. The Z80 kernel consumes the same row data.
"""
from pathlib import Path
import math
import struct
import sys
import zlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from bitmap import write_bmp
from cli_i18n import Parser,pick

WIDTH,HEIGHT=144,48
FOCAL,CAMERA_HEIGHT,HORIZON=70.0,3.0,3.0
# World units: 11-wide usable road, up from 7.8; borders are outside this area.
ROAD_HALF_WIDTH,BORDER_WIDTH=5.5,1.0
NODES=((29,19),(75,17),(106,39),(100,87),(78,109),(41,102),(19,75),(21,43))
FONT={
 ' ':('00000',)*7,
 'V':('10001','10001','10001','10001','10001','01010','00100'),
 'I':('11111','00100','00100','00100','00100','00100','11111'),
 'T':('11111','00100','00100','00100','00100','00100','00100'),
 'L':('10000','10000','10000','10000','10000','10000','11111'),
 '0':('01110','10001','10011','10101','11001','10001','01110'),
 '1':('00100','01100','00100','00100','00100','00100','01110'),
 '2':('01110','10001','00001','00010','00100','01000','11111'),
 '3':('11110','00001','00001','01110','00001','00001','11110'),
 '4':('00010','00110','01010','10010','11111','00010','00010'),
 '5':('11111','10000','10000','11110','00001','00001','11110'),
 '6':('01110','10000','10000','11110','10001','10001','01110'),
 '7':('11111','00001','00010','00100','01000','01000','01000'),
 '8':('01110','10001','10001','01110','10001','10001','01110'),
 '9':('01110','10001','10001','01111','00001','00001','01110'),
 '/':('00001','00010','00010','00100','01000','01000','10000'),
}
# Original rear-view hovercraft: broad hull, cockpit and twin engines.
# Inspired by QL-Zero's readable rear silhouettes; no QL pixels are imported.
SHIP=('........###........','......##...##......','....###.###.###....',
      '.####.........####.','##..##.#####.##..##','##...###...###...##',
      '###..#########..###','.##..##.....##..##.','..#####.###.#####..',
      '...###.......###...','....#.........#....')


def centreline():
    points=[]
    for i in range(len(NODES)):
        a,b,c,d=(NODES[(i+j)%len(NODES)] for j in (-1,0,1,2))
        for n in range(40):
            t=n/40
            points.append(tuple(.5*((2*b[k])+(-a[k]+c[k])*t+
                (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1)))
    return points


def build_track(half_width=ROAD_HALF_WIDTH):
    if not 1<=half_width<=12:
        raise ValueError('Road half-width must be between 1 and 12 world units.')
    points=centreline()
    image=bytearray(2048)
    road=bytearray(2048)
    for y in range(128):
        for x in range(128):
            index,distance=min(enumerate((x-px)**2+(y-py)**2 for px,py in points),key=lambda pair:pair[1])
            inside=distance<half_width**2
            black=((x//4+y//4)&1)==0
            if distance<(half_width+BORDER_WIDTH)**2:
                black=not inside
                if inside and (index<3 or index>317):black=((x//2+y//2)&1)==0
                if inside and 110<index<118:black=(x+2*y)%4==0
            offset=y*16+x//8;mask=128>>(x&7)
            if black:image[offset]|=mask
            if inside:road[offset]|=mask
    return bytes(image),bytes(road)


def camera(index=20):
    points=centreline();n=len(points);index%=n
    px,py=points[index]
    dx=points[(index+2)%n][0]-points[(index-2)%n][0]
    dy=points[(index+2)%n][1]-points[(index-2)%n][1]
    phase=round(math.atan2(dy,dx)*64/(2*math.pi))%64
    angle=phase*2*math.pi/64
    fx,fy=math.cos(angle),math.sin(angle)
    return px-5*fx,py-5*fy,fx,fy


def rows_for(pose,step=2,row_step=1,bottom=40):
    cx,cy,fx,fy=pose;rx,ry=-fy,fx
    rows=[]
    for y in range(8,bottom,row_step):
        distance=CAMERA_HEIGHT*FOCAL/(y+row_step/2-HORIZON)
        left=-(WIDTH/2-step/2)*distance/FOCAL
        values=(cx+fx*distance+rx*left,cy+fy*distance+ry*left,
                rx*distance/FOCAL*step,ry*distance/FOCAL*step)
        rows.append(tuple(round(value*256)&65535 for value in values))
    return rows


def packed_rows(rows):return b''.join(struct.pack('<4H',*row) for row in rows)


def sample_texture(image,u,v):
    x=(u>>8)&127;y=(v>>8)&127
    return bool(image[y*16+x//8]&(128>>(x&7)))


def reference_floor(image,rows,step=2,row_step=1):
    frame=bytearray(864)
    for index,(u,v,du,dv) in enumerate(rows):
        y=8+index*row_step
        for x in range(0,WIDTH,step):
            if sample_texture(image,u,v):
                mask=((1<<row_step)-1)<<(y&7)
                for extra in range(step):frame[(y//8)*WIDTH+x+extra]|=mask
            u=(u+du)&65535;v=(v+dv)&65535
    return frame


def pixels(frame):
    return [[int(bool(frame[y//8*WIDTH+x]&(1<<(y&7)))) for x in range(WIDTH)] for y in range(HEIGHT)]


def put(image,x,y,value=1):
    if 0<=x<WIDTH and 0<=y<HEIGHT:image[y][x]=value


def text(image,x,y,value):
    for ch in value:
        for row,bits in enumerate(FONT[ch]):
            for column,bit in enumerate(bits):put(image,x+column,y+row,int(bit))
        x+=6


def draw_ship(image,x,y,width=len(SHIP[0])):
    source_width=len(SHIP[0]);source_height=len(SHIP)
    height=max(3,round(source_height*width/source_width))
    for py in range(height):
        line=SHIP[min(source_height-1,py*source_height//height)]
        left=line.find('#');right=line.rfind('#')
        for px in range(width):
            sx=px*source_width//width
            if left<=sx<=right:put(image,x+px,y+py,int(line[sx]=='#'))


def compose(frame,index=20,language='fr'):
    image=pixels(frame)
    # Original skyline and sprites illustrate the proposed composition.
    for x in range(WIDTH):
        height=2+((x//11)*7+index//10)%5
        for y in range(7-height,8):
            put(image,x,y,0 if x%11 in (3,4) and y%3==0 else 1)
    pose=camera(index);cx,cy,fx,fy=pose;rx,ry=-fy,fx
    points=centreline()
    for advance in (22,10):
        wx,wy=points[(index+advance)%len(points)]
        wx-=cx;wy-=cy
        depth=wx*fx+wy*fy
        if depth>3:
            width=max(3,min(11,round(FOCAL*.8/depth)))
            sx=round(WIDTH/2+FOCAL*(wx*rx+wy*ry)/depth)-width//2
            sy=round(HORIZON+CAMERA_HEIGHT*FOCAL/depth)-max(3,round(len(SHIP)*width/len(SHIP[0])))
            if 8<=sy<=35:draw_ship(image,sx,sy,width)
    draw_ship(image,(WIDTH-len(SHIP[0]))//2,27)
    for y in range(40,48):image[y]=[0]*WIDTH
    text(image,0,41,'VIT380 T1/3' if language=='fr' else 'V380 L1/3')
    for x in range(78,143):
        put(image,x,41);put(image,x,47)
        if x in (78,142):
            for y in range(41,48):put(image,x,y)
        elif x<128:
            for y in range(43,46):put(image,x,y)
    return image


def save_png(path,image,scale=6):
    width=len(image[0])*scale;height=len(image)*scale
    raw=bytearray()
    for row in image:
        line=b''.join((b'\x21\x33\x26' if pixel else b'\xd7\xe5\xb7')*scale for pixel in row)
        raw.extend((b'\0'+line)*scale)
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width,height,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def save_artwork(image,output,index=20,language='fr',prefix='concept'):
    output.mkdir(parents=True,exist_ok=True)
    for step,row_step in ((1,1),(2,1),(2,2)):
        frame=reference_floor(image,rows_for(camera(index),step,row_step),step,row_step)
        scene=compose(frame,index,language)
        write_bmp(output/f'{prefix}_{step}x{row_step}.bmp',WIDTH,HEIGHT,
                  [(0,0,0) if pixel else (255,255,255) for row in scene for pixel in row])
        save_png(output/f'{prefix}_{step}x{row_step}.png',scene)


def main():
    parser=Parser('Generer une etude visuelle de piste projetee G850.',
                  'Generate G850 projected-track concept artwork.')
    parser.add_argument('--output',type=Path,default=HERE/'docs')
    parser.add_argument('--position',type=int,default=20)
    parser.add_argument('--road-half-width',type=float,default=ROAD_HALF_WIDTH)
    args=parser.parse_args()
    if not 1<=args.road_half_width<=12:
        parser.error('--road-half-width: 1..12')
    image,_=build_track(args.road_half_width)
    save_artwork(image,args.output,args.position,args.lang)
    write_bmp(args.output/'track.bmp',128,128,
        [(0,0,0) if sample_texture(image,x<<8,y<<8) else (255,255,255) for y in range(128) for x in range(128)])
    write_bmp(args.output/'ship.bmp',len(SHIP[0]),len(SHIP),
        [(0,0,0) if c=='#' else (255,255,255) for row in SHIP for c in row])
    print(pick(args.lang,'Etude visuelle generee.','Concept artwork generated.'))


if __name__=='__main__':main()
