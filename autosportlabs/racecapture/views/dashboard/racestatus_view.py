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
from kivy.properties import StringProperty
from kivy.app import Builder
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.widgets.imugauge import ImuGauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen
from autosportlabs.racecapture.views.dashboard.widgets.trackmapgauge import TrackMapGauge

from kivy.core.image import Image as CoreImage

from utils import kvFind, kvFindClass
from kivy.clock import Clock
from utils import kvFindClass

RACE_STATUS_VIEW_KV = """
<RaceStatusView>:
    AnchorLayout:
        anchor_x: 'left'
        BoxLayout:
            size_hint_x: 0.6
            orientation: 'horizontal'
            AnchorLayout:
                padding: (dp(10), dp(10))
                FieldLabel:
                    id: track_status
                    size_hint_y: 0.1
                    halign: 'center'
                    text: root.track_status            
                TrackMapGauge:
                    id: track
    
    AnchorLayout:
        anchor_x: 'right'
        BoxLayout:
            size_hint_x: 0.6
            padding: (dp(10), dp(10))       
            orientation: 'vertical'
            
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: None
                height: dp(200)
                BoxLayout:
                    orientation: 'vertical'
                    CurrentLaptime:
                        size_hint_y: 0.55
                        id: currentlaptime
                        font_size: self.height * 1.0
                        halign: 'right'
                    TimeDelta:
                        size_hint_y: 0.45
                        id: timedelta
                        font_size: self.height * 1.0
                        halign: 'right'
                        channel: 'LapDelta'

                BigNumberView:
                    padding: [dp(10), 0, 0, 0]
                    rcid: 'bignumberview_laptime'
                    size_hint_x: 0.35
                    channel: 'CurrentLap'
                    warning_color: [0.2, 0.2, 0.2, 1.0]
                    alert_color: [0.2, 0.2, 0.2, 1.0]
                
            Widget:
                
            BoxLayout:
                size_hint_y: None
                height: dp(200)
                orientation: 'horizontal'
                Widget:
                    size_hint_x: 0.01
                        
                BoxLayout:
                    orientation: 'vertical'
                                                                   
                    BoxLayout:
                        size_hint_y: 0.4
                        Widget:
                            size_hint_x: 0.3
                        GaugeFrame:
                            halign: 'right'
                            Laptime:
                                channel: 'BestLap'
                                id: lastlap2
                                halign: 'right'
                                normal_color: [1.0, 0.0 , 1.0, 1.0]
                                font_size: self.height * 1.0


                    Widget:
                        size_hint_y: 0.05
                        
                    BoxLayout:
                        size_hint_y: 0.4
                        Widget:
                            size_hint_x: 0.3                        
                        GaugeFrame:
                            halign: 'right'
                            Laptime:
                                channel: 'LapTime'
                                id: lastlap
                                halign: 'right'
                                normal_color: [1.0, 1.0 , 0.0, 1.0]
                                font_size: self.height * 1.0

    
    
                    
"""

class RaceStatusView(DashboardScreen):
    Builder.load_string(RACE_STATUS_VIEW_KV)
    track_status = StringProperty('Waiting for track')

    def __init__(self, databus, settings, dashboard_state, track_manager, status_pump, **kwargs):
        super(RaceStatusView, self).__init__(**kwargs)
        self.register_event_type('on_tracks_updated')
        self._databus = databus
        self._settings = settings
        self._dashboard_state = dashboard_state
        self._track_manager = track_manager
        self._current_track_id = None
        self._initialized = False
        status_pump.add_listener(self._update_track_status)

    def init_view(self):
        data_bus = self._databus
        settings = self._settings

        gauges = list(kvFindClass(self, Gauge))

        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = data_bus
            gauge.dashboard_state = self._dashboard_state
        self._initialized = True


    def on_tracks_updated(self, trackmanager):
        pass

    def _update_track_status(self, status_data):
        track_status = status_data['status']['track']
        track_id = track_status['trackId']
        if track_id == 0:
            self.track_status = 'Waiting for track'
        elif self._current_track_id != track_id:
            track = self._track_manager.find_track_by_short_id(track_status['trackId'])
            if track is not None:
                self.ids.track.init_map(track)
                self._current_track_id = track_id
                self.track_status = ''

    def on_enter(self):
        if not self._initialized:
            self.init_view()
        super(RaceStatusView, self).on_enter()
