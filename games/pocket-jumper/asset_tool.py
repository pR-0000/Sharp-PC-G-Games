"""FR : atlas et niveau BMP editables. EN: editable BMP atlas and level."""
from pathlib import Path
import sys
import assets
from assets import HERE,ROOT,BLACK,WHITE,COLOURS,TILES,WIDTH,HEIGHT
sys.path.insert(0,str(ROOT/'lib'))
from bitmap import read_bmp,write_bmp
from cli_i18n import Parser,pick

def import_map(path):
    patterns=assets.art();w,h,pixels=read_bmp(path)
    if (w,h)!=(768,48):raise ValueError('Carte rendue : 768 x 48 pixels requis / Rendered map: 768 x 48 pixels required')
    if any(p not in (BLACK,WHITE) for p in pixels):raise ValueError('Carte : noir/blanc pur requis / Map: pure black/white required')
    lookup={}
    for i,name in enumerate(TILES):
        key=tuple(row for row in patterns[name])
        if key in lookup:raise ValueError('Motifs de terrain identiques : utiliser le plan colore / Duplicate terrain patterns: use the colour layout')
        lookup[key]=i
    cells=[]
    for ty in range(HEIGHT):
        for tx in range(WIDTH):
            key=tuple(''.join('#' if pixels[(ty*8+y)*w+tx*8+x]==BLACK else '.' for x in range(8)) for y in range(8))
            if key not in lookup:raise ValueError(f'Case / Cell {tx},{ty} : motif 8 x 8 inconnu / unknown 8 x 8 pattern')
            cells.append(lookup[key])
    write_bmp(HERE/'level_01_layout.bmp',WIDTH,HEIGHT,[COLOURS[i] for i in cells])

def previews():
    from PIL import Image,ImageDraw,ImageFont
    import json
    def font(size):
        for name in ('C:/Windows/Fonts/consola.ttf','DejaVuSans.ttf'):
            try:return ImageFont.truetype(name,size)
            except OSError:pass
        return ImageFont.load_default()
    small,title=font(13),font(19)
    out=HERE/'docs';out.mkdir(exist_ok=True)
    spec=json.loads((HERE/'sprites.json').read_text(encoding='utf-8'))
    atlas=Image.open(HERE/'sprites.bmp').convert('RGB')
    sheet=Image.new('RGB',(680,612),'white');d=ImageDraw.Draw(sheet)
    d.text((16,12),'Pocket Jumper - atlas / sprites',fill='black',font=title)
    for item in spec['frames']:
        i=item['id'];left=16+(i//8)*336;top=50+(i%8)*68
        sprite=atlas.crop((0,item['y'],12,item['y']+12)).resize((48,48),Image.Resampling.NEAREST)
        sheet.paste(sprite,(left,top));d.rectangle((left-1,top-1,left+48,top+48),outline=(180,180,180))
        x=left+62
        d.text((x,top),f'{i:02d}  {item["fr"]}',fill='black',font=small)
        d.text((x,top+17),item['en'],fill=(70,70,70),font=small)
        d.text((x,top+34),f'{item["width"]} x {item["height"]} px',fill=(70,70,70),font=small)
        if i<9:d.rectangle((x+142,top+36,x+156,top+48),fill=COLOURS[i],outline='black')
    d.text((16,596),'Source : sprites.bmp (12 x 180) | Noir / black = pixel ON',fill='black',font=small)
    sheet.save(HERE/'sprites_guide.bmp');sheet.save(out/'sprites_preview.png')

    world=Image.open(HERE/'level_01.bmp').convert('RGB');pixels=world.load()
    patterns,level=assets.art(),assets.level_spec()
    entities=[('hero_a',*level['player_start'])]+[('enemy',e['x'],e['y']) for e in level['enemies']]
    for name,x,y in entities:
        for row,line in enumerate(patterns[name]):
            for col,value in enumerate(line):
                if value=='#' and 0<=x+col<768 and 0<=y+row<48:pixels[x+col,y+row]=BLACK
    world.save(HERE/'level_01_entities.bmp')
    overview=Image.new('RGB',(800,950),'white');d=ImageDraw.Draw(overview)
    d.text((16,12),'Niveau 01 / Level 01 - 768 x 48 px',fill='black',font=title)
    d.text((16,40),'Depart + ennemis / Start + enemies',fill='black',font=small)
    for i in range(4):
        top=72+i*214
        d.text((16,top),f'x = {192*i:03d} - {192*(i+1)-1:03d}',fill='black',font=small)
        part=world.crop((192*i,0,192*(i+1),48)).resize((768,192),Image.Resampling.NEAREST)
        overview.paste(part,(16,top+18))
        d.rectangle((15,top+17,784,top+210),outline=(180,180,180))
    d.text((16,936),'Plan editable / Editable layout : level_01_layout.bmp (96 x 6)',fill='black',font=small)
    overview.save(HERE/'level_01_preview.bmp');overview.save(out/'level_01_preview.png')
    layout=Image.open(HERE/'level_01_layout.bmp').convert('RGB').resize((768,48),Image.Resampling.NEAREST)
    layout.save(out/'level_01_layout_preview.png')

def main():
    parser=Parser('Exporter les BMP de Pocket Jumper.','Export Pocket Jumper BMP assets.')
    parser.add_argument('--import-map',type=Path,help=pick(parser.lang,'Importer une carte rendue 768 x 48, par blocs 8 x 8.','Import a rendered 768 x 48 map, using 8 x 8 tiles.'))
    parser.add_argument('--previews',action='store_true',help=pick(parser.lang,'Guides BMP/PNG agrandis (Pillow).','Enlarged BMP/PNG guides (Pillow).'))
    args=parser.parse_args()
    try:
        if args.import_map:import_map(args.import_map)
        assets.generate()
        if args.previews:previews()
    except (ValueError,KeyError,OSError) as error:parser.error(str(error))
    except ImportError:parser.error(pick(args.lang,'Les apercus demandent Pillow : python -m pip install Pillow','Previews require Pillow: python -m pip install Pillow'))
    print(pick(args.lang,'BMP exportes ; sprites.bmp et level_01_layout.bmp sont les sources editables.','BMP files exported; sprites.bmp and level_01_layout.bmp are the editable sources.'))
if __name__=='__main__':main()
