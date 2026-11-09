"""FR/EN: check public links, manifests and distributable binaries, read-only."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote, urlsplit

from cli_i18n import Parser, pick

ROOT = Path(__file__).resolve().parents[1]


def decode_hex(text):
    """Decode and check contiguous 16-bit Intel HEX data and its final EOF."""
    data=bytearray()
    origin=None
    ended=False
    for line in text.splitlines():
        if not line.strip():continue
        if ended or not line.startswith(':'):raise ValueError('Invalid HEX order or trailing data')
        record=bytes.fromhex(line[1:])
        if len(record)<5 or len(record)!=record[0]+5 or sum(record)&255:
            raise ValueError('Invalid HEX checksum or length')
        size,address,kind=record[0],int.from_bytes(record[1:3],'big'),record[3]
        if kind==1:
            if size or address:raise ValueError('Invalid HEX EOF')
            ended=True
        elif kind==0:
            if origin is None:origin=address
            if address!=origin+len(data) or address+size>65536:
                raise ValueError('Non-contiguous or overlapping HEX data')
            data.extend(record[4:-1])
        else:raise ValueError('Unsupported HEX record')
    if not ended or not data:raise ValueError('Missing HEX EOF or data')
    return origin,bytes(data)


def markdown_anchors(text):
    anchors=set(re.findall(r'<a\s+id="([^"]+)"',text))
    for heading in re.findall(r'^#{1,6} (.+)',text,re.M):
        heading=re.sub(r'[^\w\- ]','',heading.lower(),flags=re.UNICODE)
        anchors.add(heading.replace(' ','-'))
    return anchors


def check_collection(root, include):
    root=root.resolve()
    files={p.resolve() for p in root.rglob('*') if p.is_file() and include(p,root)}
    manifest_count=program_count=0
    represented=set()
    for manifest in sorted(p for p in files if p.name=='manifest.json'):
        spec=json.loads(manifest.read_text(encoding='utf-8'))
        programs=spec.get('programs')
        if not programs:raise ValueError(f'Empty program manifest: {manifest}')
        origin=int(spec['origin'],16)
        for name,info in programs.items():
            binary=manifest.parent/(name+'.bin')
            hexfile=binary.with_suffix('.hex')
            for path,key in [(binary,'sha256_bin'),(hexfile,'sha256_hex')]:
                if path not in files or hashlib.sha256(path.read_bytes()).hexdigest()!=info[key]:
                    raise ValueError(f'Missing or changed program: {path.relative_to(root)}')
            data=binary.read_bytes()
            if len(data)!=info['bytes'] or origin+len(data)-1!=int(info['last_address'],16):
                raise ValueError(f'Wrong memory size: {name}')
            if decode_hex(hexfile.read_text(encoding='ascii'))!=(origin,data):
                raise ValueError(f'HEX/BIN mismatch: {name}')
            if int(info['user_command'][4:],16)<int(info['last_address'],16):
                raise ValueError(f'Insufficient USER reservation: {name}')
            represented.update((binary,hexfile));program_count+=1
        manifest_count+=1
    for path in files:
        if path.suffix.lower() in {'.bin','.hex'} and path not in represented:
            raise ValueError(f'Program missing from manifests: {path.relative_to(root)}')
    link_count=readme_count=0
    for path in sorted(p for p in files if p.suffix=='.md'):
        text=path.read_text(encoding='utf-8')
        if path.name=='README_EN.md':raise ValueError(f'Unmerged README: {path}')
        if path.name=='README.md':
            if not (text.find('id="francais"')>=0 and text.find('id="english"')>text.find('id="francais"')):
                raise ValueError(f'Missing language navigation: {path}')
            readme_count+=1
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',text):
            parsed=urlsplit(target)
            if parsed.scheme:continue
            destination=(path.parent/unquote(parsed.path)).resolve() if parsed.path else path
            if destination not in files and not any(p.is_relative_to(destination) for p in files):
                raise ValueError(f'Broken or unpublished link: {path.relative_to(root)} -> {target}')
            if parsed.fragment and destination.suffix=='.md' and parsed.fragment not in markdown_anchors(destination.read_text(encoding='utf-8')):
                raise ValueError(f'Unknown anchor: {path.relative_to(root)} -> {target}')
            link_count+=1
        if re.search(r'[A-Za-z]:[\\/]+Users[\\/]|/Users/|/home/|nos essais|notre essai|user confirmed|utilisateur a confirmé',text,re.I):
            raise ValueError(f'Private narrative or personal path: {path.relative_to(root)}')
    return {'files':len(files),'manifests':manifest_count,'programs':program_count,
            'readmes':readme_count,'relative_links':link_count}


def main():
    from package_collection import included
    parser=Parser('Vérifier la collection avant publication, sans modifier les jeux.',
                  'Check the collection before publication without modifying games.')
    args=parser.parse_args()
    result=check_collection(ROOT,included)
    print(pick(args.lang,'Collection vérifiée : ','Collection checked: ')+json.dumps(result))


if __name__=='__main__':main()
