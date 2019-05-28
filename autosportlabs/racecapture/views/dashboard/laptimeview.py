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
from fieldlabel import FieldLabel
from kivy.app import Builder
from utils import kvFind, kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.timedelta import TimeDeltaGraph, TimeDelta
from autosportlabs.racecapture.views.dashboard.widgets.gauge import SingleChannelGauge, Gauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen

LAPTIME_VIEW_KV = """
<LaptimeView>:
    padding: (5, 5)
    BoxLayout:
        #padding: (10,10)
        orientation: 'vertical'
        TimeDeltaGraph:
            #padding: (5,5)
            id: timedelta_graph
            channel: 'LapDelta'
            size_hint_y: 0.2
        BoxLayout:
            size_hint_y: 0.5
            orientation: 'horizontal'
            CurrentLaptime:
                rcid: 'curLap'
                halign: 'center'
                valign: 'middle'
                normal_color: [1.0, 1.0 , 1.0, 1.0]
                    
        BoxLayout:
            padding: (5, 5)
            orientation: 'horizontal'
            size_hint_y: None
            height: min(300, dp(150))
            spacing: self.height * 0.1
            GaugeFrame:
                halign: 'left'
                Laptime:
                    channel: 'BestLap'
                    normal_color: [1.0, 0.0 , 1.0, 1.0]
                    font_size: self.height * 1.0
                    halign: 'left'

            BigNumberView:
                size_hint_x: 0.3
                rcid: 'bignumberview_laptime'
                channel: 'CurrentLap'
                warning_color: [0.2, 0.2, 0.2, 1.0]
                alert_color: [0.2, 0.2, 0.2, 1.0]
                    
            GaugeFrame:
                halign: 'right'
                Laptime:
                    channel: 'LapTime'
                    normal_color: [1.0, 1.0 , 0.0, 1.0]
                    font_size: self.height * 1.0
                    halign: 'right'
"""

class LaptimeView(DashboardScreen):
    Builder.load_string(LAPTIME_VIEW_KV)

    _databus = None
    _settings = None

    def __init__(self, databus, settings, dashboard_state, **kwargs):
        super(LaptimeView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self._dashboard_state = dashboard_state
        self._initialized = False

    def on_meta(self, channelMetas):
        gauges = self.findActiveGauges(SingleChannelGauge)

        for gauge in gauges:
            gauge.dashboard_state = self._dashboard_state
            channel = gauge.channel
            if channel:
                channelMeta = channelMetas.get(channel)
                if channelMeta:
                    gauge.precision = channelMeta.precision
                    gauge.min = channelMeta.min
                    gauge.max = channelMeta.max

    def findActiveGauges(self, gauge_type):
        return list(kvFindClass(self, gauge_type))

    def on_enter(self):
        if not self._initialized:
            self._init_screen()
        super(LaptimeView, self).on_enter()

    def _init_screen(self):
        dataBus = self._databus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)

        gauges = self.findActiveGauges(Gauge)
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = dataBus

        self._initialized = True


