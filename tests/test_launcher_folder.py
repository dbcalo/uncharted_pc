# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher: the game folder Browse keeps when the pick is one level off (the dump's parent
folder, or a folder inside the dump), and the error that names what was looked for. Pure Python."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher  # noqa: E402


class NearMiss(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.top = Path(folder.name) / 'Uncharted - The Nathan Drake Collection v1.02 (CUSA02320)'
        self.dump = self.top / 'CUSA02320'
        for sub in ('sce_sys', 'u1data'):
            (self.dump / sub).mkdir(parents=True)
        (self.dump / 'eboot.bin').write_bytes(b'')

    def test_the_dump_itself(self):
        self.assertEqual(launcher.game_folder_near(str(self.dump)), str(self.dump))

    def test_one_level_too_high(self):
        self.assertEqual(launcher.game_folder_near(str(self.top)), str(self.dump))

    def test_one_level_too_low(self):
        self.assertEqual(launcher.game_folder_near(str(self.dump / 'sce_sys')), str(self.dump))

    def test_a_game_dumped_on_its_own(self):
        own = self.top.parent / 'CUSA07737'
        own.mkdir()
        (own / 'big2-ps4_Shipping.elf').write_bytes(b'')
        self.assertEqual(launcher.game_folder_near(str(own)), str(own))

    def test_two_dumps_below_is_left_alone(self):
        (self.top / 'CUSA02343').mkdir()
        (self.top / 'CUSA02343' / 'eboot.bin').write_bytes(b'')
        self.assertEqual(launcher.game_folder_near(str(self.top)), str(self.top))

    def test_unrelated_folder_is_left_alone(self):
        other = self.top.parent / 'music'
        other.mkdir()
        self.assertEqual(launcher.game_folder_near(str(other)), str(other))
        self.assertEqual(launcher.game_folder_near(str(self.top.parent / 'missing')),
                         str(self.top.parent / 'missing'))


class MissingGameMessage(unittest.TestCase):
    def test_names_folder_and_file(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        ui = mock.Mock()
        ui.process = None
        ui.app = {**launcher.APP_DEFAULTS, 'game_dir': folder.name, 'start': 'u2'}
        launcher.Launcher.play(ui)
        text = ui.messagebox.showerror.call_args[0][1]
        self.assertIn('This game is not in the chosen folder.', text)
        self.assertIn('big2-ps4_Shipping.elf', text)
        self.assertIn(folder.name, text)


if __name__ == '__main__':
    unittest.main()
