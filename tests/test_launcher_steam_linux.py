# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher, Add to Steam on Linux (the Steam Deck AppImage): Steam under the home folder,
entries that start the AppImage, a moved AppImage, Steam closed while writing. Pure Python."""
import os
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import bbport_steam  # noqa: E402
import uncharted_launcher as launcher  # noqa: E402


def entries(vdf):
    root = bbport_steam.parse(Path(vdf).read_bytes())[0]
    return [{k: v for _t, k, v in value} for _kind, _key, value in root[0][2]]


class SteamOnLinux(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.home = Path(self.folder.name)
        self.appimage = '/home/deck/My Games/Uncharted.AppImage'
        for patch in (mock.patch.object(launcher, 'IS_LINUX', True),
                      mock.patch.object(bbport_steam, 'IS_LINUX', True),
                      mock.patch.object(Path, 'home', lambda: self.home),
                      mock.patch.dict(os.environ, {'APPIMAGE': self.appimage})):
            patch.start()
            self.addCleanup(patch.stop)

    def test_steam_folder_in_home(self):
        self.assertIsNone(bbport_steam.steam_folder())
        steam = self.home / '.local' / 'share' / 'Steam'
        (steam / 'userdata' / '123' / 'config').mkdir(parents=True)
        self.assertEqual(bbport_steam.steam_folder(), steam)
        self.assertEqual(bbport_steam.user_configs(steam), [steam / 'userdata' / '123' / 'config'])

    def test_shortcut_points_at_appimage(self):
        vdf = self.home / 'shortcuts.vdf'
        exe, _result = launcher.add_collection_shortcut(vdf)
        self.assertEqual(exe, PurePosixPath(self.appimage))
        (entry,) = entries(vdf)
        self.assertEqual(entry['Exe'], f'"{self.appimage}"')
        self.assertEqual(entry['LaunchOptions'], '--play')
        self.assertEqual(entry['StartDir'], '"/home/deck/My Games"')

    def test_moved_appimage_replaces_entry(self):
        vdf = self.home / 'shortcuts.vdf'
        launcher.add_collection_shortcut(vdf)
        with mock.patch.dict(os.environ, {'APPIMAGE': '/run/media/deck/Card/Uncharted.AppImage'}):
            launcher.add_collection_shortcut(vdf)
            launcher.add_steam_shortcuts(vdf)
            launcher.add_steam_shortcuts(vdf)
        names = [(e['AppName'], e['Exe']) for e in entries(vdf)]
        self.assertEqual(len(names), 3)
        self.assertTrue(all(exe == '"/run/media/deck/Card/Uncharted.AppImage"' for _n, exe in names))

    def test_per_game_entries(self):
        vdf = self.home / 'shortcuts.vdf'
        launcher.add_steam_shortcuts(vdf)
        self.assertEqual([e['LaunchOptions'] for e in entries(vdf)], ['--play u1', '--play u2', '--play u3'])

    def test_steam_running_from_proc(self):
        proc = self.home / 'proc'
        (proc / '42').mkdir(parents=True)
        (proc / '42' / 'comm').write_text('steam\n')
        (proc / '43').mkdir()
        (proc / '43' / 'comm').write_text('steamwebhelper\n')
        self.assertTrue(bbport_steam.steam_running(proc))
        (proc / '42' / 'comm').write_text('bash\n')
        self.assertFalse(bbport_steam.steam_running(proc))

    def test_shutdown_command(self):
        self.assertEqual(bbport_steam.shutdown_command(Path('/x/Steam')), ['steam', '-shutdown'])
        with mock.patch.object(bbport_steam, 'IS_LINUX', False):
            self.assertEqual(bbport_steam.shutdown_command(Path('C:/Steam')), [str(Path('C:/Steam/steam.exe')), '-shutdown'])

    def test_running_steam_is_closed(self):
        steam = self.home / 'Steam'
        (steam / 'userdata' / '7' / 'config').mkdir(parents=True)
        ui = mock.Mock()
        ui.messagebox.askyesno.return_value = True
        ui.app = {**launcher.APP_DEFAULTS}
        running = iter([True, False])
        with mock.patch.object(bbport_steam, 'steam_folder', return_value=steam), \
                mock.patch.object(bbport_steam, 'steam_running', lambda: next(running)), \
                mock.patch.object(launcher.subprocess, 'Popen') as popen, \
                mock.patch.object(launcher.time, 'sleep'), \
                mock.patch.object(launcher, 'open_target') as open_target, \
                mock.patch.object(launcher, 'add_steam_collection') as add:
            launcher.Launcher.write_to_steam(ui, 'collection')
        popen.assert_called_once()
        self.assertEqual(popen.call_args[0][0], ['steam', '-shutdown'])
        add.assert_called_once()
        open_target.assert_called_once_with('steam://open/games')


if __name__ == '__main__':
    unittest.main()
