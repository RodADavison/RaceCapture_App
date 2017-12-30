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
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from samplerateview import *
from utils import *
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.help.helpmanager import HelpInfo

GPS_CHANNELS_VIEW_KV = """
#:kivy 1.10.0
#:import ColorScheme autosportlabs.racecapture.theme.color.ColorScheme
<GPSChannelsView>:
    orientation: 'vertical'
    spacing: dp(5)
    BoxLayout:
        size_hint_y: 0.08
        orientation: 'vertical'
        SampleRateSelectorView:
            id: sr
    BoxLayout:
        orientation: 'horizontal'
        id: warning_pane
        size_hint_y: 0.0
        AnchorLayout:
            size_hint_x: 0.15
            IconButton:
                id: warning_icon
                text: u'\uf071'
                size_hint_y: 1.0
                color: ColorScheme.get_alert()
        AnchorLayout:
            size_hint_x: 0.85
            FieldLabel:
                id: warning
                halign: 'left'
                shorten: False
                    
    HSeparator:
        size_hint_y: 0.1
        text: 'Channels'
    ScrollContainer:
        id: scroller
        size_hint_y: 0.72
        do_scroll_x: False
        GridLayout:
            id: gps_grid
            row_default_height: root.height * 0.1
            row_force_default: True
            size_hint_y: None
            height: max(self.minimum_height, scroller.height)
            cols: 2
            spacing: [dp(10),dp(10)]
            padding: [dp(5),dp(5)]
            FieldLabel:
                text: 'Position'
                halign: 'right'
            Switch:
                id: position
                on_active: root.onPosActive(*args)
            FieldLabel:
                text: 'Speed'
                halign: 'right'
            Switch:
                id: speed
                halign: 'right'
                on_active: root.onSpeedActive(*args)
            FieldLabel:
                text: 'Distance'
                halign: 'right'
            Switch:
                id: distance
                on_active: root.onDistActive(*args)
            FieldLabel:
                text: 'Altitude'
                halign: 'right'
            Switch:
                id: altitude
                on_active: root.onAltitudeActive(*args)
            FieldLabel:
                text: 'Satellites'
                halign: 'right'
            Switch:
                id: satellites
                on_active: root.onSatsActive(*args)
            FieldLabel:
                text: 'GPS Fix Quality'
                halign: 'right'
            Switch:
                id: quality
                on_active: root.onGpsQualityActive(*args)
            FieldLabel:
                text: 'Dilution of Precision (DOP)'
                halign: 'right'
            Switch:
                id: dop
                on_active: root.onGpsDOPActive(*args)
"""

class GPSChannelsView(BaseConfigView):
    SAMPLE_RATE_WARNING_THRESHOLD = 25
    GPS_WARNING_DELAY = 1.0
    gpsConfig = None
    lap_config = None
    Builder.load_string(GPS_CHANNELS_VIEW_KV)

    def __init__(self, **kwargs):
        super(GPSChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.ids.sr.bind(on_sample_rate=self.on_sample_rate)

    def onPosActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.positionEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
            self._update_warning_msg()

    def onSpeedActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.speedEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
            self._update_warning_msg()

    def onDistActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.distanceEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
            self._update_warning_msg()

    def onAltitudeActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.altitudeEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')

    def onSatsActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.satellitesEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')

    def onGpsQualityActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.qualityEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')

    def onGpsDOPActive(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.DOPEnabled = 1 if value else 0
            self.gpsConfig.stale = True
            self.dispatch('on_modified')

    def on_sample_rate(self, instance, value):
        if self.gpsConfig:
            self.gpsConfig.sampleRate = value
            self.gpsConfig.stale = True
            self.dispatch('on_modified')
            if self.lap_config.primary_stats_enabled():
                self.lap_config.set_primary_stats(value)
            self._update_warning_msg()

    def _update_warning_msg(self):
        gps_cfg = self.gpsConfig
        if not gps_cfg:
            return

        warning_messages = []
        if gps_cfg.sampleRate >= GPSChannelsView.SAMPLE_RATE_WARNING_THRESHOLD:
            warning_messages.append('- High sample rates requires optimal GPS conditions')

        if not (gps_cfg.positionEnabled and gps_cfg.distanceEnabled and gps_cfg.speedEnabled) or gps_cfg.sampleRate == 0:
            warning_messages.append('- Disabling these channels will also disable lap timing')

        warning_msg = ''
        warning = self.ids.warning
        warning_pane = self.ids.warning_pane
        warning_icon = self.ids.warning_icon
        if len(warning_messages) > 0:
            warning_msg = ''
            for msg in warning_messages:
                warning_msg += msg + '\n'

            warning_pane.size_hint_y = float(len(warning_messages) * 0.1)
            warning_icon.size_hint_y = 1.0 / len(warning_messages)
            warning.text = warning_msg
            Clock.schedule_once(lambda dt: HelpInfo.help_popup('gps_warning', self, arrow_pos='top_mid'),
                                GPSChannelsView.GPS_WARNING_DELAY)
        else:
            warning_pane.size_hint_y = 0.0
            warning_icon.size_hint_y = 1.0
            warning.text = ''



    def on_config_updated(self, rc_cfg):
        gpsConfig = rc_cfg.gpsConfig
        self.ids.sr.setValue(gpsConfig.sampleRate, rc_cfg.capabilities.sample_rates.gps)
        self.ids.position.active = gpsConfig.positionEnabled
        self.ids.speed.active = gpsConfig.speedEnabled
        self.ids.distance.active = gpsConfig.distanceEnabled
        self.ids.altitude.active = gpsConfig.altitudeEnabled
        self.ids.satellites.active = gpsConfig.satellitesEnabled
        self.ids.quality.active = gpsConfig.qualityEnabled
        self.ids.dop.active = gpsConfig.DOPEnabled
        self.gpsConfig = gpsConfig
        self.lap_config = rc_cfg.lapConfig
        self._update_warning_msg()
