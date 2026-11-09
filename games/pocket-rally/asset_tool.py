"""FR/EN: circuit and sprite previews; Pillow is optional, for previews only."""
from pathlib import Path
import sys
from assets import HERE,ROOT,ROUTES,PATTERNS,car_patterns,generate,track
sys.path.insert(0,str(ROOT/'tools'))
from cli_i18n import Parser,pick
from bitmap import write_bmp

def main():
    parser=Parser('Exporter les circuits et les sprites de Pocket Rally.','Export Pocket Rally circuits and sprites.')
    parser.add_argument('--previews',action='store_true',help=pick(parser.lang,'Apercus agrandis avec Pillow.','Enlarged previews using Pillow.'))
    args=parser.parse_args();generate()
    black,white=(0,0,0),(255,255,255)
    cars=car_patterns()
    write_bmp(HERE/'cars.bmp',7,112,[black if cars[y//7][x]>>(y%7)&1 else white for y in range(112) for x in range(7)])
    write_bmp(HERE/'tiles.bmp',4,40,[black if PATTERNS[y//4][x]>>(y%4)&1 else white for y in range(40) for x in range(4)])
    if args.previews:
        from PIL import Image,ImageDraw,ImageFont
        def font(size):
            for name in ('C:/Windows/Fonts/consola.ttf','DejaVuSans.ttf'):
                try:return ImageFont.truetype(name,size)
                except OSError:pass
            return ImageFont.load_default()
        out=HERE/'docs';out.mkdir(exist_ok=True)
        view=Image.new('RGB',(624,860),'white');d=ImageDraw.Draw(view)
        for index,names in enumerate(('Boucle cotiere / Coast loop','Chicane du port / Harbour chicane')):
            top=index*430;d.text((20,top+10),names,fill='black',font=font(18))
            im=Image.open(HERE/f'track_{index+1:02}.bmp').convert('RGB').resize((576,384),Image.Resampling.NEAREST)
            view.paste(im,(24,top+38));d.rectangle((23,top+37,600,top+422),outline=(140,140,140))
            for gate,(x,y) in enumerate(ROUTES[index]):
                xx,yy=24+x*3,top+38+y*3
                d.ellipse((xx-4,yy-4,xx+4,yy+4),fill=(30,150,50) if gate==0 else (210,60,40))
                d.text((xx+5,yy-13),str(gate),fill=(160,30,30),font=font(13))
        view.save(out/'tracks_preview.png');view.save(HERE/'tracks_guide.bmp')
    print(pick(args.lang,'BMP exportes. Les plans colores sont les sources editables.','BMP files exported. Colour layouts are the editable sources.'))
if __name__=='__main__':main()
