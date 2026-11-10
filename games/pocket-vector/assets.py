"""FR/EN: original monochrome G850 assets and fixed-point projection tables."""
from pathlib import Path
import json
import hashlib
import math
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'lib'))
from bitmap import write_bmp
from graphics import load_frames,packed_sprite,mirrored,DIRECTIONS


def reference():
    import projection
    return projection


def path_nodes(ref,control=None):
    if control is None:dense=ref.centreline()
    else:
        dense=[]
        for i in range(len(control)):
            a,b,c,d=(control[(i+j)%len(control)] for j in (-1,0,1,2))
            for n in range(40):
                t=n/40
                dense.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+
                    (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in (0,1)))
    lengths=[0.0]
    for i in range(len(dense)):
        x,y=dense[i];u,v=dense[(i+1)%len(dense)]
        lengths.append(lengths[-1]+math.hypot(u-x,v-y))
    nodes=[];segment=0
    for i in range(128):
        target=i*lengths[-1]/128
        while lengths[segment+1]<target:segment+=1
        t=(target-lengths[segment])/(lengths[segment+1]-lengths[segment])
        x,y=dense[segment];u,v=dense[(segment+1)%len(dense)]
        nodes.append((round(x+(u-x)*t),round(y+(v-y)*t)))
    return nodes


