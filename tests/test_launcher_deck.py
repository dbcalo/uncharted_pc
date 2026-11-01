# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher on a Steam Deck: detection, the Deck's defaults, the first page.
Pure Python: runs on any host with IS_LINUX and the DMI folder patched."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher  # noqa: E402


def dmi(folder, vendor, product):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'board_vendor').write_text(vendor + '\n')
    (folder / 'product_name').write_text(product + '\n')
    return folder


class Detection(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def test_deck_detected(self):
        with mock.patch.object(launcher, 'IS_LINUX', True):
            self.assertTrue(launcher.is_steam_deck(dmi(self.root / 'oled', 'Valve', 'Galileo')))
            self.assertTrue(launcher.is_steam_deck(dmi(self.root / 'lcd', 'Valve', 'Jupiter')))
            self.assertFalse(launcher.is_steam_deck(dmi(self.root / 'other', 'Valve', 'Other')))
            self.assertFalse(launcher.is_steam_deck(dmi(self.root / 'pc', 'ASUSTeK', 'Jupiter')))
            self.assertFalse(launcher.is_steam_deck(self.root / 'missing'))
        with mock.patch.object(launcher, 'IS_LINUX', False):  # never on Windows
            self.assertFalse(launcher.is_steam_deck(dmi(self.root / 'win', 'Valve', 'Galileo')))

    def test_defaults_off_a_deck(self):
        with mock.patch.object(launcher, 'is_steam_deck', return_value=False):
            self.assertEqual(launcher.app_defaults(), launcher.APP_DEFAULTS)

    def test_window_title(self):
        with mock.patch.object(launcher, 'IS_LINUX', False):
            self.assertIn('The Nathan Drake Collection for Windows', launcher.window_title())
        with mock.patch.object(launcher, 'IS_LINUX', True):
            with mock.patch.object(launcher, 'is_steam_deck', return_value=True):
                self.assertIn('The Nathan Drake Collection for Steam Deck', launcher.window_title())
            with mock.patch.object(launcher, 'is_steam_deck', return_value=False):
                self.assertIn('The Nathan Drake Collection for Linux', launcher.window_title())


class DeckDefaults(unittest.TestCase):
    def setUp(self):
        patch = mock.patch.object(launcher, 'is_steam_deck', return_value=True)
        patch.start()
        self.addCleanup(patch.stop)
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        for patch in (mock.patch.object(launcher, 'DATA_DIR', Path(self.folder.name)),
                      mock.patch.object(launcher, 'screen_size', return_value=(1280, 800))):
            patch.start()
            self.addCleanup(patch.stop)

    def environment(self, saved):
        settings = {**launcher.app_defaults(), 'game_dir': self.folder.name, **saved}
        return launcher.game_environment(settings)

    def test_deck_defaults_apply_when_unsaved(self):
        env = self.environment({})
        self.assertEqual(env['BB_VBLANK_HZ'], '120')
        self.assertEqual(env['BB_WINDOW_SIZE'], '1280x800')
        self.assertEqual(env['BB_GAME_RES'], '1280x800')
        self.assertEqual(env['BB_FULLSCREEN'], '1')
        self.assertEqual(env['BB_PRESENT_MODE'], 'Mailbox')
        self.assertEqual(env['BB_UPSCALER'], 'off')
        self.assertEqual(env['BB_FRAME_GEN'], 'off')
        self.assertEqual((env['BB_FSR1'], env['BB_RCAS'], env['BB_RCAS_ATTENUATION']), ('1', '1', '500'))
        self.assertEqual(env['BB_JOB_SLEEP'], '1')
        self.assertEqual(env['BB_BUTTON_PROMPTS'], 'auto')
        defaults = launcher.app_defaults()
        self.assertIs(defaults['gyro_aim'], True)
        self.assertIs(defaults['gyro_builtin'], False)

    def test_saved_value_wins(self):
        self.assertEqual(self.environment({'frame_rate': '60'})['BB_VBLANK_HZ'], '60')

    def test_render_800(self):
        self.assertEqual(launcher.game_resolution(
            {'render_height': '800', 'aspect': 'window', 'fullscreen': True}, (1280, 800)), '1280x800')
        self.assertIn('800', dict(launcher.RENDER_HEIGHTS))



class FirstRun(unittest.TestCase):
    def test_first_page(self):
        self.assertEqual(launcher.first_page({}), 'game')
        self.assertEqual(launcher.first_page({**launcher.APP_DEFAULTS}), 'game')
        self.assertEqual(launcher.first_page({**launcher.APP_DEFAULTS, 'game_dir': '/x'}), 'play')
        self.assertEqual(launcher.first_page({**launcher.APP_DEFAULTS, 'game_dir_u2': '/x'}), 'play')

    def test_deck_hint(self):
        ready = {**launcher.APP_DEFAULTS, 'game_dir': '/x'}
        with mock.patch.object(launcher, 'is_steam_deck', return_value=True):
            self.assertEqual(launcher.deck_hint(ready), 'Next: Add to Steam, then play from Gaming Mode.')
            self.assertEqual(launcher.deck_hint({**ready, 'steam_added': True}), '')
            self.assertEqual(launcher.deck_hint({**launcher.APP_DEFAULTS}), '')  # no game folder yet
        with mock.patch.object(launcher, 'is_steam_deck', return_value=False):
            self.assertEqual(launcher.deck_hint(ready), '')

    def test_steam_added_after_writing(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        steam = Path(folder.name)
        (steam / 'userdata' / '7' / 'config').mkdir(parents=True)
        ui = mock.Mock()
        ui.app = {**launcher.APP_DEFAULTS}
        with mock.patch('bbport_steam.steam_folder', return_value=steam), \
                mock.patch('bbport_steam.steam_running', return_value=False), \
                mock.patch.object(launcher, 'add_steam_collection'), \
                mock.patch.object(launcher, 'write_control_layout'):
            launcher.Launcher.write_to_steam(ui, 'collection')
        self.assertIs(ui.app['steam_added'], True)
        self.assertEqual(launcher.APP_DEFAULTS['steam_added'], False)

    def test_failed_write_leaves_steam_added(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        steam = Path(folder.name)
        (steam / 'userdata' / '7' / 'config').mkdir(parents=True)
        ui = mock.Mock()
        ui.app = {**launcher.APP_DEFAULTS}
        with mock.patch('bbport_steam.steam_folder', return_value=steam), \
                mock.patch('bbport_steam.steam_running', return_value=False), \
                mock.patch.object(launcher, 'add_steam_collection', side_effect=OSError('disk')):
            launcher.Launcher.write_to_steam(ui, 'collection')
        self.assertIs(ui.app['steam_added'], False)


if __name__ == '__main__':
    unittest.main()
