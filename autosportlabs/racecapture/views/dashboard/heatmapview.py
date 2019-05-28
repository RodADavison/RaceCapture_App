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
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.logger import Logger
from kivy.uix.modalview import ModalView
from kivy.uix.settings import SettingsWithNoMenu
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.dashboard.dashboardscreen import DashboardScreen
from autosportlabs.racecapture.views.dashboard.widgets.imugauge import ImuGauge
from autosportlabs.racecapture.views.dashboard.widgets.trackmapgauge import TrackMapGauge
from autosportlabs.racecapture.views.dashboard.widgets.heatmapgauge import HeatmapCornerGauge
from utils import kvFindClass

class HeatmapContainer(ButtonBehavior, BoxLayout):
    pass

HEATMAP_VIEW_KV = """
<HeatmapView>:
    BoxLayout:
        orientation: 'horizontal'
        HeatmapContainer:
            on_press: root.on_heatmap_options()
            size_hint_x: 0.6
            orientation: 'vertical'
            spacing: dp(10)        
            BoxLayout:
                spacing: dp(10)
                orientation: 'horizontal'
                HeatmapCornerLeftGauge:
                    id: corner_fl
                    corner_prefix: 'FL'
                HeatmapCornerRightGauge:
                    id: corner_fr
                    corner_prefix: 'FR'
            BoxLayout:
                spacing: dp(10)        
                orientation: 'horizontal'
                HeatmapCornerLeftGauge:
                    id: corner_rl
                    corner_prefix: 'RL'
                HeatmapCornerRightGauge:
                    id: corner_rr
                    corner_prefix: 'RR'
        AnchorLayout:
            size_hint_x: 0.4
            BoxLayout:
                orientation: 'vertical'
                                
                AnchorLayout:
                    size_hint_y: 0.6
                    FieldLabel:
                        id: track_name
                        size_hint_y: 0.1
                        halign: 'center'
                        text: 'Waiting for track'
                    AnchorLayout:
                        anchor_y: 'top'
                        padding: (dp(10), dp(10))
                        TrackMapGauge:
                            id: track
                            size_hint: (1.0, 1.0)
                ImuGauge:
                    id: imu
                    size_hint_y: 0.4
                    zoom: 0.5
                    rcid: 'heatmap_view_imu'
"""

class HeatmapView(DashboardScreen):
    Builder.load_string(HEATMAP_VIEW_KV)
    _POPUP_SIZE_HINT = (0.75, 0.8)

    def __init__(self, databus, settings, dashboard_state, track_manager, status_pump, **kwargs):
        super(HeatmapView, self).__init__(**kwargs)
        self._initialized = False
        self.register_event_type('on_tracks_updated')
        self._databus = databus
        self._settings = settings
        self._dashboard_state = dashboard_state
        self._track_manager = track_manager
        status_pump.add_listener(self._update_track_status)
        self._current_track_id = None
        self._set_default_preferences()
        self._update_heatmap_preferences()

    def _set_default_preferences(self):
        config = self._settings.userPrefs.config
        config.adddefaultsection('heatmap_preferences')
        config.setdefault('heatmap_preferences', 'tire_temp_channel_prefix', HeatmapCornerGauge.DEFAULT_TIRE_CHANNEL_PREFIX)
        config.setdefault('heatmap_preferences', 'brake_temp_channel_prefix', HeatmapCornerGauge.DEFAULT_BRAKE_CHANNEL_PREFIX)
        config.setdefault('heatmap_preferences', 'tire_zones_fl', '1')
        config.setdefault('heatmap_preferences', 'tire_zones_fr', '1')
        config.setdefault('heatmap_preferences', 'tire_zones_rl', '1')
        config.setdefault('heatmap_preferences', 'tire_zones_rr', '1')
        config.setdefault('heatmap_preferences', 'brake_zones_fl', '1')
        config.setdefault('heatmap_preferences', 'brake_zones_fr', '1')
        config.setdefault('heatmap_preferences', 'brake_zones_rl', '1')
        config.setdefault('heatmap_preferences', 'brake_zones_rr', '1')

    def _update_heatmap_preferences(self):
        zones = ['fl', 'fr', 'rl', 'rr']
        config = self._settings.userPrefs.config
        for zone in zones:
            tire_zones = config.get('heatmap_preferences', 'tire_zones_{}'.format(zone))
            brake_zones = config.get('heatmap_preferences', 'brake_zones_{}'.format(zone))
            tire_zones = 0 if tire_zones == 'None' else int(tire_zones)
            brake_zones = 0 if brake_zones == 'None' else int(brake_zones)
            corner_widget = self.ids.get('corner_{}'.format(zone))
            corner_widget.tire_zones = tire_zones
            corner_widget.brake_zones = brake_zones

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

    def on_enter(self):
        if not self._initialized:
            self.init_view()
        super(HeatmapView, self).on_enter()

    def _update_track_status(self, status_data):
        track_status = status_data['status']['track']
        track_id = track_status['trackId']
        if track_id == 0:
            self._set_state_message('Waiting for track')
        elif self._current_track_id != track_id:
            track = self._track_manager.find_track_by_short_id(track_status['trackId'])
            if track is not None:
                self.ids.track.init_map(track)
                self._current_track_id = track_id
                self._set_state_message('')

    def _set_state_message(self, msg):
        self.ids.track_name.text = msg

    def on_heatmap_options(self):
        def popup_dismissed(response):
            self._update_heatmap_preferences()

        settings_view = SettingsWithNoMenu()
        base_dir = self._settings.base_dir
        settings_view.add_json_panel('Heatmap Settings',
                                     self._settings.userPrefs.config,
                                     os.path.join(base_dir,
                                                  'autosportlabs',
                                                  'racecapture',
                                                  'views',
                                                  'dashboard',
                                                  'heatmap_settings.json'))

        popup = ModalView(size_hint=HeatmapView._POPUP_SIZE_HINT)
        popup.add_widget(settings_view)
        popup.bind(on_dismiss=popup_dismissed)
        popup.open()
