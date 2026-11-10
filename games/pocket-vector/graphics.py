"""FR/EN: import editable native BMPs without changing the source artwork."""
from pathlib import Path
import struct
import zlib
from bitmap import read_bmp,write_bmp

COLORS=((128,128,128),(255,255,255),(0,0,0))
DIRECTIONS=('north','north_west','west','west_south','south','east_south','east','north_east')
FRAME_SPECS={**{f'player_{name}':(23,11) for name in DIRECTIONS},
             **{f'rival_{family}_{w:02}':(w,h) for family in ('a','b')
                for w,h in ((3,3),(5,3),(7,4),(9,5),(11,6),(15,7))},
             'exhaust_0':(5,2),'exhaust_1':(5,2)}


def read_sprite(path,expected):
    width,height,pixels=read_bmp(path)
    if (width,height)!=expected:
        raise ValueError(f'{path.name}: {expected[0]}x{expected[1]} pixels required / requis')
    data=[]
    for color in pixels:
        # Neutral near-white pixels from bitmap editors remain white on the LCD.
        if color[0]==color[1]==color[2] and color[0]>=240:color=COLORS[1]
        if color not in COLORS:
            raise ValueError(f'{path.name}: black, white or #808080 transparency / noir, blanc ou transparence #808080')
        data.append(COLORS.index(color))
    if not any(v==2 for v in data):raise ValueError(f'{path.name}: empty silhouette / silhouette vide')
    return bytes([width,height]+data)


def packed_sprite(record):
    """Two bits per pixel, low pair first, continuous across row boundaries."""
    out=bytearray(record[:2]);pixels=record[2:]
    for i in range(0,len(pixels),4):
        out.append(sum(value<<(2*j) for j,value in enumerate(pixels[i:i+4])))
    return bytes(out)


def mirrored(record):
    w,h=record[:2]
    return record[:2]+b''.join(record[2+y*w:2+(y+1)*w][::-1] for y in range(h))


def save_rgb_png(path,width,height,pixels,scale=1):
    raw=bytearray()
    for y in range(height):
        line=b''.join(bytes(c)*scale for c in pixels[y*width:(y+1)*width])
        raw.extend((b'\0'+line)*scale)
    def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',width*scale,height*scale,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def load_frames(folder,docs,font):
    docs.mkdir(exist_ok=True)
    frames={name:read_sprite(folder/(name+'.bmp'),size) for name,size in FRAME_SPECS.items()}
    atlas=[COLORS[0]]*(24*16*len(frames))
    for index,record in enumerate(frames.values()):
        w,h=record[:2]
        for y in range(h):
            for x in range(w):atlas[(index*16+y)*24+x]=COLORS[record[2+y*w+x]]
    write_bmp(docs/'sprites.bmp',24,16*len(frames),atlas)
    canvas_w,cell_w,cell_h=540,180,92
    canvas_h=((len(frames)+2)//3)*cell_h
    canvas=[(236,236,230)]*(canvas_w*canvas_h)
    for index,(name,record) in enumerate(frames.items()):
        ox=(index%3)*cell_w;oy=(index//3)*cell_h;w,h=record[:2]
        label=name.replace('player_','P ').replace('rival_','R ').replace('_',' ').upper()
        for i,ch in enumerate(label):
            for y,row in enumerate(font.get(ch,font[' '])):
                for x,bit in enumerate(row):
                    if bit=='1':canvas[(oy+3+y)*canvas_w+ox+4+i*6+x]=(15,20,20)
        for y in range(h):
            for x in range(w):
                color=COLORS[record[2+y*w+x]]
                for sy in range(5):
                    for sx in range(5):canvas[(oy+18+y*5+sy)*canvas_w+ox+20+x*5+sx]=color
    save_rgb_png(docs/'sprites_preview.png',canvas_w,canvas_h,canvas)
    return frames
