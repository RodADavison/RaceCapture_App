#
# Race Capture App
#
# Copyright (C) 2014-2017 Autosport Labs
#
# This file is part of the Race Capture App
#
# This is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should
# have received a copy of the GNU General Public License along with
# this code. If not, see <http://www.gnu.org/licenses/>.

import kivy
from __builtin__ import True
kivy.require('1.10.0')
from kivy.clock import Clock
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.logger import Logger
from autosportlabs.racecapture.views.setup.infoview import InfoView
from autosportlabs.racecapture.views.configuration.rcp.wireless.cellularconfigview import CellSettingsView
import webbrowser
from utils import is_mobile_platform
from fieldlabel import FieldLabel
from valuefield import ValueField
from settingsview import SettingsSwitch, SettingsMappedSpinner
import json
import os


class CellServiceView(InfoView):
    """
    A setup screen that lets them set up their cellular carrier
    """
    Builder.load_string("""
<CellServiceView>:
    background_source: 'resource/setup/background_cellservice.jpg'
    info_text: 'Select your cellular service'
    BoxLayout:
        padding: (dp(10), dp(20))
        spacing: (dp(10), dp(10))
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(25)
        CellSettingsView:
            id: cell_settings
            size_hint_y: 0.8
        BoxLayout:
            size_hint_y: 0.1    
            size_hint_y: None
            height: dp(50)
    """)

    def __init__(self, **kwargs):
        super(CellServiceView, self).__init__(**kwargs)

    def on_rc_config(self, instance, value):
        self.ids.cell_settings.rc_config = value

    def on_base_dir(self, instance, value):
        self.ids.cell_settings.base_dir = value

    def on_setup_config(self, instance, value):
        self.ids.next.disabled = False
        self.ids.next.pulsing = False

    def select_next(self):
        self.ids.next.disabled = True
        def do_next():
            super(CellServiceView, self).select_next()

        cfg = self.rc_config.connectivityConfig
        cfg.stale = True

        self.write_rcp_config('Updating Configuration ... ', do_next)


