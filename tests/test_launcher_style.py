# SPDX-License-Identifier: GPL-2.0-or-later
"""Uncharted launcher's ttk style: what Tk's own dialogs read from it. On Linux the folder picker
(tkfbox.tcl, iconlist.tcl) draws its file list with Treeview's background and foreground; the clam
theme's white Treeview with the launcher's light text was unreadable on the Steam Deck."""
import sys
import unittest
from unittest import mock

from paths import ROOT

sys.path.insert(0, str(ROOT / 'launcher'))
import uncharted_launcher as launcher  # noqa: E402

try:
    import tkinter
    from tkinter import ttk
    ROOT_WINDOW = tkinter.Tk()
    ROOT_WINDOW.withdraw()
except Exception:  # no Tk or no display
    ROOT_WINDOW = None


@unittest.skipIf(ROOT_WINDOW is None, 'needs Tk and a display')
class DialogColours(unittest.TestCase):
    def setUp(self):
        ui = mock.Mock()
        ui.root, ui.tk, ui.ttk, ui.dpi = ROOT_WINDOW, tkinter, ttk, 1.0
        ui.px = lambda n: n
        ui.font_ui = ui.font_ui_sm = ui.font_ui_md = ('TkDefaultFont', 10)
        ui.brand_family = 'TkDefaultFont'
        ui.check_images = lambda: launcher.Launcher.check_images(ui)
        launcher.Launcher.style(ui)
        self.style = ttk.Style(ROOT_WINDOW)

    def test_folder_picker_list_is_dark_with_light_text(self):
        # the lookups iconlist.tcl makes for its canvas and its file names
        self.assertEqual(self.style.lookup('Treeview', 'background'), launcher.CARD)
        self.assertEqual(self.style.lookup('Treeview', 'foreground'), launcher.TEXT)


if __name__ == '__main__':
    unittest.main()
