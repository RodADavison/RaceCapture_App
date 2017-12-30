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
from kivy.app import Builder
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.views.setup.infoview import InfoView
from autosportlabs.uix.button.betterbutton import BetterToggleButton
from autosportlabs.racecapture.views.tracks.tracksview import TrackCollectionScreen
from fieldlabel import FieldLabel

SELECT_TRACKS_VIEW_KV = """
<SelectTracksView>:
    background_source: 'resource/setup/background_blank.png'
    info_text: 'Select your favorite tracks'
    BoxLayout:
        orientation: 'vertical'
        padding: [0, dp(20)]
        spacing: [0, dp(10)]
        BoxLayout:
            size_hint_y: 0.10
        TrackCollectionScreen:
            id: track_list
            size_hint_y: 0.7
        Widget:
            size_hint_y: None
            height: dp(50)
    """

class SelectTracksView(InfoView):
    """
    A setup screen that lets users select what tracks they have
    """
    Builder.load_string(SELECT_TRACKS_VIEW_KV)

    def __init__(self, **kwargs):
        super(SelectTracksView, self).__init__(**kwargs)
        self._tracks_modified = False
        self.ids.next.pulsing = False

    def on_setup_config(self, instance, value):
        self._update_ui()
        self.ids.next.disabled = False

    def _update_ui(self):
        track_list = self.ids.track_list
        track_list.track_manager = self.track_manager
        track_list.on_config_updated(self.rc_config.trackDb)
        track_list.disableView(False)
        track_list.bind(on_modified=self._on_tracks_modified)

    def _on_tracks_modified(self, *args):
        self._tracks_modified = True
        self.ids.next.pulsing = True

    def select_next(self):
        def do_next():
            super(SelectTracksView, self).select_next()

        if self._tracks_modified:
            self.write_rcp_config('Updating Tracks ... ', do_next)
        else:
            self.info_popup('You can customize tracks later under Setup', do_next)
