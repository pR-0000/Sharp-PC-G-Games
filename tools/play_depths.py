"""FR: lancer le FPS dans g800. EN: launch the FPS in g800."""
from pathlib import Path
import os
import shutil
import subprocess
from cli_i18n import Parser,pick

ROOT=Path(__file__).resolve().parents[1]
parser=Parser('Jouer a Pocket Depths dans g800 sans ROM.','Play Pocket Depths in g800 without a ROM.')
parser.add_argument('--emulator',default=os.environ.get('G800','g800'),help=pick(parser.lang,'Chemin g800, G800 ou PATH.','g800 path, G800 or PATH.'))
parser.add_argument('--lite',action='store_true',help=pick(parser.lang,'Edition PC-G801 Lite.','PC-G801 Lite edition.'))
args=parser.parse_args()
emulator=shutil.which(args.emulator)
if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
edition='lite_' if args.lite else ''
program=ROOT/f'games/pocket-depths/build/depths_{edition}{args.lang.upper()}.hex'
subprocess.Popen([emulator,'-machine='+('PC-G801' if args.lite else 'PC-G805'),'-rom_dir=','-ram_path=','-basic_path=','-emulate_iocs=y','-clock=4000',
                  '-zoom=6','-use_joy=n',str(program),'100'],cwd=Path(emulator).resolve().parent)
print(pick(args.lang,'Jeu lance ; ENTER pour commencer.','Game launched; ENTER to start.'))
