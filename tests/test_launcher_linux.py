# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher on Linux (the Steam Deck AppImage): no Windows calls, run.sh, XDG folders.
Pure Python: runs on any host with IS_LINUX patched."""
import ctypes
import sys
import unittest
from pathlib import Path
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher  # noqa: E402


class NoWindows:
    """Stands in for ctypes.windll: any use is a test failure."""
    def __getattr__(self, name):
        raise AssertionError(f'ctypes.windll.{name} used on Linux')


class OnLinux(unittest.TestCase):
    def setUp(self):
        patches = [mock.patch.object(launcher, 'IS_LINUX', True),
                   mock.patch.object(ctypes, 'windll', NoWindows(), create=True)]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_run_command_uses_run_sh(self):
        self.assertEqual(launcher.run_command(), ['bash', str(launcher.PORT_DIR / 'run.sh')])

    def test_config_dir_follows_xdg(self):
        self.assertEqual(launcher.config_dir('linux', {'XDG_CONFIG_HOME': '/tmp/x'}),
                         Path('/tmp/x/uncharted-launcher'))
        self.assertEqual(launcher.config_dir('linux', {}), Path.home() / '.config' / 'uncharted-launcher')
        self.assertEqual(launcher.config_dir('win32', {'APPDATA': r'C:\AppData'}),
                         Path(r'C:\AppData') / 'uncharted-launcher')

    def test_no_windll_reached(self):
        self.assertIsNone(launcher.screen_size())
        self.assertIsNone(launcher.display_refresh_rate())
        self.assertEqual(launcher.side_buttons(), (False, False))
        launcher.attach_stdio()

    def test_game_job_is_a_process_group(self):
        process = mock.Mock(pid=4321)
        process.poll.return_value = None
        job = launcher.GameJob(process)
        with mock.patch.object(launcher.os, 'killpg', create=True) as killpg:
            self.assertTrue(job.terminate())
        killpg.assert_called_once_with(4321, launcher.signal.SIGTERM)
        job.close()

    def test_probe_without_exe(self):
        with mock.patch.object(Path, 'is_file', lambda path: path.name == 'bb-probe'):
            self.assertEqual(launcher.controller_probe_path(), launcher.PORT_DIR / 'bin' / 'bb-probe')

    def test_play_problem_is_shown(self):
        with mock.patch.object(launcher, 'load_json', return_value={}), \
                mock.patch.object(launcher, 'show_error') as show_error, \
                mock.patch.object(sys, 'argv', ['uncharted', '--play', 'u2']):
            with self.assertRaises(SystemExit) as stop:
                launcher.main()
        self.assertEqual(stop.exception.code, 2)
        show_error.assert_called_once()
        self.assertIn('is not available', show_error.call_args[0][0])

    def test_open_target_uses_xdg_open(self):
        with mock.patch.object(launcher.subprocess, 'Popen') as popen:
            launcher.open_target('steam://open/games')
        popen.assert_called_once_with(['xdg-open', 'steam://open/games'])


if __name__ == '__main__':
    unittest.main()
