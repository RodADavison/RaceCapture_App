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
kivy.require('1.10.0')
from kivy.app import Builder
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger
from kivy.properties import StringProperty, ObjectProperty
import os
import json
from utils import *
from settingsview import SettingsSwitch, SettingsMappedSpinner
from kivy.uix.boxlayout import BoxLayout

class CellSettingsView(BoxLayout):
    Builder.load_string("""
<CellSettingsView>:
    orientation: 'vertical'
    SettingsView:
        id: cell_enable
        label_text: 'Enable on-board cellular'
        help_text: ''
        size_hint_y: 0.2
    SettingsView:
        id: cell_provider
        label_text: 'Cellular provider'
        help_text: 'Select the cellular provider, or specify custom APN'
        size_hint_y: 0.3
    ScreenManager:
        size_hint_y: 0.5
        id: custom_apn_screen
        Screen:
            name: 'blank'
            Widget:            
        Screen:
            name: 'custom'
            BoxLayout:
                orientation: 'vertical'
                GridLayout:            
                    padding: (0, dp(5))
                    cols: 2
                    FieldLabel:
                        text: 'APN Host'
                        halign: 'right'
                        padding: (dp(5),0)                                            
                    ValueField:
                        id: apn_host
                        on_text: root.on_apn_host(*args)
                GridLayout:
                    padding: (0, dp(5))
                    cols: 2
                    FieldLabel:
                        halign: 'right'
                        text: 'APN User Name'
                        padding: (dp(5),0)                                            
                    ValueField:
                        id: apn_user
                        size_hint_y: 1
                        on_text: root.on_apn_user(*args)
                GridLayout:
                    padding: (0, dp(5))
                    cols: 2
                    FieldLabel:
                        halign: 'right'
                        text: 'APN Password'
                        padding: (dp(5),0)                                            
                    ValueField:
                        id: apn_pass
                        size_hint_y: 1
                        on_text: root.on_apn_pass(*args)    
""")

    CUSTOM_APN = 'Custom APN'
    base_dir = StringProperty(None, noneallowed=True)
    rc_config = ObjectProperty()

    def __init__(self, **kwargs):
        super(CellSettingsView, self).__init__(**kwargs)
        self.register_event_type('on_modified')
        self.loaded = False
        self.cell_provider_info = {}

    def on_modified(self):
        pass

    def on_rc_config(self, instance, value):
        self.init_view()

    def on_base_dir(self, instance, value):
        self.init_view()

    def init_view(self):
        if None in [self.base_dir, self.rc_config]:
            return

        cell_enable = self.ids.cell_enable
        cell_enable.setControl(SettingsSwitch(active=self.rc_config.connectivityConfig.cellConfig.cellEnabled))
        cell_enable.control.bind(active=self.on_cell_change)

        cell_provider = self.ids.cell_provider
        cell_provider.bind(on_setting=self.on_cell_provider)
        apn_spinner = SettingsMappedSpinner()

        self.load_apn_settings_spinner(apn_spinner)
        self.apn_spinner = apn_spinner
        cell_provider.setControl(apn_spinner)
        self._update_from_config()
        self.loaded = True

    def _update_from_config(self):
        cellEnable = self.ids.cell_enable
        cell_config = self.rc_config.connectivityConfig.cellConfig
        self.ids.apn_host.text = cell_config.apnHost
        self.ids.apn_user.text = cell_config.apnUser
        self.ids.apn_pass.text = cell_config.apnPass

        existing_apn_name = self.update_controls_state()
        if existing_apn_name:
            self.apn_spinner.text = existing_apn_name

    def get_apn_setting_by_name(self, name):
        providers = self.cell_provider_info['cellProviders']
        for apn_name in providers:
            if apn_name == name:
                return providers[apn_name]
        return None

    def update_controls_state(self):
        cell_provider_info = self.cell_provider_info
        existing_apn_name = CellSettingsView.CUSTOM_APN
        show_custom_fields = True
        cellConfig = self.rc_config.connectivityConfig.cellConfig
        providers = cell_provider_info['cellProviders']
        for name in providers:
            apnInfo = providers[name]
            if apnInfo['apn_host'] == cellConfig.apnHost and apnInfo['apn_user'] == cellConfig.apnUser and apnInfo['apn_pass'] == cellConfig.apnPass:
                existing_apn_name = name
                show_custom_fields = False
                break
        self.ids.custom_apn_screen.current = 'custom' if show_custom_fields else 'blank'
        return existing_apn_name

    def modified(self):
        if self.loaded:
            self.dispatch('on_modified')

    def on_cell_change(self, instance, value):
        self.rc_config.connectivityConfig.stale = True
        self.rc_config.connectivityConfig.cellConfig.cellEnabled = value
        self.modified()

    def on_cell_provider(self, instance, value):
        apn_setting = self.get_apn_setting_by_name(value)
        known_provider = False
        if apn_setting:
            self.ids.apn_host.text = apn_setting['apn_host']
            self.ids.apn_user.text = apn_setting['apn_user']
            self.ids.apn_pass.text = apn_setting['apn_pass']
            known_provider = True
        self.ids.custom_apn_screen.current = 'blank' if known_provider else 'custom'
        self.modified()

    def on_apn_host(self, instance, value):
        self.rc_config.connectivityConfig.cellConfig.apnHost = value
        self.rc_config.connectivityConfig.stale = True
        self.modified()

    def on_apn_user(self, instance, value):
        self.rc_config.connectivityConfig.cellConfig.apnUser = value
        self.rc_config.connectivityConfig.stale = True
        self.modified()

    def on_apn_pass(self, instance, value):
        self.rc_config.connectivityConfig.cellConfig.apnPass = value
        self.rc_config.connectivityConfig.stale = True
        self.modified()

    def load_apn_settings_spinner(self, spinner):
        try:
            json_data = open(os.path.join(self.base_dir, 'resource', 'settings', 'cell_providers.json'))
            cell_provider_info = json.load(json_data)
            apn_map = {}

            apn_map['custom'] = CellSettingsView.CUSTOM_APN
            for name in cell_provider_info['cellProviders']:
                apn_map[name] = name

            spinner.setValueMap(apn_map, CellSettingsView.CUSTOM_APN)
            self.cell_provider_info = cell_provider_info
        except Exception as detail:
            Logger.error('CellSettingsView: Error loading cell providers ' + str(detail))

Builder.load_string('''
<CellularConfigView>:
    id: cellular
    cols: 1
    spacing: [0, dp(20)]
    row_default_height: dp(40)
    size_hint: [1, None]
    height: self.minimum_height
    HSeparator:
        text: 'Cellular Configuration'
        
    CellSettingsView:
        id: cell_settings
        on_modified: root.modified()
        size_hint_y: None
        height: dp(300)
''')


class CellularConfigView(GridLayout):

    def __init__(self, base_dir, rc_config, **kwargs):
        super(CellularConfigView, self).__init__(**kwargs)
        self.connectivityConfig = None
        self.register_event_type('on_modified')
        self.apnSpinner = None
        self.ids.cell_settings.base_dir = base_dir

    def config_updated(self, rc_config):
        self.ids.cell_settings.rc_config = rc_config
        self.ids.cell_settings.init_view()

    def modified(self):
        self.dispatch('on_modified')

    def on_modified(self):
        pass
