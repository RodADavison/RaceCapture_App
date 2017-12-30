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
from kivy.clock import Clock
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.views.setup.infoview import InfoView
from utils import  is_android, is_ios
from autosportlabs.uix.progressspinner import ProgressSpinner
from autosportlabs.uix.button.betterspinner import BetterSpinner

SELECT_CONNECTION_VIEW_KV = """
<SelectConnectionView>:
    background_source: 'resource/setup/background_connection.jpg'
    info_text: 'Setup your connection'
    Image:
        id: device
        allow_stretch: True
        size_hint_x: 0.6
    AnchorLayout:
        anchor_x: 'right'
        padding: (dp(10), dp(10))
        BoxLayout:
            size_hint: (0.7, 1.0)
            spacing: dp(10)
            orientation: 'vertical'
            BoxLayout:
                size_hint_y: 0.2
            BoxLayout:
                canvas.before:
                    Color:
                        rgba: ColorScheme.get_dark_background_translucent()
                    Rectangle:
                        pos: self.pos
                        size: self.size
                padding: (dp(10), dp(10))
                spacing: dp(10)
                orientation: 'vertical'
                size_hint_y: 0.6
                BoxLayout:
                    size_hint_y: 0.7
                    BetterSpinner:
                        size_hint: (0.6, 0.7)
                        id: connection_types
                        font_size: self.height * 0.3
                        on_text: root.on_connection_type(self.text)
                FieldLabel:
                    size_hint_y: 0.3
                    id: connection_help
                    shorten: False
                    font_size: self.height * 0.4
                    halign: 'center'
            BoxLayout:
                canvas.before:
                    Color:
                        rgba: ColorScheme.get_dark_background_translucent()
                    Rectangle:
                        pos: self.pos
                        size: self.size
            
                orientation: 'horizontal'
                size_hint_y: 0.2
                FieldLabel:
                    size_hint_x: 0.8
                    halign: 'center'
                    id: connection_status_note
                    font_size: self.height * 0.4
                AnchorLayout:
                    size_hint_x: 0.2
                    ProgressSpinner:
                        size_hint_y: 0.8
                        id: progress_spinner
                    IconButton:
                        id: connection_status
                        color: ColorScheme.get_happy()
                        text: ''
            BoxLayout:
                size_hint_y: 0.2
"""

class SelectConnectionView(InfoView):
    """
    A setup screen that lets users select the connection they want to use for RaceCapture
    """
    Builder.load_string(SELECT_CONNECTION_VIEW_KV)
    CONNECTION_CHECK_INTERVAL = 0.5

    CONNECTION_NOTES = {'USB':'Plug your system into USB',
                        'WiFi':'Ensure your handheld is already connected to the RaceCapture WiFi network',
                        'Bluetooth': 'Ensure your handheld is paired with the RaceCapture Bluetooth'}

    CONNECTION_TYPES = {'USB':'Serial',
                        'WiFi':'WiFi',
                        'Bluetooth':'Bluetooth'}

    CHANGE_CONNECTION_DELAY = 2.0


    def __init__(self, **kwargs):
        super(SelectConnectionView, self).__init__(**kwargs)
        self._screen_active = True
        self.ids.next.disabled = True
        self._init_ui()

    def on_rc_api(self, instance, value):
        self._init_ui()
        self._start_connection_check()

    def on_setup_config(self, instance, value):
        self._init_ui()

    def _get_image_for_device(self, device):
        return 'resource/setup/device_{}.png'.format(device)

    def _get_supported_connection_list(self, device):
        supported_connections = []
        if not self.rc_api.is_wireless_connection:
            supported_connections.append('USB')
        else:
            if is_android() and (device in ['RCP_MK2', 'RCP_MK3', 'RCP_Apex']):
                supported_connections.append('Bluetooth')
            supported_connections.append('WiFi')

        return supported_connections

    def _init_ui(self):
        if not self.setup_config or not self.rc_api:
            return

        device_step = self.get_setup_step('device')
        device = device_step['device']

        supported_connections = self._get_supported_connection_list(device)


        # force the user to select their connection if there are multiple choices
        connection_spinner = self.ids.connection_types
        connection_spinner.values = supported_connections
        default_connection_type = supported_connections[0]
        connection_spinner.text = default_connection_type
        self._update_connection_type(default_connection_type)
        self._update_device_image()

    @property
    def _device_connected(self):
        return True if self.rc_api is not None and self.rc_api.connected else False

    def _update_connection_note(self, connection_type):
        connected = self._device_connected
        help_text = SelectConnectionView.CONNECTION_NOTES.get(connection_type)
        if help_text is None or connected:
            help_text = ''

        self.ids.connection_help.text = help_text

        self.ids.connection_status_note.text = 'Connected' if connected else 'Waiting for connection'

    def _update_connection_type(self, connection_type):
        # convert display connection type to internal connection type code
        connection_type_code = SelectConnectionView.CONNECTION_TYPES[connection_type]
        Clock.schedule_once(lambda dt: self.settings.userPrefs.set_pref('preferences', 'conn_type', connection_type_code), SelectConnectionView.CHANGE_CONNECTION_DELAY)

    def on_connection_type(self, connection_type):
        self._update_connection_note(connection_type)
        self._update_connection_type(connection_type)

    def _start_connection_check(self):
        if self._screen_active:
            Clock.schedule_once(lambda dt: self._check_connection_status(), SelectConnectionView.CONNECTION_CHECK_INTERVAL)

    def _update_device_image(self, device=None):
        # update the device image; if the device is passed in,
        # update the current configuration
        device_step = self.get_setup_step('device')
        if device is None:
            device = device_step['device']
        else:
            device_step['device'] = device
        self.ids.device.source = self._get_image_for_device(device)

    def _check_connection_status(self):
        if self.rc_api.connected:
            self.ids.progress_spinner.stop_spinning()
            self.ids.connection_status.text = u'\uf00c'
            self.ids.next.disabled = False
            self.ids.next.pulsing = True
            connected_version = self.rc_api.connected_version
            device = None if connected_version is None else connected_version.name
            self._update_device_image(device=device)
        else:
            self.ids.progress_spinner.start_spinning()
            self.ids.connection_status.text = ''
            self.ids.next.disabled = True

        self._update_connection_note(self.ids.connection_types.text)
        self._start_connection_check()

    def on_enter(self, *args):
        self._screen_active = True

    def on_leave(self, *args):
        super(SelectConnectionView, self).on_leave(args)
        self._screen_active = False
        self.ids.progress_spinner.stop_spinning()
