"""FR: lancer Pocket Clash sur g800. EN: launch Pocket Clash in g800."""
from pathlib import Path
import os
import shutil
import subprocess
from cli_i18n import Parser,pick

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=Parser('Jouer a Pocket Clash PC-G850 dans g800 sans ROM.',
                  'Play Pocket Clash PC-G850 in g800 without a ROM.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--target',choices=('g850','g80x-32k'),default='g850')
    parser.add_argument('--clock',type=int)
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    native=args.target=='g850'
    folder=ROOT/'games/pocket-clash/build'/('g850' if native else 'g80x-32k')
    program=folder/f'clash_{"g850" if native else "g80x_32k"}_{args.lang.upper()}.ihx'
    if not program.is_file():parser.error(pick(args.lang,'Reconstruire Pocket Clash.','Rebuild Pocket Clash.'))
    subprocess.Popen([emulator,'-machine='+('PC-G850' if native else 'PC-G801'),'-rom_dir=','-ram_path=','-basic_path=',
        '-emulate_iocs=y','-clock='+str(args.clock or (8000 if native else 4000)),'-zoom=6','-use_joy=n',str(program),'100'],
        cwd=Path(emulator).resolve().parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(pick(args.lang,'Pocket Clash lance : fleches pour choisir, ENTER pour valider, D pour la demo, M pour l’aide.',
               'Pocket Clash started: arrows to choose, ENTER to confirm, D for demo, M for help.'))


if __name__=='__main__':main()
