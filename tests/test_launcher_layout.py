# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher on a Steam Deck: the controller layout written with the Steam entries
(Steam Input's controller_neptune.vdf per entry name). Pure Python."""
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher  # noqa: E402


class ControlLayout(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.steam = Path(self.folder.name) / 'Steam'
        self.config = self.steam / 'userdata' / '123' / 'config'
        self.config.mkdir(parents=True)
        patch = mock.patch.object(launcher, 'IS_LINUX', True)
        patch.start()
        self.addCleanup(patch.stop)

    def layout(self, name):
        return (self.steam / 'steamapps' / 'common' / 'Steam Controller Configs' / '123' / 'config'
                / name / 'controller_neptune.vdf')

    def test_layout_folder(self):
        self.assertEqual(launcher.layout_folder(self.steam, self.config, launcher.COLLECTION_TITLE),
                         self.layout('uncharted: the nathan drake collection').parent)

    def test_layout_written_per_entry(self):
        # plain names: Windows, where the tests also run, allows no colon in a folder name
        written = launcher.write_control_layout(self.steam, self.config, ['The Collection'])
        self.assertEqual(written, [self.layout('the collection')])
        self.assertEqual(len(launcher.write_control_layout(self.steam, self.config, ['One', 'Two', 'Three'])), 3)
        self.assertTrue(self.layout('two').is_file())

    def test_layout_content(self):
        (path,) = launcher.write_control_layout(self.steam, self.config, ['The Collection'])
        text = path.read_text(encoding='utf-8')
        self.assertIn('"controller_type"\t\t"controller_neptune"', text)
        for setting, value in (('gyro_natural_sensitivity', '270'), ('flickstick_rotation_sensitivity', '2400'),
                               ('gyro_to_2d_conversion_style', '4'), ('gyro_ratchet_button_mask', '2')):
            self.assertIn(f'"{setting}"\t\t"{value}"', text)
        self.assertIn('"14"\t\t"gyro active"', text)
        for personal in ('"creator"', '"url"', 'autosave://'):  # nothing of the account it came from
            self.assertNotIn(personal, text)
        self.assertIsNone(re.search(r'7656119\d{10}', text))  # no Steam ID

    def test_existing_layout_kept(self):
        mine = self.layout('the collection')
        mine.parent.mkdir(parents=True)
        mine.write_text('my own layout')
        self.assertEqual(launcher.write_control_layout(self.steam, self.config, ['The Collection']), [])
        self.assertEqual(mine.read_text(), 'my own layout')

    def test_windows_writes_no_layout(self):
        with mock.patch.object(launcher, 'IS_LINUX', False):
            self.assertEqual(launcher.write_control_layout(self.steam, self.config, [launcher.COLLECTION_TITLE]), [])
        self.assertFalse((self.steam / 'steamapps').exists())

    def test_written_with_the_entries(self):
        ui = mock.Mock()
        ui.app = {**launcher.APP_DEFAULTS}
        with mock.patch('bbport_steam.steam_folder', return_value=self.steam), \
                mock.patch('bbport_steam.steam_running', return_value=False), \
                mock.patch.object(launcher, 'add_steam_games'), \
                mock.patch.object(launcher, 'write_control_layout') as write:
            launcher.Launcher.write_to_steam(ui, 'games')
        write.assert_called_once_with(self.steam, self.config, list(launcher.STEAM_TITLES.values()))


if __name__ == '__main__':
    unittest.main()
