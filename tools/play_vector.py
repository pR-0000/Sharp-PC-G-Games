"""FR: lancer Pocket Vector sur g800. EN: launch Pocket Vector in g800."""
from pathlib import Path
import os
import shutil
import subprocess
from cli_i18n import Parser,pick

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=Parser('Jouer a Pocket Vector PC-G850 dans g800 sans ROM.',
                  'Play Pocket Vector PC-G850 in g800 without a ROM.')
    parser.add_argument('--emulator',default=os.environ.get('G800','g800'))
    parser.add_argument('--target',choices=('g850','g80x-32k'),default='g850')
    parser.add_argument('--clock',type=int)
    args=parser.parse_args();emulator=shutil.which(args.emulator)
    if not emulator:parser.error('g800: --emulator / G800 / PATH')
    native=args.target=='g850'
    folder=ROOT/'games/pocket-vector/build'/('g850' if native else 'g80x-32k')
    program=folder/f'vector_{"" if native else "g80x_32k_"}{args.lang.upper()}.ihx'
    if not program.is_file():parser.error(pick(args.lang,'Reconstruire Pocket Vector.','Rebuild Pocket Vector.'))
    subprocess.Popen([emulator,'-machine='+('PC-G850' if native else 'PC-G801'),'-rom_dir=','-ram_path=','-basic_path=',
        '-emulate_iocs=y','-clock='+str(args.clock or (8000 if native else 4000)),'-zoom=6','-use_joy=n',str(program),'100'],
        cwd=Path(emulator).resolve().parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(pick(args.lang,'Pocket Vector lance : fleches pour choisir, ENTER pour valider, D pour la demo, M pour l’aide.',
               'Pocket Vector started: arrows to choose, ENTER to confirm, D for demo, M for help.'))


if __name__=='__main__':main()
