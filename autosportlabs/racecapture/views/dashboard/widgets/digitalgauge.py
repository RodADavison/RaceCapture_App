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
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from utils import kvFind, kvquery
from fieldlabel import AutoShrinkFieldLabel
from kivy.properties import NumericProperty, ObjectProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge

DEFAULT_BACKGROUND_COLOR = [0, 0, 0, 0]

class DigitalGauge(CustomizableGauge):
    Builder.load_string("""
<DigitalGauge>:
    anchor_x: 'center'
    anchor_y: 'center'
    title_size: self.height * 0.5
    value_size: self.height * 0.7
    BoxLayout:
        orientation: 'horizontal'
        spacing: self.height * 0.1
        
        AutoShrinkFieldLabel:
            id: title
            text: 'channel'
            font_size: root.title_size
            halign: 'right'
        AutoShrinkFieldLabel:
            canvas.before:
                Color:
                    rgba: root.alert_background_color
                Rectangle:
                    pos: self.pos
                    size: self.size
            id: value
            text: '---'
            font_size: root.value_size
            halign: 'center'    
    """)

    alert_background_color = ObjectProperty(DEFAULT_BACKGROUND_COLOR)

    def __init__(self, **kwargs):
        super(DigitalGauge, self).__init__(**kwargs)
        self.normal_color = DEFAULT_BACKGROUND_COLOR

    def update_title(self, channel, channel_meta):
        try:
            self.title = channel if channel else ''
        except Exception as e:
            print('Failed to update digital gauge title ' + str(e))

    def update_colors(self):
        alert_color = self.select_alert_color()
        self.alert_background_color = DEFAULT_BACKGROUND_COLOR if alert_color is None else alert_color
