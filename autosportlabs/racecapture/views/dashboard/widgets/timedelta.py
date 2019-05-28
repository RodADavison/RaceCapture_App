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
from kivy.uix.anchorlayout import AnchorLayout
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel, AutoShrinkFieldLabel
from kivy.properties import ListProperty, BoundedNumericProperty, ObjectProperty, BooleanProperty, StringProperty, NumericProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import SingleChannelGauge

MIN_TIME_DELTA = -99.0
MAX_TIME_DELTA = 99.0

DEFAULT_AHEAD_COLOR = [0.0, 1.0 , 0.0, 1.0]
DEFAULT_BEHIND_COLOR = [1.0, 0.65, 0.0 , 1.0]

TIME_DELTA_GRAPH_KV = """
<TimeDeltaGraph>:
    padding: (0,0)
    spacing: (0,0)
    orientation: 'horizontal'
    AnchorLayout:
        AnchorLayout:
            size_hint_y: 0.75
            RelativeLayout:
                StencilView:
                    size_hint: (None, 1.0)
                    id: stencil
                    canvas.after:
                        Color:
                            rgba: root.color
                        Rectangle:
                            pos: self.pos
                            size: self.size
        AutoShrinkFieldLabel:
            canvas.before:
                Color:
                    rgba: root.color
                RoundedRectangle:
                    pos: self.pos
                    radius: [self.height * .2,self.height * .2,self.height * .2,self.height * .2]
                    size: self.size
            size_hint_x: 0.3
            size_hint_y: 0.8
            id: delta_value
            text: root.formatted_delta
            font_size: self.height
            color: [0,0,0,1]
            bold: True
"""

class TimeDeltaGraph(SingleChannelGauge):
    Builder.load_string(TIME_DELTA_GRAPH_KV)
    label_color = ListProperty([1, 1, 1, 1.0])
    color = ListProperty([1, 1, 1, 0.5])
    minval = NumericProperty(-3.0)
    maxval = NumericProperty(3.0)
    ahead_color = ObjectProperty(DEFAULT_AHEAD_COLOR)
    behind_color = ObjectProperty(DEFAULT_BEHIND_COLOR)
    formatted_delta = StringProperty()

    def __init__(self, **kwargs):
        super(TimeDeltaGraph, self).__init__(**kwargs)
        self.bind(pos=self._update_size)
        self.bind(size=self._update_size)

    def _update_size(self, *args):
        self.refresh_value(self.value)

    def value_to_percent(self, value):
        min_value = self.minval
        max_value = self.maxval
        railed_value = max(min_value, min(max_value, value))

        range = max_value - min_value
        range = 1 if range == 0 else range

        offset = railed_value - min_value

        return offset * 100 / range

    def update_delta_color(self):
        self.color = self.ahead_color if self.value < 0 else self.behind_color

    def refresh_value(self, value):

        value = 0 if value is None else value

        pct = self.value_to_percent(value) / 100.0

        stencil = self.ids.stencil
        width = 0
        x = 0

        # Draw the bar, extending from either the left or right side of the center label
        # ========(DELTA)
        #         (DELTA)========
        delta_value_width = self.ids.delta_value.width
        # There seems to be a static 5 pixel offset fo the label,
        # cannot identify where this is coming from. leave this for now.
        MYSTERY_PIXEL_OFFSET = 5
        label_offset = (delta_value_width * 0.5) - MYSTERY_PIXEL_OFFSET

        center = self.width * 0.5
        width = abs(pct - 0.5) * (self.width - delta_value_width)
        x = center - width - label_offset if value > 0 else center + label_offset

        stencil.width = width
        stencil.x = x
        self.update_delta_color()
        self.formatted_delta = u'{0:+1.1f}\u2206'.format(value)


class TimeDelta(SingleChannelGauge):
    Builder.load_string("""
<TimeDelta>:
    anchor_x: 'center'
    anchor_y: 'center'
    FieldLabel:
        text: root.NULL_TIME_DELTA    
        id: value
        font_size: root.height * 0.8
        color: [0.5, 0.5, 0.5, 1.0]    
    """)
    ahead_color = ObjectProperty(DEFAULT_AHEAD_COLOR)
    behind_color = ObjectProperty(DEFAULT_BEHIND_COLOR)
    font_size = NumericProperty()
    NULL_TIME_DELTA = u'--.-\u2206'

    def __init__(self, **kwargs):
        super(TimeDelta, self).__init__(**kwargs)
        from kivy.clock import Clock
        Clock.schedule_once(self._init_value)

    def _init_value(self, *args):
        self.value = 0

    def on_value(self, instance, value):
        view = self.valueView
        if value == None or value == 0:
            view.text = TimeDelta.NULL_TIME_DELTA
        else:
            railedValue = value
            railedValue = MIN_TIME_DELTA if railedValue < MIN_TIME_DELTA else railedValue
            railedvalue = MAX_TIME_DELTA if railedValue > MAX_TIME_DELTA else railedValue
            view.text = u'{0:+1.1f}\u2206'.format(float(railedValue))
        self.update_delta_color()

    def update_delta_color(self):
        self.valueView.color = self.ahead_color if self.value <= 0 else self.behind_color

    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass

