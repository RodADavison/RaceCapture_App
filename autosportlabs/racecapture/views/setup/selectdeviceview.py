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
from autosportlabs.uix.button.betterbutton import BetterToggleButton

SELECT_DEVICE_VIEW_KV = """
<SelectDeviceView>:
    background_source: 'resource/setup/background_device.jpg'
    info_text: 'Select your device'
    BoxLayout:
        orientation: 'vertical'
        padding: [0, dp(20)]
        spacing: [0, dp(10)]
        BoxLayout:
            size_hint_y: 0.10
        ScrollContainer:
            size_hint_y: 0.7
            do_scroll_x: False
            do_scroll_y: True
            size_hint_y: 1
            size_hint_x: 1
            GridLayout:
                id: devices
                spacing: [0, dp(10)]
                row_default_height: dp(130)
                size_hint_y: None
                height: self.minimum_height
                cols: 1
                AnchorLayout:
                    Image:
                        allow_stretch: True
                        source: 'resource/setup/device_PC_MK1.png'
                    AnchorLayout:
                        anchor_x: 'right'
                        padding: (dp(10), dp(10))
                        BetterToggleButton:
                            group: 'device'
                            size_hint: (0.45, 0.5)
                            text: 'PodiumConnect'
                            on_release: root.select_device('PC_MK1')

                AnchorLayout:
                    Image:
                        allow_stretch: True
                        source: 'resource/setup/device_RCT.png'
                    AnchorLayout:
                        anchor_x: 'right'
                        padding: (dp(10), dp(10))
                        BetterToggleButton:
                            group: 'device'
                            size_hint: (0.45, 0.5)
                            text: 'RaceCapture/Track'
                            on_release: root.select_device('RCT')

                AnchorLayout:
                    Image:
                        allow_stretch: True
                        source: 'resource/setup/device_RCP_MK3.png'
                        nocache: True
                    AnchorLayout:
                        anchor_x: 'right'
                        padding: (dp(10), dp(10))
                        BetterToggleButton:
                            group: 'device'
                            size_hint: (0.45, 0.5)
                            text: 'RaceCapture/Pro MK3'
                            on_release: root.select_device('RCP_MK3')

                AnchorLayout:
                    Image:
                        allow_stretch: True
                        source: 'resource/setup/device_RCP_Apex.png'
                        nocache: True
                    AnchorLayout:
                        anchor_x: 'right'
                        padding: (dp(10), dp(10))
                        BetterToggleButton:
                            group: 'device'
                            size_hint: (0.45, 0.5)
                            text: 'RaceCapture/Apex'
                            on_release: root.select_device('RCP_Apex')

                AnchorLayout:
                    Image:
                        allow_stretch: True
                        source: 'resource/setup/device_RCP_MK2.png'
                        nocache: True             
                    AnchorLayout:
                        anchor_x: 'right'
                        padding: (dp(10), dp(10))
                        BetterToggleButton:
                            id: racecapturepro
                            group: 'device'
                            size_hint: (0.45, 0.5)
                            text: 'RaceCapture/Pro MK2'
                            on_release: root.select_device('RCP_MK2')
        BoxLayout:
            size_hint_y: None
            height: dp(50)
"""


class SelectDeviceView(InfoView):
    """
    A setup screen that lets users select what device they have.
    """
    Builder.load_string(SELECT_DEVICE_VIEW_KV)

    def __init__(self, **kwargs):
        super(SelectDeviceView, self).__init__(**kwargs)
        self.ids.next.disabled = True

    def select_device(self, device):
        self.ids.next.disabled = False
        self.ids.next.pulsing = True
        # update our setup config with the selected device
        step = self.get_setup_step('device')
        step['device'] = device

    def on_setup_config(self, instance, value):
        self._update_ui()

    def _update_ui(self):
        # set the button that matches what's in the current config, if set
        if self.setup_config is not None:
            step = self.get_setup_step('device')
            current_device = step['device']
            current_device_button = self.ids.get(current_device)
            if current_device_button is not None:
                current_device_button.active = True
