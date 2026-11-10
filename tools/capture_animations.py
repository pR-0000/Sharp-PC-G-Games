"""FR/EN: G850 animated LCD captures of the distributed Z80 games.

Requires Windows, external g800, Pillow and z80==1.2.0. Each temporary
snapshot renders through g800 and its playfield is checked against Z80
execution. GIF timing is illustrative, not a hardware speed measurement.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile

from build import intel_hex
from capture_lcd import capture
from cli_i18n import Parser, pick
from package_collection import included

ROOT = Path(__file__).resolve().parents[1]
GAMES = {
    'vector': ('pocket-vector', 'vector_g850_race_g800.gif', 160),
    'clash': ('pocket-clash', 'clash_g850_battle_g800.gif', 180),
    'jumper': ('pocket-jumper', 'jumper_g850_scroll_g800.gif', 160),
    'rally': ('pocket-rally', 'rally_g850_scroll_g800.gif', 160),
    'depths2': ('pocket-depths-2', 'depths2_g850_turn_g800.gif', 180),
}


def load_checks(game, filename='check_g850.py'):
    folder = ROOT / 'games' / game
    sys.path.insert(0, str(folder))
    sys.modules.pop('assets', None)
    spec = importlib.util.spec_from_file_location('animation_' + game.replace('-', '_'), folder / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scenes(game):
    """Yield live CPU states, renderer and pixel-comparison bounds."""
    folder = GAMES[game][0]
    if game == 'vector':
        module = load_checks(folder, 'check_vector.py')
        machine = module.VectorMachine()
        machine.initialise(1)
        for _ in range(12):
            machine.call('race_tick')
        for _ in range(60):
            for _ in range(2):
                machine.call('race_tick')
            assert machine.byte('phase') == 1
            yield machine, 'show_frame', (0, 0, 144, 48)
    elif game == 'clash':
        module = load_checks(folder, 'check_clash.py')
        machine = module.ClashG850()
        machine.tap(0x0B)  # The game's own demonstration AI controls both fighters.
        for _ in range(96):
            machine.poll()
        for _ in range(60):
            for _ in range(3):
                machine.poll()
            assert machine.byte('phase') == 1
            yield machine, 'draw_game', (0, 8, 144, 40)
    elif game == 'jumper':
        module = load_checks(folder)
        machine = module.JumperG850()
        machine.tap(0x0B)  # Built-in demonstration, with real collisions and jumps.
        for _ in range(16):
            machine.poll()
        for _ in range(56):
            for _ in range(2):
                machine.poll()
            assert machine.byte('phase') == 1
            yield machine, 'draw_game', (0, 8, 144, 40)
    elif game == 'rally':
        module = load_checks(folder)
        from check_rally import reference_driver, ROUTES
        machine = module.RallyG850()
        machine.start()
        for _ in range(28):
            machine.poll(reference_driver(machine.car(), ROUTES[0]))
        for _ in range(64):
            for _ in range(2):
                machine.poll(reference_driver(machine.car(), ROUTES[0]))
            assert machine.byte('phase') == 1
            yield machine, 'draw_game', (0, 8, 144, 40)
    else:
        module = load_checks(folder)
        machine = module.DepthsG850()
        machine.start()
        # Prepared camera sweep; all perspective and pixels come from the DDA.
        machine.set_word('player_x', 0x0380)
        machine.set_word('player_y', 0x0D80)
        angles = list(range(144, 241, 8))
        for angle in angles + angles[-2:0:-1]:
            machine.set_byte('angle', angle)
            yield machine, 'render', (0, 8, 144, 40)


def make_animation(game, emulator, language):
    from PIL import Image
    folder, filename, duration = GAMES[game]
    destination = ROOT / 'games' / folder / 'docs' / filename
    pictures = []
    verified_pixels = 0
    with tempfile.TemporaryDirectory(prefix='sharp-lcd-animation-') as temporary:
        temporary = Path(temporary)
        for index, (machine, renderer, region) in enumerate(scenes(game)):
            # Keep live gameplay unchanged by the additional rendering pass.
            memory = bytes(machine.cpu.memory)
            data = bytearray(memory[256:machine.sym['program_end']])
            target = machine.sym[renderer]
            data[:6] = bytes((0xCD, target & 255, target >> 8, 0xC3, 3, 1))
            fixture = temporary / 'frame.ihx'
            fixture.write_text(intel_hex(data, 256), encoding='ascii')
            if game == 'vector':
                machine.call(renderer)
                expected = machine.native_frame()
            else:
                machine.routine(renderer)
                expected = machine.pixels()
            machine.cpu.memory[:] = memory
            picture_path = temporary / 'frame.png'
            capture(emulator, fixture, picture_path, model='PC-G850')
            with Image.open(picture_path) as source:
                picture = source.convert('RGB')
            thumb = picture.resize((144, 48), Image.Resampling.NEAREST)
            tones = sorted({color for count, color in thumb.getcolors(144 * 48)}, key=sum)
            assert len(tones) == 2, (game, index, 'LCD palette')
            left, top, width, height = region
            for y in range(top, top + height):
                for x in range(left, left + width):
                    wanted = bool(expected[(y // 8) * 144 + x] & (1 << (y & 7)))
                    assert (thumb.getpixel((x, y)) == tones[0]) == wanted, (game, index, x, y)
            verified_pixels += width * height
            pictures.append(picture)
            if index % 12 == 0:
                print(f'{game}: {index + 1} '+pick(language, 'images vérifiées', 'verified frames'), flush=True)
    assert len(pictures) >= 20
    assert len({hashlib.sha256(p.tobytes()).digest() for p in pictures}) >= 12
    pictures[0].save(destination, save_all=True, append_images=pictures[1:],
                     duration=duration, loop=0, optimize=True)
    with Image.open(destination) as animation:
        assert animation.is_animated and animation.n_frames >= 12 and animation.size == (864, 288)
        assert animation.info['loop'] == 0
        saved_frames = animation.n_frames
    return {'image': destination.relative_to(ROOT).as_posix(), 'model': 'PC-G850',
            'source': 'Distributed Z80 renderer in g800; native LCD text; no Sharp ROM.',
            'scene': 'Prepared DDA camera sweep' if game == 'depths2' else 'Continuous Z80 gameplay',
            'frames': saved_frames, 'sampled_frames': len(pictures), 'duration_ms': duration,
            'timing': 'Illustrative presentation cadence, not a hardware benchmark',
            'verified_playfield_pixels': verified_pixels,
            'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}


def main():
    parser = Parser('Créer les GIF des jeux G850, LCD uniquement.',
                    'Create G850 game GIFs, LCD only.')
    parser.add_argument('--emulator', default=os.environ.get('G800', 'g800'))
    parser.add_argument('--game', choices=('all', *GAMES), default='all')
    args = parser.parse_args()
    emulator = shutil.which(args.emulator)
    if not emulator:
        parser.error('g800: --emulator / G800 / PATH')
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in ROOT.rglob('*')
              if p.is_file() and p.suffix in {'.bin', '.ihx'} and included(p)}
    output = ROOT / '.local' / 'animated-gallery'
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    for game in GAMES if args.game == 'all' else (args.game,):
        reports.append(make_animation(game, emulator, args.lang))
        # Save progress so a later interrupted run still has an audit trail.
        (output / (game + '.json')).write_text(json.dumps(reports[-1], indent=2) + '\n', encoding='utf-8')
        print(reports[-1]['image'], flush=True)
    assert all(hashlib.sha256(p.read_bytes()).digest() == digest for p, digest in before.items())
    print(pick(args.lang, 'GIF vérifiés : ', 'Verified GIFs: ') + str(len(reports)))


if __name__ == '__main__':
    main()
