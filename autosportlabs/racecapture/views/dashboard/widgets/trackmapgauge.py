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
from kivy.app import Builder
from kivy.properties import ObjectProperty, ListProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.uix.track.racetrackview import RaceTrackView
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from kivy.clock import Clock
RACETRACK_GAUGE_KV = """
<TrackMapGauge>:
    RaceTrackView:
        id: track
"""

class TrackMapGauge(Gauge):
    Builder.load_string(RACETRACK_GAUGE_KV)
    REFERENCE_MARK_KEY = "live"
    channel_metas = ObjectProperty()
    reference_mark_color = [1.0, 1.0, 1.0, 1.0]
    position = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super(TrackMapGauge, self).__init__(**kwargs)

    def on_data_bus(self, instance, value):
        self._update_channel_binding()

    def _update_channel_binding(self):
        data_bus = self.data_bus
        if data_bus is None:
            return

        data_bus.addChannelListener("Latitude", self._set_latitude)
        data_bus.addChannelListener("Longitude", self._set_longitude)

        data_bus.addMetaListener(self.on_channel_meta)
        meta = data_bus.getMeta()
        if len(data_bus.getMeta()) > 0:
            self.on_channel_meta(meta)

    def _set_latitude(self, value):
        self.position = [value, self.position[1]]

    def _set_longitude(self, value):
        self.position = [self.position[0], value]

    def on_position(self, instance, value):
        self._update_reference_mark()

    def _update_reference_mark(self):
        point = self.position
        self.ids.track.update_reference_mark(TrackMapGauge.REFERENCE_MARK_KEY, GeoPoint.fromPoint(point[0], point[1]))
        
    def _update_channel_metas(self):
        channel_metas = self.channel_metas
        if channel_metas is None:
            return

    def on_channel_meta(self, channel_metas):
        self.channel_metas = channel_metas

    def on_channel_metas(self, instance, value):
        self._update_channel_metas()

    def init_map(self, track):
        self.ids.track.initMap(track)
        self.ids.track.add_reference_mark(TrackMapGauge.REFERENCE_MARK_KEY, TrackMapGauge.reference_mark_color)
        self._update_reference_mark()


