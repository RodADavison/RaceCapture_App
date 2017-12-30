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
import os
import kivy
kivy.require('1.10.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import NumericProperty, StringProperty, ListProperty
from autosportlabs.uix.gauge.bargraphgauge import BarGraphGauge
from autosportlabs.uix.color.colorgradient import HeatColorGradient
from autosportlabs.racecapture.widgets.heat.heatgauge import TireHeatGauge, BrakeHeatGauge
from kivy.app import Builder

class TireCorner(BoxLayout):
    LABEL_COLOR = [0.5, 0.5, 0.5, 1.0]
    zones = NumericProperty()
    minval = NumericProperty()
    maxval = NumericProperty()

    def __init__(self, **kwargs):
        super(TireCorner, self).__init__(**kwargs)
        self.tire_value_widgets = []
        self.heat_gradient = HeatColorGradient()

    def _init_view(self):
        self.tire_zones = TireCorner.DEFAULT_TIRE_ZONES
        self.minval = TireCorner.DEFAULT_TIRE_MIN
        self.maxval = TireCorner.DEFAULT_TIRE_MAX

    def on_minval(self, instance, value):
        for gauge in self.tire_value_widgets:
            gauge.minval = value

    def on_maxval(self, instance, value):
        for gauge in self.tire_value_widgets:
            gauge.maxval = value

    def on_zones(self, instance, value):
        self.ids.tire.zones = value

        self.ids.tire_values_top.clear_widgets()
        self.ids.tire_values_bottom.clear_widgets()
        self.ids.tire_values.clear_widgets()

        if value > 2:
            tv = self.ids.tire_values
            value_containers = [tv]
            orientation = 'right-left' if self.children.index(tv) == 1 else 'left-right'
        else:
            value_containers = [self.ids.tire_values_top, self.ids.tire_values_bottom]
            orientation = 'center'

        if len(value_containers) == 2:
            for c in value_containers:
                c.size_hint_y = 0.1
            self.ids.tire.size_hint_y = 0.6


        del(self.tire_value_widgets[:])
        for i in range(0, value):
            tire_values = value_containers[0] if i % len(value_containers) == 0 else value_containers[1]
            gauge = BarGraphGauge(orientation=orientation, label_color=TireCorner.LABEL_COLOR)
            tire_values.add_widget(gauge)
            self.tire_value_widgets.append(gauge)
            gauge.minval = self.minval
            gauge.maxval = self.maxval

    def set_value(self, zone, value):
        value = min(self.maxval, value)
        value = max(self.minval, value)
        scaled = value / self.maxval if self.maxval > 0 else 0
        self.ids.tire.set_value(zone, scaled)
        try:
            value_widget = self.tire_value_widgets[zone]
            value_widget.value = value
            value_widget.color = self.heat_gradient.get_color_value(scaled)
        except IndexError:
            pass

TIRE_CORNER_LEFT_KV = """
<TireCornerLeft>:
    spacing: dp(10)
    GridLayout:
        id: tire_values
        size_hint: (0.4, 0.5)
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}                        
        cols: 1
    BoxLayout:
        size_hint: (0.6, 0.8)
        orientation: 'vertical'
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        spacing: dp(5)              
        GridLayout:
            id: tire_values_top
            size_hint_y: 0.1
            cols: 1            
        TireHeatGauge:
            id: tire
            size_hint_y: 0.8
            direction: 'right-left'
        GridLayout:
            id: tire_values_bottom
            size_hint_y: 0.1
            cols: 1                                                
                
"""
class TireCornerLeft(TireCorner):
    Builder.load_string(TIRE_CORNER_LEFT_KV)

TIRE_CORNER_RIGHT_KV = """
<TireCornerRight>:
    spacing: dp(10)
    BoxLayout:
        size_hint: (0.6, 0.8)
        orientation: 'vertical'
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        spacing: dp(5)
        GridLayout:
            id: tire_values_top
            size_hint_y: 0.1
            cols: 1            
        TireHeatGauge:
            id: tire
            size_hint_y: 0.8
            direction: 'left-right'
        GridLayout:
            id: tire_values_bottom
            size_hint_y: 0.1
            cols: 1                                                
    GridLayout:
        id: tire_values
        size_hint: (0.4, 0.5)
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        cols: 1
        
"""
class TireCornerRight(TireCorner):
    Builder.load_string(TIRE_CORNER_RIGHT_KV)

BRAKE_CORNER_KV = """
<BrakeCorner>:
    bar_gauge_orientation: 'center'
    orientation: 'vertical'
    AnchorLayout:
        anchor_y: 'bottom'
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        size_hint: (0.5, 0.2)
        GridLayout:
            id: brake_values_top
            cols: 1                                        
    BrakeHeatGauge:
        id: brake
        size_hint: (1.0, 0.6)
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
    AnchorLayout:
        anchor_y: 'top'
        pos_hint: {'center_x': 0.5, 'center_y': 0.5}
        size_hint: (0.5, 0.2)
        GridLayout:
            id: brake_values_bottom
            cols: 1                                                                            
"""

class BrakeCorner(BoxLayout):
    Builder.load_string(BRAKE_CORNER_KV)
    zones = NumericProperty()
    minval = NumericProperty()
    maxval = NumericProperty()
    bar_gauge_orientation = StringProperty()
    LABEL_COLOR = [0.5, 0.5, 0.5, 1.0]

    def __init__(self, **kwargs):
        super(BrakeCorner, self).__init__(**kwargs)
        self.brake_value_widgets = []
        self.heat_gradient = HeatColorGradient()

    def on_zones(self, instance, value):
        self.ids.brake.zones = value
        top_values = self.ids.brake_values_top
        bottom_values = self.ids.brake_values_bottom
        top_values.clear_widgets()
        bottom_values.clear_widgets()
        del(self.brake_value_widgets[:])


        for i in range(0, value):
            if value <= 2:  # if zones are 2 or less zones go above and below
                current_grid = top_values if i % 2 == 0 else bottom_values
            else:  # if zones > 2 then go top to bottom
                current_grid = top_values if i < 2 else bottom_values

            gauge = BarGraphGauge(orientation=self.bar_gauge_orientation, label_color=BrakeCorner.LABEL_COLOR)
            gauge.minval = self.minval
            gauge.maxval = self.maxval
            current_grid.add_widget(gauge)
            self.brake_value_widgets.append(gauge)

        size_hint_y = 0.5 if value <= 2 else 1.0
        top_values.size_hint_y = size_hint_y
        bottom_values.size_hint_y = size_hint_y

    def set_value(self, zone, value):
        value = min(self.maxval, value)
        value = max(self.minval, value)
        scaled = value / self.maxval if self.maxval > 0 else 0
        self.ids.brake.set_value(zone, scaled)
        try:
            value_widget = self.brake_value_widgets[zone]
            value_widget.value = value
            value_widget.color = self.heat_gradient.get_color_value(scaled)
        except IndexError:
            pass

    def on_minval(self, instance, value):
        for gauge in self.brake_value_widgets:
            gauge.minval = value

    def on_maxval(self, instance, value):
        for gauge in self.brake_value_widgets:
            gauge.maxval = value

class HeatmapCorner(AnchorLayout):
    brake_zones = NumericProperty(None)
    tire_zones = NumericProperty(None)
    brake_range = ListProperty()
    tire_range = ListProperty()

    def __init__(self, **kwargs):
        super(HeatmapCorner, self).__init__(**kwargs)

    def on_brake_zones(self, instance, value):
        self.ids.brake.zones = value
        self._update_note()

    def on_tire_zones(self, instance, value):
        self.ids.tire.zones = value
        self._update_note()

    def _update_note(self):
        self.ids.note.text = 'No sensors' if self.tire_zones == 0 and self.brake_zones == 0 else ''

    def on_tire_range(self, instance, value):
        self.ids.tire.minval = value[0]
        self.ids.tire.maxval = value[1]

    def on_brake_range(self, instance, value):
        self.ids.brake.minval = value[0]
        self.ids.brake.maxval = value[1]

    def set_brake_value(self, zone, value):
        self.ids.brake.set_value(zone, value)

    def set_tire_value(self, zone, value):
        self.ids.tire.set_value(zone, value)

HEATMAP_CORNER_LEFT_KV = """
<HeatmapCornerLeft>:
    FieldLabel:
        id: note
        size_hint_x: 0.5
    BoxLayout:
        padding: (dp(10), dp(10))
        spacing: dp(10)
        TireCornerLeft:
            id: tire
            size_hint_x: 0.55
        BrakeCorner:
            id: brake
            size_hint_x: 0.45
"""

class HeatmapCornerLeft(HeatmapCorner):
    Builder.load_string(HEATMAP_CORNER_LEFT_KV)

HEATMAP_CORNER_RIGHT_KV = """
<HeatmapCornerRight>:
    FieldLabel:
        id: note
        size_hint_x: 0.5
    BoxLayout:
        padding: (dp(10), dp(10))
        spacing: dp(10)
        BrakeCorner:
            id: brake
            size_hint_x: 0.45
        TireCornerRight:
            id: tire
            size_hint_x: 0.55
"""
class HeatmapCornerRight(HeatmapCorner):
    Builder.load_string(HEATMAP_CORNER_RIGHT_KV)
