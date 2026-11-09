"""FR/EN: original pixel art and level for Pocket Jumper."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from bitmap import read_bmp,write_bmp
WIDTH,HEIGHT=96,6
BLACK,WHITE=(0,0,0),(255,255,255)
COLOURS=(WHITE,(150,90,40),(190,60,45),(255,200,0),(255,255,0),(255,0,0),(0,180,0),(0,100,255),(128,128,128))
TILES=('tile_air','tile_soil','tile_brick','tile_bonus','tile_coin','tile_spike','tile_flag','tile_checkpoint','tile_used')

def default_level():
    cells=bytearray(WIDTH*HEIGHT)
    for x in range(WIDTH):cells[5*WIDTH+x]=1
    for x in (20,21,44,45,70,71,72):cells[5*WIDTH+x]=0
    for x in range(8,12):cells[4*WIDTH+x]=2
    for x in range(27,31):cells[4*WIDTH+x]=2
    for x in (29,30):cells[3*WIDTH+x]=2
    for x in range(53,57):cells[4*WIDTH+x]=2
    for x in (5,15,34,61,79):cells[2*WIDTH+x]=3
    for x in (14,16,33,35,78,80):cells[2*WIDTH+x]=2
    for x,y in ((3,3),(9,2),(11,2),(18,3),(23,3),(28,2),(30,1),(38,3),
                (43,3),(47,3),(50,3),(54,2),(56,2),(65,3),(69,3),(74,3),(85,3),(89,3)):
        assert cells[y*WIDTH+x]==0
        cells[y*WIDTH+x]=4
    cells[4*WIDTH+62]=5
    cells[4*WIDTH+48]=7
    cells[3*WIDTH+92]=cells[4*WIDTH+92]=6
    return cells

def columns(rows):
    assert rows and all(len(r)==len(rows[0]) for r in rows)
    return [sum((c!='.')<<y for y,row in enumerate(rows) for c in [row[x]]) for x in range(len(rows[0]))]

def default_art():
    art={
      'tile_air':['........']*8,
      'tile_soil':['########','.#.#.#.#','########','#...#...','..#...#.','.#..#...','...#..#.','#....#..'],
      'tile_brick':['########','#...#..#','#...#..#','########','#.#....#','#.#....#','#.#....#','########'],
      'tile_bonus':['########','#......#','#.###..#','#....#.#','#..##..#','#......#','#..#...#','########'],
      'tile_coin':['..####..','.#....#.','#..#...#','#..#...#','#..#...#','#...#..#','.#....#.','..####..'],
      'tile_spike':['...#....','..###...','..###...','..###...','.#####..','.#####..','#######.','########'],
      'tile_flag':['.#......','.######.','.#####..','.####...','.#......','.#......','.#......','###.....'],
      'tile_checkpoint':['.#......','.#####..','.#...#..','.#####..','.#......','.#......','.#......','###.....'],
      'tile_used':['########','#......#','#.#..#.#','#......#','#......#','#.#..#.#','#......#','########'],
      'hero_a':['....#####...','...#######..','...##..#....','...##..###..','....#####...','...##.##....','..#######...','.##.#####.#.','....#####.#.','...##..##...','..###..###..','.####..####.'],
      'hero_b':['....#####...','...#######..','...##..#....','...##..###..','....#####...','...##.##....','..#######...','..#.#####.#.','....#####...','..###..##...','.###....###.','.......####.'],
      'enemy':['..######..','.########.','###.##.###','###.##.###','.########.','..######..','.##....##.','####..####'],
      'cloud':['...######...','..#......#..','.##......##.','#..........#','#..........#','.##########.'],
      'heart':['.##.##.','#######','#######','.#####.','..###..','...#...'],
    }
    art.pop('heart')
    for name,cols in (('heart_icon',(14,31,62,31,14)),('coin_icon',(28,34,62,34,28))):
        art[name]=[''.join('#' if value>>y&1 else '.' for value in cols) for y in range(7)]
    return art

def art():
    defaults=default_art();path=HERE/'sprites.bmp'
    width,height=12,len(defaults)*12
    if not path.exists():
        pixels=[WHITE]*(width*height)
        for i,rows in enumerate(defaults.values()):
            for y,row in enumerate(rows):
                for x,pixel in enumerate(row):pixels[(12*i+y)*12+x]=BLACK if pixel=='#' else WHITE
        write_bmp(path,width,height,pixels)
    w,h,pixels=read_bmp(path)
    if (w,h)!=(width,height):raise ValueError(f'Atlas BMP : {width} x {height} pixels requis / required')
    if any(p not in (BLACK,WHITE) for p in pixels):raise ValueError('Atlas : noir/blanc pur requis / pure black/white required')
    result={}
    for i,(name,rows) in enumerate(defaults.items()):
        w,h=len(rows[0]),len(rows)
        for y in range(12):
            for x in range(12):
                if (x>=w or y>=h) and pixels[(12*i+y)*12+x]!=WHITE:
                    raise ValueError(f'{name} : conserver les marges blanches / keep padding white ({w} x {h})')
        result[name]=[''.join('#' if pixels[(12*i+y)*12+x]==BLACK else '.' for x in range(w)) for y in range(h)]
    if any('#' in row for row in result['tile_air']):raise ValueError('Air : laisser blanc / leave white')
    return result

def level():
    path=HERE/'level_01_layout.bmp'
    if not path.exists():write_bmp(path,WIDTH,HEIGHT,[COLOURS[tile] for tile in default_level()])
    w,h,pixels=read_bmp(path)
    if (w,h)!=(WIDTH,HEIGHT):raise ValueError('Plan : 96 x 6 pixels requis / Layout: 96 x 6 pixels required')
    lookup={colour:i for i,colour in enumerate(COLOURS)}
    try:return bytearray(lookup[p] for p in pixels)
    except KeyError:raise ValueError('Plan : couleurs de la legende uniquement / Layout: use only legend colours') from None

def level_spec():
    path=HERE/'level_01.json'
    if not path.exists():
        spec={'name_fr':'La route des nuages','name_en':'Cloud Road','player_start':[16,28],
              'enemies':[{'x':x,'y':32,'min_x':lo,'max_x':hi,'direction':1} for x,lo,hi in ((192,184,206),(320,304,330),(400,392,410),(680,664,686))]}
        path.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    spec=json.loads(path.read_text(encoding='utf-8'))
    x,y=spec['player_start']
    if not(0<=x<=756 and 0<=y<=36) or len(spec['enemies'])!=4:raise ValueError('Niveau : depart et quatre ennemis requis / Level: start and four enemies required')
    for enemy in spec['enemies']:
        if not(0<=enemy['min_x']<=enemy['x']<=enemy['max_x']<=758 and 0<=enemy['y']<=40 and enemy['direction'] in (-1,1)):
            raise ValueError('Patrouille ennemie invalide / Invalid enemy patrol')
    return spec

def export_views(patterns=None,cells=None):
    patterns=art() if patterns is None else patterns
    cells=level() if cells is None else cells
    width,height=WIDTH*8,HEIGHT*8
    pixels=[]
    for y in range(height):
        for x in range(width):
            rows=patterns[TILES[cells[(y//8)*WIDTH+x//8]]]
            pixels.append(BLACK if rows[y%8][x%8]=='#' else WHITE)
    write_bmp(HERE/'level_01.bmp',width,height,pixels)
    names_fr=('Air','Sol','Brique cassable','Bloc bonus','Piece','Pointes','Arrivee','Point de reprise','Bloc utilise',
              'Heros - pas A','Heros - pas B','Ennemi','Nuage','Coeur du panneau','Piece du panneau')
    names_en=('Air','Ground','Breakable brick','Bonus block','Coin','Spikes','Goal flag','Checkpoint','Used block',
              'Hero - step A','Hero - step B','Enemy','Cloud','HUD heart','HUD coin')
    spec={'cell_width':12,'cell_height':12,'frames':[],'level_palette':[]}
    for i,(name,rows) in enumerate(patterns.items()):
        spec['frames'].append({'id':i,'name':name,'fr':names_fr[i],'en':names_en[i],'x':0,'y':12*i,'width':len(rows[0]),'height':len(rows)})
        if i<9:spec['level_palette'].append({'id':i,'rgb':list(COLOURS[i]),'fr':names_fr[i],'en':names_en[i]})
    (HERE/'sprites.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')

def generate():
    patterns,cells,spec=art(),level(),level_spec()
    x,y=spec['player_start']
    out=['; FR/EN: generated from editable BMP assets.',f'PLAYER_START_X EQU {x}',f'PLAYER_START_Y EQU {y}','level_initial:']
    for p in range(0,len(cells),24):out.append('    db '+','.join(map(str,cells[p:p+24])))
    for name,rows in patterns.items():
        op='db' if name.endswith('_icon') else 'dw'
        out.append(name+': '+op+' '+','.join(str(v) for v in columns(rows)))
        if name.startswith('hero_'):out.append(name+'_left: dw '+','.join(str(v) for v in reversed(columns(rows))))
    out.extend(('tile_patterns: dw '+','.join(TILES),
                'buffer_rows: dw frame_buffer,frame_buffer+120,frame_buffer+240,frame_buffer+360','enemies_initial:'))
    for enemy in spec['enemies']:
        out.extend((f'    dw {enemy["x"]}',f'    db {enemy["y"]}',f'    dw {enemy["min_x"]},{enemy["max_x"]}',f'    db {enemy["direction"]},1'))
    (HERE/'generated.inc').write_text('\n'.join(out)+'\n',encoding='ascii')
    export_views(patterns,cells)
if __name__=='__main__':generate()
