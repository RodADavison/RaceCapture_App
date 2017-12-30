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

from math import sin
from installfix_garden_graph import Graph, LinePlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivy.utils import get_color_from_hex as rgb
from kivy.app import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.popup import Popup
from valuefield import *
from utils import *
from autosportlabs.racecapture.views.configuration.channels.channelnameselectorview import ChannelNameSelectorView
from channelnamespinner import ChannelNameSpinner
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseMultiChannelConfigView, BaseChannelView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble, WarnLabel
from autosportlabs.racecapture.presets.presetview import PresetBrowserView

class AnalogChannelsView(BaseMultiChannelConfigView):
    preset_manager = ObjectProperty()

    def __init__(self, **kwargs):
        super(AnalogChannelsView, self).__init__(**kwargs)
        self.channel_title = 'Analog '
        self.accordion_item_height = dp(350)


    def channel_builder(self, index, max_sample_rate):
        editor = AnalogChannel(id='analog' + str(index), channels=self.channels, preset_manager=self.preset_manager)
        editor.bind(on_modified=self.on_modified)
        if self.config:
            editor.on_config_updated(self.config.channels[index], max_sample_rate)
        return editor

    def get_specific_config(self, rcp_cfg):
        return rcp_cfg.analogConfig

class AnalogChannel(BaseChannelView):
    Builder.load_string("""
<AnalogChannel>:
    orientation: 'horizontal'
    BoxLayout:
        orientation: 'vertical'
        padding: (dp(10), dp(10))
        spacing: dp(5)
        ChannelNameSelectorView:
            id: chan_id
            channel_type: 1
            size_hint: (1.0,0.15)
        SampleRateSelectorView:
            id: sr
            size_hint: (1.0,0.15)
        HSeparatorMinor:
            text: 'Mode'
        GridLayout:
            size_hint: (1.0, 0.4)
            cols: 2
            FieldLabel:
                text: 'Raw (0-5v)'
                font_size: dp(17)
                halign: 'right'
            CheckBox:
                size_hint_x: None
                width: dp(140)
                group: 'scalingType'
                id: smRaw
                on_active: root.on_scaling_type_raw(*args)
            FieldLabel:
                text: 'Linear'
                font_size: dp(17)
                halign: 'right'
            CheckBox:
                size_hint_x: None
                width: dp(140)
                group: 'scalingType'
                id: smLinear
                on_active: root.on_scaling_type_linear(*args)
            FieldLabel:
                text: 'Mapped'
                font_size: dp(17)
                halign: 'right'
            CheckBox:
                size_hint_x: None
                width: dp(140)
                group: 'scalingType'
                id: smMapped
                on_active: root.on_scaling_type_map(*args)
        HSeparatorMinor:
            text: 'Smoothing'
        AnchorLayout:
            size_hint: (1.0,0.2)
            AnchorLayout:
                anchor_y: 'top'
                BoxLayout:
                    FieldLabel:
                        text: 'Less'
                        size_hint_x: None
                        width: dp(50)
                        halign: 'right'
                    Slider:
                        id: smoothing
                        min: 0
                        max: 99
                        on_value: root.on_smoothing(*args)
                    FieldLabel:
                        text: 'More'
                        halign: 'left'
                        size_hint_x: None
                        width: dp(50)
            AnchorLayout:
                anchor_y: 'bottom'
                FieldLabel:
                    id: smoothing_value
                    halign: 'center'
                    size_hint_y: None
                    height: dp(20)
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            orientation: 'horizontal'
            BoxLayout:
            LabelIconButton:
                size_hint_x: None
                width: dp(120)
                id: load_preset
                title: 'Presets'
                icon_size: self.height * 0.7
                title_font_size: self.height * 0.5
                icon: u'\uf150'
                on_press: root.load_preset_view()
                           
    VSeparator:
    BoxLayout:
        orientation: 'vertical'
        padding: (dp(5), dp(5))
        BoxLayout:
            size_hint_y: 0.6
            id: graphcontainer        
            orientation: 'vertical'
        ScreenManager:
            size_hint_y: 0.4
            id: screens
            orientation: 'vertical'
            Screen:
                name: 'blank'
            Screen:
                name: 'map'
                AnalogScalingMapEditor:
                    id: map_editor
                    size_hint_x: 1.0
            Screen:
                name: 'linear'
                BoxLayout:
                    size_hint_x: 1.0
                    orientation: 'vertical'
                    HSeparatorMinor:
                        text: 'Linear Formula'
                        size_hint_y: None
                        height: dp(50)
                    BoxLayout:
                        padding: (dp(10), dp(10))
                        size_hint_y: None
                        height: dp(60)
                        orientation: 'horizontal'
                        FieldLabel:
                            text: u'Raw \u00D7'
                            halign: 'center'
                            font_size: self.height * 0.7
                            size_hint_x: None
                            width: dp(100)                       
                        FloatValueField:
                            id: linearscaling
                            on_text: root.on_linear_map_value(*args)
                        FieldLabel:
                            text: '+'
                            halign: 'center'
                            font_size: self.height * 0.7
                            size_hint_x: None
                            width: dp(50)                       
                        FloatValueField:
                            id: linearoffset
                            on_text: root.on_linear_map_offset(*args)
                    BoxLayout:
    """)
    preset_manager = ObjectProperty()

    SCREEN_MAP = {ANALOG_SCALING_MODE_RAW: 'blank',
                  ANALOG_SCALING_MODE_LINEAR: 'linear',
                  ANALOG_SCALING_MODE_MAP: 'map'}

    def __init__(self, **kwargs):
        super(AnalogChannel, self).__init__(**kwargs)
        self.max_sample_rate = None
        self.channelConfig = None

    def on_smoothing(self, instance, value):
        self.ids.smoothing_value.text = str(int(value))
        try:
            if self.channelConfig:
                alpha = (100.0 - float(value)) * .01
                self.channelConfig.alpha = alpha
                self.channelConfig.stale = True
                self.dispatch('on_modified', self.channelConfig)
        except:
            pass

    def on_linear_map_offset(self, instance, value):
        try:
            if self.channelConfig:
                self.channelConfig.linearOffset = float(value)
                self.channelConfig.stale = True
                self.dispatch('on_modified', self.channelConfig)
        except:
            pass
    def on_linear_map_value(self, instance, value):
        try:
            if self.channelConfig:
                self.channelConfig.linearScaling = float(value)
                self.channelConfig.stale = True
                self.dispatch('on_modified', self.channelConfig)
        except:
            pass

    def on_scaling_type_raw(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_RAW
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
            self._synchronize_view()

    def on_scaling_type_linear(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_LINEAR
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
            self._synchronize_view()

    def on_scaling_type_map(self, instance, value):
        if self.channelConfig and value:
            self.channelConfig.scalingMode = ANALOG_SCALING_MODE_MAP
            self.channelConfig.stale = True
            self.dispatch('on_modified', self.channelConfig)
            self._synchronize_view()

    def _synchronize_view(self):
        self.ids.screens.current = AnalogChannel.SCREEN_MAP.get(self.channelConfig.scalingMode)
        self.regen_plot()

    def on_config_updated(self, channelConfig, max_sample_rate):
        self.max_sample_rate = max_sample_rate
        self.ids.chan_id.setValue(channelConfig)
        self.ids.sr.setValue(channelConfig.sampleRate, max_sample_rate)

        scaling_mode = channelConfig.scalingMode

        check_raw = self.ids.smRaw
        check_linear = self.ids.smLinear
        check_mapped = self.ids.smMapped
        if scaling_mode == 0:
            check_raw.active = True
            check_linear.active = False
            check_mapped.active = False
        elif scaling_mode == 1:
            check_raw.active = False
            check_linear.active = True
            check_mapped.active = False
        elif scaling_mode == 2:
            check_raw.active = False
            check_linear.active = False
            check_mapped.active = True

        self.ids.smoothing.value = 100 - (channelConfig.alpha * 100.0)
        self.ids.linearscaling.text = str(channelConfig.linearScaling)
        self.ids.linearoffset.text = str(channelConfig.linearOffset)
        map_editor = self.ids.map_editor
        map_editor.on_config_changed(channelConfig.scalingMap)
        map_editor.bind(on_map_updated=self.on_map_updated)
        self.channelConfig = channelConfig
        self._synchronize_view()

    def regen_plot(self):
        cfg = self.channelConfig
        mode = cfg.scalingMode
        if mode == 0:
            self._regen_plot_linear(1, 0)
        elif mode == 1:
            self._regen_plot_linear(cfg.linearScaling, cfg.linearOffset)
        else:
            scaling_map = self.channelConfig.scalingMap
            volts = []
            scaled = []
            for i in range (0, ScalingMap.SCALING_MAP_POINTS):
                volts.append(scaling_map.getVolts(i))
                scaled.append(scaling_map.getScaled(i))
            self._regen_plot_interpolated(volts, scaled)

    def _regen_plot_linear(self, scaling, offset):
        volt_increment = float(ScalingMap.SCALING_MAP_POINTS) / (ScalingMap.SCALING_MAP_POINTS - 1)
        volts = []
        scaled = []
        v = 0
        for i in range(0, ScalingMap.SCALING_MAP_POINTS):
            volts.append(v)
            scaled.append(v * scaling + offset)
            v += volt_increment
        self._regen_plot_interpolated(volts, scaled)

    def _regen_plot_interpolated(self, volts, scaled):
        graphContainer = self.ids.graphcontainer
        graphContainer.clear_widgets()

        graph = AnalogScaler()
        graphContainer.add_widget(graph)

        plot = LinePlot(color=rgb('00FF00'), line_width=1.25)
        graph.add_plot(plot)
        self.plot = plot

        points = []
        max_scaled = None
        min_scaled = None
        for i in range(ScalingMap.SCALING_MAP_POINTS):
            v = volts[i]
            s = scaled[i]
            points.append((v, s))
            if max_scaled == None or s > max_scaled:
                max_scaled = s
            if min_scaled == None or s < min_scaled:
                min_scaled = s

        graph.ymin = min_scaled
        graph.ymax = max_scaled
        graph.xmin = 0
        graph.xmax = 5
        plot.points = points

    def on_map_updated(self, *args):
        self.channelConfig.stale = True
        self.dispatch('on_modified', self.channelConfig)
        self._synchronize_view()

    def _import_preset(self, preset_id):
        try:
            preset = self.preset_manager.get_preset_by_id(preset_id)
            mapping = preset.mapping
            cfg = self.channelConfig
            cfg.fromJson(mapping)
            self.on_config_updated(cfg, self.max_sample_rate)
            cfg.stale = True
            self.dispatch('on_modified', cfg)
        except Exception as e:
            Logger.error('Failed to import analog preset {}'.format(e))
            raise

    def load_preset_view(self):
        def preset_selected(instance, preset_id):
            self._import_preset(preset_id)
            popup.dismiss()

        def popup_dismissed(*args):
            pass

        content = PresetBrowserView(self.preset_manager, 'analog')
        content.bind(on_preset_selected=preset_selected)
        content.bind(on_preset_close=lambda *args:popup.dismiss())
        popup = Popup(title='Import a preset', content=content, size_hint=(0.7, 0.8))
        popup.bind(on_dismiss=popup_dismissed)
        popup.open()

    def _on_preset_selected(self):
        pass

class AnalogScaler(Graph):
    Builder.load_string("""
<AnalogScaler>:
    id: graph
    xlabel: 'Volts'
    ylabel: 'Scaled'
    x_ticks_minor: 1
    x_ticks_major: 1
    y_grid_label: True
    x_grid_label: True
    padding: 5
    x_grid: True
    y_grid: True
    xmin: 0
    xmax: 5    
    """)
    def __init__(self, **kwargs):
        super(AnalogScaler, self).__init__(**kwargs)

WARN_DISMISS_TIMEOUT = 3

class LinearScalingMapEditor(Screen):
    Builder.load_string("""
<LinearScalingMapEditor>:
    """)

class AnalogScalingMapEditor(BoxLayout):
    Builder.load_string("""
<AnalogScalingMapEditor>:
    orientation: 'vertical'
    HSeparatorMinor:
        text: 'Interpolated Mapping'
        size_hint_y: None
        height: dp(50)
    GridLayout:
        cols: 6
        Label:
            text: ''
        Label:
            text: '1'
        Label:
            text: '2'
        Label:
            text: '3'
        Label:
            text: '4'
        Label:
            text: '5'
        Label:
            text: 'Volts'
        FloatValueField:
            rcid: 'v_0'
            text: ''
            on_text_validate: root.on_volts(0, *args)
        FloatValueField:
            rcid: 'v_1'
            text: ''
            on_text_validate: root.on_volts(1, *args)
        FloatValueField:
            rcid: 'v_2'
            text: ''
            on_text_validate: root.on_volts(2, *args)
        FloatValueField:
            rcid: 'v_3'
            text: ''
            on_text_validate: root.on_volts(3, *args)
        FloatValueField:
            rcid: 'v_4'
            text: ''
            on_text_validate: root.on_volts(4, *args)
        Label:
            text: 'Scaled'
        FloatValueField:
            rcid: 's_0'
            text: ''
            on_text: root.on_scaled(0, *args)
        FloatValueField:
            rcid: 's_1'
            text: ''
            on_text: root.on_scaled(1, *args)
        FloatValueField:
            rcid: 's_2'
            text: ''
            on_text: root.on_scaled(2, *args)
        FloatValueField:
            rcid: 's_3'
            text: ''
            on_text: root.on_scaled(3, *args)
        FloatValueField:
            rcid: 's_4'
            text: ''
            on_text: root.on_scaled(4, *args)    
    """)
    scaling_map = None
    plot = None
    def __init__(self, **kwargs):
        super(AnalogScalingMapEditor, self).__init__(**kwargs)
        self.register_event_type('on_map_updated')

    def setTabStops(self, mapSize):
        voltsCellFirst = kvFind(self, 'rcid', 'v_0')
        voltsCellNext = None
        for i in range(mapSize):
            voltsCell = kvFind(self, 'rcid', 'v_' + str(i))
            scaledCell = kvFind(self, 'rcid', 's_' + str(i))
            voltsCell.set_next(scaledCell)
            if (i < mapSize - 1):
                voltsCellNext = kvFind(self, 'rcid', 'v_' + str(i + 1))
            else:
                voltsCellNext = voltsCellFirst
            scaledCell.set_next(voltsCellNext)

    def set_volts_cell(self, cell_field, value):
        cell_field.text = '{:.3g}'.format(value)

    def set_scaled_cell(self, scaled_field, value):
        scaled_field.text = '{:.3g}'.format(value)

    def on_config_changed(self, scaling_map):
        map_size = ScalingMap.SCALING_MAP_POINTS
        self.setTabStops(map_size)
        for i in range(map_size):
            volts = scaling_map.getVolts(i)
            scaled = scaling_map.getScaled(i)
            volts_cell = kvFind(self, 'rcid', 'v_' + str(i))
            scaled_cell = kvFind(self, 'rcid', 's_' + str(i))
            self.set_volts_cell(volts_cell, volts)
            self.set_scaled_cell(scaled_cell, scaled)
        self.scaling_map = scaling_map

    def on_map_updated(self):
        pass

    def _refocus(self, widget):
        widget.focus = True

    def on_volts(self, mapBin, instance):
        value = instance.text.strip()
        if value == '' or value == "." or value == "-":
            value = 0
            instance.text = str(value)
        try:
            value = float(value)
            if self.scaling_map:
                self.scaling_map.setVolts(mapBin, value)
                self.dispatch('on_map_updated')
        except ScalingMapException as e:
            warn = CenteredBubble()
            warn.add_widget(WarnLabel(text=str(e)))
            warn.auto_dismiss_timeout(WARN_DISMISS_TIMEOUT)
            warn.background_color = (1, 0, 0, 1.0)
            warn.size = (dp(200), dp(50))
            warn.size_hint = (None, None)
            self.get_root_window().add_widget(warn)
            warn.center_above(instance)
            original_value = self.scaling_map.getVolts(mapBin)
            self.set_volts_cell(instance, original_value)
            Clock.schedule_once(lambda dt: self._refocus(instance))
        except Exception as e:

            alertPopup('Scaling Map', str(e))
            original_value = self.scaling_map.getVolts(mapBin)
            self.set_volts_cell(instance, original_value)

    def on_scaled(self, mapBin, instance, value):
        value = value.strip()
        if value == '' or value == "." or value == "-":
            value = 0
            instance.text = str(value)
        try:
            value = float(value)
            if self.scaling_map:
                self.scaling_map.setScaled(mapBin, value)
                self.dispatch('on_map_updated')
        except Exception as e:
            Logger.error("Error updating chart with scaled value: " + str(e))



