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
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.widgets.imugauge import ImuGauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen
from utils import kvFind, kvFindClass
from kivy.clock import Clock
from utils import kvFindClass

TRACTION_VIEW_KV = """
<TractionView>:
    AnchorLayout:
        AnchorLayout:
            anchor_y: 'top'
            Label:
                text: ''
                size_hint_y: 0.2

        AnchorLayout:
            anchor_y: 'bottom'
            Label:
                text: ''
                size_hint_y: 0.2
        ImuGauge:
            size_hint_x: 0.8
            size_hint_y: 1.0
            padding: (dp(40), dp(40))
            id: imu_gauge
            rcid: 'traction_view_imu'
"""

class TractionView(DashboardScreen):
    Builder.load_string(TRACTION_VIEW_KV)

    def __init__(self, databus, settings, **kwargs):
        super(TractionView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = databus
        self._settings = settings
        self._initialized = False

    def init_view(self):
        data_bus = self._databus
        settings = self._settings

        gauges = list(kvFindClass(self, Gauge))

        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = data_bus
        self._initialized = True

        self.ids.imu_gauge.zoom = 0.5

    def on_tracks_updated(self, trackmanager):
        pass

    def on_enter(self):
        if not self._initialized:
            self.init_view()
        super(TractionView, self).on_enter()
