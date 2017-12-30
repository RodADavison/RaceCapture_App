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
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.graphics import *
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.logger import Logger
from autosportlabs.uix.color.colorgradient import HeatColorGradient
from kivy.core.image import Image as CoreImage

HEAT_GAUGE_KV = """
<TireHeatGauge>:
"""

class BrakeHeatGauge(AnchorLayout):
    Builder.load_string(HEAT_GAUGE_KV)
    zones = NumericProperty(None)
    CENTER_SIZE_PCT = 0.5
    ROTOR_IMAGE = CoreImage('autosportlabs/racecapture/widgets/heat/rotor.png')
    TIRE_IMAGE = CoreImage('autosportlabs/racecapture/widgets/heat/tire.png')
    def __init__(self, **kwargs):
        super(BrakeHeatGauge, self).__init__(**kwargs)
        self.heat_gradient = HeatColorGradient()
        self.colors = []
        self.values = []
        self._init_view()
        self.bind(pos=self._update_gauge)
        self.bind(size=self._update_gauge)
        self.bind(zones=self._update_gauge)

    def on_zones(self, instance, value):
        self._sync_zones()

    def _init_view(self):
        self._sync_zones()

    def _sync_zones(self):
        zones = self.zones
        if zones is None:
            return

        values = self.values
        values.extend([0] * (zones - len(values)))
        colors = self.colors
        colors.extend([Color()] * (zones - len(colors)))
        self._update_gauge()

    def set_value(self, zone, value):
        try:
            rgba = self.heat_gradient.get_color_value(value)
            self.colors[zone].rgba = rgba
            self.values[zone] = value
        except IndexError:
            pass

    def _update_gauge(self, *args):
        self.canvas.clear()
        zones = self.zones
        if zones is None or zones == 0:
            return

        x = self.pos[0]
        y = self.pos[1]
        width = self.size[0]
        height = self.size[1]

        min_size = min(width, height)
        center_size = min_size * BrakeHeatGauge.CENTER_SIZE_PCT
        rw = ((min_size - center_size) / float(zones))

        center_x = x + (width / 2)
        center_y = y + (height / 2)
        index = zones
        with self.canvas:
            for i in range(0, zones):
                color = self.heat_gradient.get_color_value(self.values[index - 1])
                c = Color(rgba=color)
                self.colors[index - 1] = c
                segment_size = (index * (rw)) + center_size
                c_x = center_x - segment_size / 2
                c_y = center_y - segment_size / 2
                Ellipse(pos=(c_x, c_y), size=(segment_size, segment_size))
                index -= 1
            Color(1.0, 1.0, 1.0, 1.0)
            r_x = center_x - (center_size / 2)
            r_y = center_y - (center_size / 2)
            Rectangle(texture=BrakeHeatGauge.ROTOR_IMAGE.texture, pos=(r_x, r_y), size=(center_size, center_size))

    def on_values(self, instance, value):
        pass


class TireHeatGauge(AnchorLayout):
    Builder.load_string(HEAT_GAUGE_KV)
    zones = NumericProperty(None)
    direction = StringProperty('left-right')

    def __init__(self, **kwargs):
        super(TireHeatGauge, self).__init__(**kwargs)
        self.heat_gradient = HeatColorGradient()
        self.colors = []
        self.values = []
        self._init_view()
        self.bind(pos=self._update_gauge)
        self.bind(size=self._update_gauge)
        self.bind(zones=self._update_gauge)
        self.bind(direction=self._update_gauge)

    def on_zones(self, instance, value):
        self._sync_zones()

    def _init_view(self):
        self._sync_zones()

    def _sync_zones(self):
        zones = self.zones
        if zones is None:
            return

        values = self.values
        values.extend([0] * (zones - len(values)))
        colors = self.colors
        colors.extend([Color()] * (zones - len(colors)))
        self._update_gauge()

    def set_value(self, zone, value):
        try:
            rgba = self.heat_gradient.get_color_value(value)
            self.colors[zone].rgba = rgba
            self.values[zone] = value
        except IndexError:
            pass

    def _update_gauge(self, *args):
        self.canvas.clear()
        zones = self.zones
        if zones is None or zones == 0:
            return

        x = self.pos[0]
        y = self.pos[1]
        width = self.size[0]
        height = self.size[1]

        rw = width / float(zones)

        if self.direction == 'left-right':
            index = 0
            index_dir = 1
        elif self.direction == 'right-left':
            index = zones - 1
            index_dir = -1
        else:
            raise Exception('Invalid direction {}'.self.dir)

        with self.canvas:
            for i in range(0, zones):
                xp = x + (rw * i)
                color = self.heat_gradient.get_color_value(self.values[index])
                c = Color(rgba=color)
                self.colors[index] = c
                Rectangle(pos=(xp, y), size=(rw, height))
                index += index_dir
            Color(rgba=(0.0, 0.0, 0.0, 1.0))
            Rectangle(texture=BrakeHeatGauge.TIRE_IMAGE.texture, pos=(x, y), size=(width, height))


    def on_values(self, instance, value):
        pass

