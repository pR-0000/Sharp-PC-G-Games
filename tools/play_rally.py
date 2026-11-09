"""FR/EN: launch Pocket Rally in g800, without a Sharp ROM."""
from pathlib import Path
import os,shutil,subprocess
from cli_i18n import Parser,pick
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=Parser('Jouer a Pocket Rally dans g800 sans ROM.','Play Pocket Rally in g800 without a ROM.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'),
        help=pick(parser.lang,'Chemin g800, G800 ou PATH.','g800 path, G800 or PATH.'))
    parser.add_argument('--model',choices=('PC-G801','PC-G805'),default='PC-G805',
        help=pick(parser.lang,'Profil du simulateur (defaut : PC-G805).','Simulator profile (default: PC-G805).'))
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
    program=ROOT/f'games/pocket-rally/build/rally_{args.lang.upper()}.hex'
    if not program.is_file():parser.error(pick(args.lang,'Fichier de jeu absent : reconstruire la collection.','Game file missing: rebuild the collection.'))
    subprocess.Popen([emulator,'-machine='+args.model,'-rom_dir=','-ram_path=','-basic_path=',
        '-emulate_iocs=y','-clock=4000','-zoom=6','-use_joy=n',str(program),'100'],cwd=Path(emulator).resolve().parent)
    print(pick(args.lang,'Pocket Rally lance : ENTER pour jouer, M pour l’aide.','Pocket Rally launched: ENTER to play, M for help.'))
if __name__=='__main__':main()