def world_maps(nodes,half_width=6.0,theme=0):
    visual=bytearray(2048);road=bytearray(2048)
    for y in range(128):
        for x in range(128):
            best=(1e9,0)
            for i,(px,py) in enumerate(nodes):
                qx,qy=nodes[(i+1)&127];dx=qx-px;dy=qy-py
                t=max(0,min(1,((x-px)*dx+(y-py)*dy)/(dx*dx+dy*dy)))
                dist=(x-px-t*dx)**2+(y-py-t*dy)**2
                if dist<best[0]:best=(dist,(i+(t>.5))&127)
            dist,index=best;inside=dist<half_width**2
            # Floating asphalt, a thin rail, white separator and striped verge.
            black=True
            if theme==0 and x%24<2 and y%24<2:black=False
            if theme==1 and (x//12+y//20)%3==0:black=False
            if theme==2 and (x%24==0 or y%24==0):black=False
            if dist<(half_width+2.4)**2:black=bool((index//2)&1)
            if dist<(half_width+1.3)**2:black=False
            if dist<(half_width+.6)**2:black=True
            if inside:black=False
            if inside and index==0:black=((x+y)&1)==0
            if inside and 44<=index<52:black=((x+y)//2)&1
            offset=y*16+x//8;mask=128>>(x&7)
            if black:visual[offset]|=mask
            if inside:road[offset]|=mask
    return bytes(visual),bytes(road)


def lz_pack(data):
    """0=end, 1..127=literal length, 128..255=match length 3..130 + distance16."""
    out=bytearray();literal=bytearray();i=0;positions={}
    def flush():
        if literal:out.append(len(literal));out.extend(literal);literal.clear()
    while i<len(data):
        key=data[i:i+3];best_length=0;best_distance=0
        for previous in reversed(positions.get(key,[])):
            length=3
            while length<130 and i+length<len(data) and data[previous+length]==data[i+length]:length+=1
            if length>best_length:best_length=length;best_distance=i-previous
            if length==130:break
        take=best_length if best_length>=4 else 1
        if take>1:
            flush();out.extend((128+take-3,best_distance&255,best_distance>>8))
        else:
            literal.append(data[i])
            if len(literal)==127:flush()
        for j in range(i,i+take):positions.setdefault(data[j:j+3],[]).append(j)
        i+=take
    flush();return bytes(out+b'\0')


def skyline(theme):
    out=[]
    for x in range(128):
        if theme==0:
            height=2+((x//7)*11)%6
            byte=sum((0 if x%7 in (2,3) and y%3==0 else 1)<<y for y in range(8-height,8))
        elif theme==1:
            height=2+abs((x//4)%14-7)//2
            byte=((1<<height)-1)<<(8-height)
            if x%24 in (0,1):byte=0xFF
        else:
            height=2+round(3*(1+math.sin(x*math.pi/32)))
            byte=((1<<height)-1)<<(8-height)
        out.append(byte)
    return bytes(out+out[:16])


EXTRA_FONT={
 'A':('01110','10001','10001','11111','10001','10001','10001'),
 'B':('11110','10001','10001','11110','10001','10001','11110'),
 'C':('01111','10000','10000','10000','10000','10000','01111'),
 'D':('11110','10001','10001','10001','10001','10001','11110'),
 'E':('11111','10000','10000','11110','10000','10000','11111'),
 'F':('11111','10000','10000','11110','10000','10000','10000'),
 'G':('01111','10000','10000','10111','10001','10001','01110'),
 'H':('10001','10001','10001','11111','10001','10001','10001'),
 'J':('00111','00010','00010','00010','10010','10010','01100'),
 'K':('10001','10010','10100','11000','10100','10010','10001'),
 'M':('10001','11011','10101','10101','10001','10001','10001'),
 'N':('10001','11001','10101','10011','10001','10001','10001'),
 'O':('01110','10001','10001','10001','10001','10001','01110'),
 'P':('11110','10001','10001','11110','10000','10000','10000'),
 'Q':('01110','10001','10001','10001','10101','10010','01101'),
 'R':('11110','10001','10001','11110','10100','10010','10001'),
 'S':('01111','10000','10000','01110','00001','00001','11110'),
 'U':('10001','10001','10001','10001','10001','10001','01110'),
 'W':('10001','10001','10001','10101','10101','10101','01010'),
 'X':('10001','10001','01010','00100','01010','10001','10001'),
 'Y':('10001','10001','01010','00100','00100','00100','00100'),
 'Z':('11111','00001','00010','00100','01000','10000','11111'),
 ':':('00000','00100','00100','00000','00100','00100','00000'),
 '-':('00000','00000','00000','11111','00000','00000','00000'),
 '+':('00000','00100','00100','11111','00100','00100','00000'),
 '(':('00010','00100','01000','01000','01000','00100','00010'),
 ')':('01000','00100','00010','00010','00010','00100','01000'),
 '!':('00100','00100','00100','00100','00100','00000','00100'),
 '<':('00010','00100','01000','10000','01000','00100','00010'),
 '>':('01000','00100','00010','00001','00010','00100','01000'),
}


def sprite(ref,width=19,spin=0,bank=0):
    # Readable distant silhouettes: point sampling can erase thin 19px outlines.
    micro={3:('#.#','###','.#.'),5:('.###.','#####','#.#.#'),
           7:('..###..','.##.##.','#######','.#...#.'),
           9:('...###...','..##.##..','.##...##.','#########','.##...##.'),
           11:('....###....','..###.###..','.##.....##.','###.###.###',
               '###.###.###','..##...##..')}
    if width in micro:
        result=[]
        for row in micro[width]:
            left,right=row.find('#'),row.rfind('#')
            result.extend(2 if c=='#' else 1 if left<=x<=right else 0 for x,c in enumerate(row))
        return bytes([width,len(micro[width])]+result)
    height=max(3,round(11*width/19));data=[]
    ca,sa=math.cos(spin),math.sin(spin)
    for y in range(height):
        source=[]
        for x in range(width):
            u=(x+.5)*19/width-9.5;v=(y+.5)*11/height-5.5
            sx=round(ca*u+sa*v+9-bank*(v+5)/9)
            sy=round(-sa*u+ca*v+5)
            source.append(0<=sx<19 and 0<=sy<11 and ref.SHIP[sy][sx]=='#')
        on=[i for i,value in enumerate(source) if value]
        for x,value in enumerate(source):
            data.append(2 if value else 1 if on and on[0]<=x<=on[-1] else 0)
    return bytes([width,height]+data)


def generate(target='g850'):
    native=target=='g850'
    ref=reference();tracks=json.loads((HERE/'tracks.json').read_text(encoding='utf-8'))['tracks']
    assert len(tracks)==3
    docs=HERE/'docs';docs.mkdir(exist_ok=True)
    lines=['; Generated original assets / ressources originales generees. MIT.']
    def emit(label,data):
        lines.append(label+':')
        for i in range(0,len(data),24):lines.append('    db '+','.join(str(v&255) for v in data[i:i+24]))
    emit('direction_table',[value for i in range(64) for value in
         (round(math.cos(i*math.pi/32)*127),round(math.sin(i*math.pi/32)*127))])
    coeff=[]
    for i in range(16):
        angle=i*math.pi/32
        for row in ref.rows_for((0,0,math.cos(angle),math.sin(angle)),2,1 if native else 2,bottom=48):
            for value in row:coeff.extend((value&255,value>>8))
    emit('perspective_offsets',coeff)
    font={**ref.FONT,**EXTRA_FONT}
    emit('font_columns',[sum(int(font.get(chr(code),font[' '])[y][x])<<y for y in range(7))
                         for code in range(32,91) for x in range(5)])
    lines.append('countdown_sprites: dw countdown_3,countdown_2,countdown_1,countdown_go')
    for name,text in (('3','3'),('2','2'),('1','1'),('go','GO!')):
        columns=[]
        for i,ch in enumerate(text):
            if i:columns.append([0]*7)
            glyph=font[ch]
            for x in ((2,) if ch=='!' else range(5)):
                columns.append([int(glyph[y][x]) for y in range(7)])
        width=len(columns)*2+2;height=16;pixels=[1]*(width*height)
        for x,column in enumerate(columns):
            for y,value in enumerate(column):
                if value:
                    for dx in range(2):
                        for dy in range(2):pixels[(y*2+1+dy)*width+x*2+1+dx]=2
        emit('countdown_'+name,packed_sprite(bytes([width,height]+pixels)))
    frames=load_frames(HERE/'graphics',docs,font)
    stored={};render_frames={}
    for name,record in frames.items():
        label,flip=stored.get(record,(None,0))
        if label is None and name.startswith('player_'):
            label,flip=stored.get(mirrored(record),(None,0))
            flip=1 if label is not None else 0
        if label is None:
            label=name;emit(label,packed_sprite(record));stored[record]=(label,0)
        render_frames[name]=(label,flip)
        if name!=label:lines.append(f'{name} EQU {label}')
    lines.append('ship_straight EQU player_north')
    for family in ('a','b'):
        lines.append(f'rival_{family}_table: dw '+','.join(render_frames[f'rival_{family}_{w:02}'][0] for w in (3,5,7,9,11,15)))
    for width in (3,5,7,9,11,15):lines.append(f'rival_sprite_{width} EQU rival_a_{width:02}')
    lines.append('player_sprites:')
    for direction in DIRECTIONS:
        label,flip=render_frames['player_'+direction]
        lines.append(f'    dw {label}')
        lines.append(f'    db {flip}')
    tiny={'0':('111','101','101','101','111'),'1':('010','110','010','010','111'),
          '2':('110','001','010','100','111'),'3':('110','001','010','001','110'),
          '4':('101','101','111','001','001'),'5':('111','100','110','001','110'),
          '6':('011','100','111','101','111'),'7':('111','001','010','010','010'),
          '8':('111','101','111','101','111'),'9':('111','101','111','001','110'),
          'V':('101','101','101','101','010'),'T':('111','010','010','010','010'),
          'L':('100','100','100','100','111'),'P':('110','101','110','100','100'),
          'B':('110','101','110','101','110'),'D':('110','101','101','101','110'),
          '/':('001','001','010','100','100'),'-':('000','000','111','000','000')}
    emit('tiny_font',[sum(int(tiny.get(chr(code),('000',)*5)[y][x])<<y for y in range(5))
                      for code in range(32,91) for x in range(3)])
    lines.append('minimap_table: dw minimap_0,minimap_1,minimap_2')
    emit('map_player',packed_sprite(bytes([3,3,2,2,2,2,1,2,2,2,2])))
    emit('map_player_flash',packed_sprite(bytes([3,3,1,1,1,1,2,1,1,1,1])))
    emit('map_rival',packed_sprite(bytes([2,2,2,1,1,2])))
    lines.append('track_table:')
    for i in range(3):lines.append(f'    dw texture_{i},road_{i},path_{i},sky_{i}')
    manifest={'tracks':[],'sprites':{name:hashlib.sha256(data).hexdigest() for name,data in frames.items()},
              'sprite_storage':{'format':'2bpp, low pair first',
                  'source_pixel_bytes':sum(len(record)-2 for record in frames.values()),
                  'packed_bytes':sum(len(packed_sprite(record)) for record in stored),
                  'mirrored':[name for name,(label,flip) in render_frames.items() if flip]}}
    for i,spec in enumerate(tracks):
        nodes=path_nodes(ref,spec['nodes'])
        # Put the line in the first straight; the grid sits on nodes 124..127.
        nodes=nodes[12:]+nodes[:12]
        # A level starting straight avoids one-pixel path rounding turning the
        # stationary camera by 11.25 degrees. Rebuild road, headings and maps
        # together; the curve resumes beyond the start/finish line.
        start_y=nodes[0][1]
        for n in (*range(120,128),*range(5)):
            nodes[n]=(nodes[n][0],start_y)
        visual,road=world_maps(nodes,spec['half_width'],spec['theme'])
        path=[]
        for n,(x,y) in enumerate(nodes):
            px,py=nodes[(n-1)&127];qx,qy=nodes[(n+1)&127]
            angle=round(math.atan2(qy-py,qx-px)*32/math.pi)&63
            path.extend((x,y,angle,0))
        emit('path_'+str(i),path);emit('texture_'+str(i),lz_pack(visual));emit('road_'+str(i),lz_pack(road))
        emit('sky_'+str(i),skyline(spec['theme']))
        mini=[0]*512;route={(x>>2,y>>3) for x,y in nodes}
        for x,y in route:
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    if 0<=x+dx<32 and 0<=y+dy<16:mini[(y+dy)*32+x+dx]=2
        for x,y in route:mini[y*32+x]=1
        # Native two-page AND/OR pairs avoid unpacking 512 pixels each frame.
        mini_native=[]
        for page in range(2):
            for x in range(32):
                column=[mini[(page*8+y)*32+x] for y in range(8)]
                mask=sum((value!=0)<<y for y,value in enumerate(column))
                ink=sum((value==2)<<y for y,value in enumerate(column))
                mini_native.extend((255^mask,ink))
        emit('minimap_'+str(i),mini_native)
        if not native:
            route_small={(x>>3,y>>4) for x,y in nodes}
            halo={(x+dx,y+dy) for x,y in route_small for dx,dy in
                  ((0,0),(-1,0),(1,0),(0,-1),(0,1)) if 0<=x+dx<16 and 0<=y+dy<8}
            packed=[]
            for page in (2,3):
                for x in range(16):
                    mask=ink=0
                    for y in range(8):
                        logical=20+y
                        if logical//7!=page:continue
                        bit=1<<(logical%7)
                        if (x,y) in halo:mask|=bit
                        if (x,y) in route_small:ink|=bit
                    packed.extend((127^mask,ink))
            emit('g80x_map_'+str(i),packed)
        manifest['tracks'].append({'name_fr':spec['name_fr'],'name_en':spec['name_en'],
            'visual_sha256':hashlib.sha256(visual).hexdigest(),'road_sha256':hashlib.sha256(road).hexdigest(),
            'path_sha256':hashlib.sha256(bytes(path)).hexdigest(),
            'sky_sha256':hashlib.sha256(skyline(spec['theme'])).hexdigest(),
            'packed_visual_bytes':len(lz_pack(visual)),'packed_road_bytes':len(lz_pack(road))})
        write_bmp(docs/f'track{i+1}.bmp',128,128,[(0,0,0) if visual[y*16+x//8]&(128>>(x&7)) else (255,255,255)
                  for y in range(128) for x in range(128)])
        lines.append('    IF BUILD_LANG_EN')
        lines.append(f'track_name_{i}: db "{spec["name_en"]}",0')
        lines.append('    ELSE')
        lines.append(f'track_name_{i}: db "{spec["name_fr"]}",0')
        lines.append('    ENDIF')
    lines.append('track_names: dw track_name_0,track_name_1,track_name_2')
    scales=[]
    for spec in tracks:
        points=path_nodes(ref,spec['nodes'])
        distance=sum(math.dist(points[i],points[(i+1)&127]) for i in range(128))
        scales.append(round((127/32)/(distance/128)*256))
    lines.append('rival_scales: dw '+','.join(map(str,scales)))
    lines.append('    ALIGN 256')
    emit('texture_masks',[128,64,32,16,8,4,2,1])
    if not native:
        emit('g80x_sample_x',[(2*x+1)*144//240 for x in range(120)])
        lines.append('g80x_sample_rows:')
        for y in range(21):
            sy=(2*y+1)*40//42
            lines.extend((f'    dw frame+{sy//8*144}',f'    db {1<<(sy&7)}',
                          f'    dw lcd_frame+{(1+y//7)*120}',f'    db {1<<(y%7)}'))
        lines.append('g80x_map_table: dw g80x_map_0,g80x_map_1,g80x_map_2')
    destination=HERE if native else HERE/'targets/g80x-32k'
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'assets.inc').write_text('\n'.join(lines)+'\n',encoding='ascii')
    (destination/'assets_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':generate()
