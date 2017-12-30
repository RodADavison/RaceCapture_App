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
from autosportlabs.racecapture.views.setup.infoview import InfoView
import webbrowser
from utils import is_mobile_platform
from fieldlabel import FieldLabel
from valuefield import ValueField
import re

class PodiumSetupView(InfoView):
    """
    A setup screen that lets them set up their Podium Device ID
    """
    Builder.load_string("""
<PodiumSetupView>:
    background_source: 'resource/setup/background_podium.jpg'
    info_text: 'Stream real-time telemetry for free to your pit crew, friends, race coaches, and fans around the world.\\n\\nSign up at [color=00BCD4][ref=podium]podium.live[/ref][/color] to get your device Id:'
    BoxLayout:
        orientation: 'vertical'
        padding: (0, dp(20))
        spacing: (0, dp(10))
        Widget:
            size_hint_y: 0.5
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            padding: (dp(10), 0)            
            FieldLabel:
                text: 'Your Device Id'
                halign: 'left'
                font_size: self.height * 0.6
                size_hint_x: None
                width: dp(200)
            ValueField:
                id: device_id
                on_text: root._on_device_id_value(*args)
                size_hint_x: None
                width: dp(200)
            Widget:
        Widget:
            size_hint_y: 0.5
            
            
                
    """)
    def __init__(self, **kwargs):
        super(PodiumSetupView, self).__init__(**kwargs)

    def on_info_ref(self, instance, value):
        if value == 'podium':
            webbrowser.open('http://podium.live')

    def on_setup_config(self, instance, value):
        self.ids.next.disabled = False
        self.ids.next.pulsing = False

    def _on_device_id_value(self, instance, value):
        self.ids.next.pulsing = len(value) > 0

    def select_next(self):
        self.ids.next.disabled = True
        def do_next():
            super(PodiumSetupView, self).select_next()

        device_id = re.sub(r'\W+', '', self.ids.device_id.text)[0:34]
        self.ids.device_id.text = device_id


        if len(device_id) == 0:
            self.info_popup('You can set your Device ID later under Setup', do_next)
            return

        cfg = self.rc_config.connectivityConfig
        cfg.telemetryConfig.deviceId = device_id
        cfg.stale = True

        self.write_rcp_config('Updating Device Id ... ', do_next)


