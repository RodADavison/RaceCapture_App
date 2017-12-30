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
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.properties import ListProperty
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color, Line
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.uix.track.trackmap import TrackMapView
from autosportlabs.racecapture.theme.color import ColorScheme
from utils import *

RACETRACK_VIEW_KV = """
<RaceTrackView>:
    orientation: 'vertical'
    TrackMapView:
        track_color: root.track_color
        id: trackmap
"""
class RaceTrackView(BoxLayout):
    Builder.load_string(RACETRACK_VIEW_KV)
    track_color = ListProperty(ColorScheme.get_primary())
    
    def __init__(self, **kwargs):
        super(RaceTrackView, self).__init__(**kwargs)

    def loadTrack(self, track):
        self.initMap(track)

    def initMap(self, track):
        self.ids.trackmap.setTrackPoints(track.map_points)
        self.ids.trackmap.sector_points = track.sector_points
        self.ids.trackmap.start_point = track.start_finish_point
        self.ids.trackmap.finish_point = track.finish_point

    def remove_reference_mark(self, key):
        self.ids.trackmap.remove_marker(key)

    def add_reference_mark(self, key, color):
        trackmap = self.ids.trackmap
        if trackmap.get_marker(key) is None:
            trackmap.add_marker(key, color)

    def update_reference_mark(self, key, geo_point):
        self.ids.trackmap.update_marker(key, geo_point)

    def add_map_path(self, key, path, color):
        self.ids.trackmap.add_path(key, path, color)

    def remove_map_path(self, key):
        self.ids.trackmap.remove_path(key)

    def add_heat_values(self, key, heat_values):
        self.ids.trackmap.add_heat_values(key, heat_values)

    def remove_heat_values(self, key):
        self.ids.trackmap.remove_heat_values(key)
