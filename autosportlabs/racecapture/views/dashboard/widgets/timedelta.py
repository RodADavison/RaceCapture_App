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
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty, ObjectProperty, BooleanProperty, StringProperty, NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import SingleChannelGauge

MIN_TIME_DELTA = -99.0
MAX_TIME_DELTA = 99.0

DEFAULT_AHEAD_COLOR = [0.0, 1.0 , 0.0, 1.0]
DEFAULT_BEHIND_COLOR = [1.0, 0.65, 0.0 , 1.0]

class TimeDelta(SingleChannelGauge):
    Builder.load_string("""
<TimeDelta>:
    anchor_x: 'center'
    anchor_y: 'center'
    FieldLabel:
        text: root.NULL_TIME_DELTA    
        id: value
        font_size: root.font_size
        color: [0.5, 0.5, 0.5, 1.0]    
    """)
    ahead_color = ObjectProperty(DEFAULT_AHEAD_COLOR)
    behind_color = ObjectProperty(DEFAULT_BEHIND_COLOR)
    font_size = NumericProperty()
    NULL_TIME_DELTA = u'--.-\u2206'

    def __init__(self, **kwargs):
        super(TimeDelta, self).__init__(**kwargs)

    def on_value(self, instance, value):
        view = self.valueView
        if value == None:
            view.text = TimeDelta.NULL_TIME_DELTA
        else:
            railedValue = value
            railedValue = MIN_TIME_DELTA if railedValue < MIN_TIME_DELTA else railedValue
            railedvalue = MAX_TIME_DELTA if railedValue > MAX_TIME_DELTA else railedValue
            self.valueView.text = u'{0:+1.1f}\u2206'.format(float(railedValue))
        self.update_delta_color()

    def update_delta_color(self):
        self.valueView.color = self.ahead_color if self.value < 0 else self.behind_color

    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass

