#
# Race Capture App
#
# Copyright (C) 2014-2016 Autosport Labs
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
kivy.require('1.9.1')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.metrics import dp
from autosportlabs.racecapture.views.dashboard.widgets.gauge import CustomizableGauge
from utils import kvFind
from kivy.graphics import *
from kivy.properties import NumericProperty, ListProperty
from kivy.logger import Logger
from kivy.core.image import Image as CoreImage
import io


class SweepGauge(BoxLayout):
    # these values match the dimensions of the svg elements used in this gauge.
    Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/roundgauge.kv')

    value = NumericProperty(0)
    color = ListProperty([1, 1, 1, 1])
    gauge_mask = CoreImage('resource/gauge/gauge_mask.png')
    gauge_image = CoreImage('resource/gauge/round_gauge_270.png')
    gauge_shadow = CoreImage('resource/gauge/round_gauge_270_shadow.png')

    def __init__(self, **kwargs):
        super(SweepGauge, self).__init__(**kwargs)
        self.gauge_height = 110
        self.gauge_width = 100
        self.zoom_factor = 1.1

        self.mask_rotations = []
        size = self.height if self.height < self.width else self.width
        gauge_height = size / self.gauge_height
        x_center = self.pos[0] + self.width / 2 - self.gauge_width / 2
        y_center = self.pos[1] + self.height / 2 - self.gauge_height / 2

        with self.canvas:
            PushMatrix()
            self.dial_color = Color(rgba=self.color)
            self.gauge_translate = Translate(x_center, y_center, 0)
            self.gauge_scale = Scale(x=gauge_height, y=gauge_height)
            Rectangle(texture=SweepGauge.gauge_image.texture, pos=self.pos, size=self.size)
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-135, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(texture=SweepGauge.gauge_mask.texture)
            PopMatrix()
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-225, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(texture=SweepGauge.gauge_mask.texture)
            PopMatrix()
            PushMatrix()
            self.mask_rotations.append(Rotate(angle=-315, axis=(0, 0, 1), origin=(self.center[0], self.center[1])))
            Rectangle(texture=SweepGauge.gauge_mask.texture)
            PopMatrix()
            PopMatrix()

        with self.canvas.after:
            PushMatrix()
            Color(1, 1, 1, 1)
            self.shadow_translate = Translate(x_center, y_center, 0)
            self.shadow_scale = Scale(x=gauge_height, y=gauge_height)
            Rectangle(texture=SweepGauge.gauge_shadow.texture)
            PopMatrix()

        self.bind(pos=self.update_all, size=self.update_all)

    def update_all(self, *args):
        size = self.height if self.height < self.width else self.width
        gauge_height = size / self.gauge_height * self.zoom_factor

        x_center = self.pos[0] + self.width / 2 - (self.gauge_width / 2) * gauge_height
        y_center = self.pos[1] + self.height / 2 - (self.gauge_height / 2) * gauge_height

        self.gauge_translate.x = x_center
        self.gauge_translate.y = y_center
        self.shadow_translate.x = x_center
        self.shadow_translate.y = y_center

        self.gauge_scale.x = gauge_height
        self.gauge_scale.y = gauge_height
        self.shadow_scale.x = gauge_height
        self.shadow_scale.y = gauge_height

    def on_value(self, instance, value):
        angle = (value * 270) / 100
        self.mask_rotations[0].angle = -135 - angle
        self.mask_rotations[1].angle = -135 - angle  if angle > 90 else -225
        self.mask_rotations[2].angle = -135 - angle  if angle > 180 else -315

    def on_color(self, instance, value):
        self.dial_color.rgba = value

class RoundGauge(CustomizableGauge):

    def __init__(self, **kwargs):
        super(RoundGauge, self).__init__(**kwargs)
        self.initWidgets()

    def initWidgets(self):
        pass

    def on_channel(self, instance, value):
        addChannelView = self.ids.get('add_gauge')
        if addChannelView: addChannelView.text = '+' if value == None else ''
        return super(RoundGauge, self).on_channel(instance, value)


    def update_colors(self):
        self.ids.gauge.color = self.select_alert_color()
        return super(RoundGauge, self).update_colors()

    def on_value(self, instance, value):
        try:
            value = self.value
            min = self.min
            max = self.max
            railedValue = value
            if railedValue > max:
                railedValue = max
            if railedValue < min:
                railedValue = min

            range = max - min
            offset = railedValue - min
            self.ids.gauge.value = offset * 100 / range
        except Exception as e:
            Logger.error('RoundGauge: error setting gauge value ' + str(e))

        return super(RoundGauge, self).on_value(instance, value)

