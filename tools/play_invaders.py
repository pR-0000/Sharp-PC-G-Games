"""FR/EN: launch Pocket Invaders in separately installed g800, without a ROM."""
from pathlib import Path
import os
import shutil
import subprocess
from cli_i18n import Parser,pick
ROOT=Path(__file__).resolve().parents[1]
parser=Parser('Jouer a Pocket Invaders dans g800 sans ROM.','Play Pocket Invaders in g800 without a ROM.')
parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
args=parser.parse_args();emulator=shutil.which(args.emulator)
if not emulator:parser.error(pick(args.lang,'g800 absent : indiquer --emulator.','g800 missing: use --emulator.'))
program=ROOT/f'games/pocket-invaders/build/invaders_{args.lang.upper()}.hex'
subprocess.Popen([emulator,'-machine=PC-G801','-rom_dir=','-ram_path=','-basic_path=','-emulate_iocs=y',
                  '-clock=4000','-zoom=6','-use_joy=n',str(program),'100'],cwd=Path(emulator).resolve().parent)
print(pick(args.lang,'Pocket Invaders lance ; ENTER pour jouer, M pour les commandes.','Pocket Invaders started; ENTER to play, M for controls.'))
