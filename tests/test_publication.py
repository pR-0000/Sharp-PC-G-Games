"""Release checks reject missing files, corrupted programs and private reports."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from check_publication import check_collection,decode_hex
from package_collection import included


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.build=self.root/'games/sample/build/g850'
        self.build.mkdir(parents=True)
        (self.build/'sample.bin').write_bytes(b'\xc9')
        (self.build/'sample.ihx').write_text(':01010000C935\n:00000001FF\n',encoding='ascii')
        self.spec={'origin':'0100','programs':{'sample':{
            'bytes':1,'last_address':'0100','user_command':'USER01FF',
            'sha256_bin':hashlib.sha256((self.build/'sample.bin').read_bytes()).hexdigest(),
            'sha256_ihx':hashlib.sha256((self.build/'sample.ihx').read_bytes()).hexdigest()}}}
        (self.build/'manifest.json').write_text(json.dumps(self.spec),encoding='utf-8')
        (self.root/'README.md').write_text(
            '<a id="francais"></a>\n\n[English](#english)\n\n<a id="english"></a>\n',encoding='utf-8')

    def tearDown(self):self.temp.cleanup()

    def test_decoding_rejects_corruption_overlap_and_missing_or_duplicate_eof(self):
        data=':01010000C935\n:00000001FF\n'
        self.assertEqual(decode_hex(data),(0x100,b'\xc9'))
        for invalid in (data.replace('C935','C934'),data.splitlines()[0],
                        data+':00000001FF\n',data.splitlines()[0]+'\n'+data):
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):decode_hex(invalid)

    def test_reports_and_personal_files_excluded_but_assets_and_agents_retained(self):
        for name in ('.local/captures.json','ROM dumps/bank00.bin','rom-dumps/rom.bin',
                     'games/quest/build/timing_comparison.json','games/quest/build/cpu_validation.json',
                     'games/quest/TIMING_PATCH_EN.md','games/pocket-invaders/docs/capture_fr.json',
                     'sharp_pc_g_link.ini','build/sample.sym'):
            self.assertFalse(included(self.root/name,self.root),name)
        for name in ('games/quest/tiles.json','games/pocket-jumper/sprites.bmp',
                     'games/pocket-rally/tracks.json','build/manifest.json','build/sample.bin'):
            self.assertTrue(included(self.root/name,self.root),name)

    def test_complete_fixture_passes_and_changed_binary_fails(self):
        self.assertEqual(check_collection(self.root,included)['programs'],1)
        (self.build/'sample.bin').write_bytes(b'\x00')
        with self.assertRaisesRegex(ValueError,'changed program'):check_collection(self.root,included)

    def test_g850_rejects_user_reservation_above_firmware_safe_limit(self):
        self.spec['target']='PC-G850'
        for reservation in ('USER6CFF','USER76E2','USER76FF','USER77FF','USER7FFF'):
            self.spec['programs']['sample']['user_command']=reservation
            (self.build/'manifest.json').write_text(json.dumps(self.spec),encoding='utf-8')
            with self.subTest(reservation=reservation):
                if int(reservation[4:],16)<=0x76E2:
                    self.assertEqual(check_collection(self.root,included)['programs'],1)
                else:
                    with self.assertRaisesRegex(ValueError,'G850 USER reservation'):
                        check_collection(self.root,included)

    def test_broken_link_anchor_and_unlisted_binary_are_rejected(self):
        readme=self.root/'README.md'
        original=readme.read_text(encoding='utf-8')
        for link in ('[Missing](missing.md)','[Anchor](#absent)'):
            readme.write_text(original+'\n'+link,encoding='utf-8')
            with self.assertRaises(ValueError):check_collection(self.root,included)
        readme.write_text(original,encoding='utf-8')
        (self.build/'unlisted.bin').write_bytes(b'\xc9')
        with self.assertRaisesRegex(ValueError,'missing from manifests'):check_collection(self.root,included)

    def test_legacy_hex_and_mixed_target_folders_are_rejected(self):
        legacy=self.build/'sample.hex'
        legacy.write_bytes((self.build/'sample.ihx').read_bytes())
        with self.assertRaisesRegex(ValueError,'Use .ihx'):check_collection(self.root,included)
        legacy.unlink()
        original=self.build/'manifest.json'
        mixed=self.build.parent/'manifest.json'
        original.rename(mixed)
        with self.assertRaisesRegex(ValueError,'grouped by machine'):check_collection(self.root,included)


if __name__=='__main__':unittest.main()
