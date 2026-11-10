"""FR/EN: editable Canon Quest 8x8 artwork -> G850 pages and 2x portraits."""
from pathlib import Path
import json,sys,unicodedata

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[1]
sys.path.insert(0,str(GAME.parents[1]/'lib'))
from bitmap import read_bmp,write_bmp,write_png


def generate():
    w,h,pixels=read_bmp(HERE/'tiles.bmp')
    black,white=(0,0,0),(255,255,255)
    if (w,h)!=(8,184) or set(pixels)-{black,white}:
        raise ValueError('tiles.bmp: 8 x 184 pixels, noir/blanc uniquement / black and white only')
    labels=json.loads((GAME/'tiles.json').read_text(encoding='utf-8'))['tiles']
    tiles=[pixels[i*64:(i+1)*64] for i in range(23)]
    def columns(tile):
        return bytes(sum((tile[y*8+x]==black)<<y for y in range(8)) for x in range(8))
    lines=['; Genere depuis / Generated from targets/g850/tiles.bmp.','glyph_tiles:']
    for i,tile in enumerate(tiles):
        if i==15:lines.append('glyph_hero:')
        lines.append('    db '+','.join(f'0x{v:02X}' for v in columns(tile))+f' ; {i:02}')
    lines.append('portrait_tiles:')
    for tile in tiles:
        for page in (0,1):
            data=[sum((tile[(page*4+y//2)*8+x//2]==black)<<y for y in range(8)) for x in range(16)]
            lines.append('    db '+','.join(f'0x{v:02X}' for v in data))
    (HERE/'tiles.inc').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    import tiles_tool
    rows=tiles_tool.read_map(GAME/'map_packed.inc')
    world=[white]*(240*128)
    for y,row in enumerate(rows):
        for x,tile in enumerate(row):
            for dy in range(8):world[(y*8+dy)*240+x*8:(y*8+dy)*240+x*8+8]=tiles[tile][dy*8:dy*8+8]
    docs=GAME/'docs';docs.mkdir(exist_ok=True)
    write_bmp(docs/'map_g850.bmp',240,128,world)
    write_png(docs/'map_g850.png',960,512,[world[(y//4)*240+x//4] for y in range(512) for x in range(960)])
    width,height=620,23*56;preview=[white]*(width*height)
    def text(x,y,value):
        value=unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().upper()
        for char in value:
            pattern=bytes.fromhex(tiles_tool.FONT.get(char,tiles_tool.FONT[' ']))
            for dy,bits in enumerate(pattern):
                for dx in range(5):
                    if bits&(1<<(4-dx)):
                        for yy in range(2):
                            for xx in range(2):preview[(y+dy*2+yy)*width+x+dx*2+xx]=black
            x+=12
    for i,tile in enumerate(tiles):
        for y in range(48):
            for x in range(48):preview[(i*56+y)*width+x]=tile[y//6*8+x//6]
        text(60,i*56+6,f'{i:02} {labels[i]["fr"]}')
        text(60,i*56+28,labels[i]['en'])
    write_png(docs/'tiles_g850.png',width,height,preview)


if __name__=='__main__':generate()
