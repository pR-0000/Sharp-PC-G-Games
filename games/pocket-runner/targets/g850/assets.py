"""FR/EN: editable native 7x8 patterns, 12 tiles stacked vertically."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'lib'))
from bitmap import read_bmp,write_png


def generate():
    w,h,pixels=read_bmp(HERE/'tiles.bmp')
    if (w,h)!=(7,96) or set(pixels)-{(0,0,0),(255,255,255)}:
        raise ValueError('tiles.bmp: 7 x 96 pixels, noir/blanc / black and white')
    lines=['; Genere depuis / Generated from targets/g850/tiles.bmp.','patterns:']
    for i in range(12):
        data=[sum((pixels[(i*8+y)*7+x]==(0,0,0))<<y for y in range(8)) for x in range(7)]
        lines.append('    db '+','.join(f'0x{v:02X}' for v in data)+f' ; {i:02}')
    (HERE/'patterns.inc').write_text('\n'.join(lines)+'\n',encoding='ascii')
    docs=HERE.parents[1]/'docs';docs.mkdir(exist_ok=True)
    write_png(docs/'tiles_g850.png',56,768,[pixels[y//8*7+x//8] for y in range(768) for x in range(56)])


if __name__=='__main__':generate()
