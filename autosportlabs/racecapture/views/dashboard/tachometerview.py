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
from kivy.uix.label import Label
from kivy.app import Builder
from kivy.clock import Clock
from autosportlabs.racecapture.views.dashboard.widgets.tachometer import TachometerGauge
from autosportlabs.racecapture.views.dashboard.widgets.bignumberview import BigNumberView
from autosportlabs.racecapture.views.dashboard.widgets.laptime import Laptime
from autosportlabs.racecapture.views.dashboard.widgets.timedelta import TimeDelta
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen
from utils import kvFind, kvFindClass

TACHOMETER_VIEW_KV = """
<TachometerView>:
    rcid: 'tachview'
    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'bottom'
            BoxLayout:
                size_hint: (1.0, 0.6)
                orientation: 'horizontal'
                BoxLayout:
                    size_hint_x: 0.02
                AnchorLayout:
                    size_hint_x: 0.23
                    anchor_x: 'left'
                    anchor_y: 'center'
                    BigNumberView:
                        rcid: 'bignumberview_tach'
                        size_hint: (1.0, 0.8)
                        channel: 'CurrentLap'
                        warning_color: [0.2, 0.2, 0.2, 1.0]
                        alert_color: [0.2, 0.2, 0.2, 1.0]
                BoxLayout:
                    size_hint: (0.70, 1.0)
                    orientation: 'vertical'
                    CurrentLaptime:
                        rcid: 'curLap'
                        halign: 'right'
                        normal_color: [1.0, 1.0 , 1.0, 1.0]                        
                    TimeDelta:
                        rcid: 'delta'
                        channel: 'LapDelta'
                        halign: 'right'
                        valign: 'middle'
                        value: None
                BoxLayout:
                    size_hint_x: 0.02
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'top'
            orientation: 'horizontal'
            padding: (sp(5), sp(10))
            TachometerGauge:
                size_hint_y: 0.4
                size_hint_x: 0.96
                rcid: 'tach'
                channel: 'RPM'
                min: 0
                max: 10000
"""
class TachometerView(DashboardScreen):
    Builder.load_string(TACHOMETER_VIEW_KV)

    _databus = None
    _settings = None

    def __init__(self, databus, settings, dashboard_state, **kwargs):
        super(TachometerView, self).__init__(**kwargs)
        self._databus = databus
        self._settings = settings
        self._dashboard_state = dashboard_state
        self._initialized = False

    def on_meta(self, channelMetas):
        pass

    def on_enter(self):
        if not self._initialized:
            self._init_screen()
        super(TachometerView, self).on_enter()

    def _init_screen(self):
        dataBus = self._databus
        settings = self._settings
        dataBus.addMetaListener(self.on_meta)

        gauges = list(kvFindClass(self, Gauge))

        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = dataBus
            gauge.dashboard_state = self._dashboard_state

        self._initialized = True

