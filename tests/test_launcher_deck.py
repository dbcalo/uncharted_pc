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


if __name__ == '__main__':
    unittest.main()
