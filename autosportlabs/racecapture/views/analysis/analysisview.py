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

import os.path
import kivy
import traceback
kivy.require('1.10.0')
from threading import Thread
from kivy.logger import Logger
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from autosportlabs.racecapture.views.analysis.analysisdata import CachingAnalysisDatastore
from autosportlabs.racecapture.datastore.datastore import InvalidChannelException
from autosportlabs.racecapture.views.analysis.analysismap import AnalysisMap
from autosportlabs.racecapture.views.analysis.channelvaluesview import ChannelValuesView
from autosportlabs.racecapture.views.analysis.addstreamview import AddStreamView
from autosportlabs.racecapture.views.analysis.sessionlistview import SessionListView
from autosportlabs.racecapture.views.analysis.flyinpanel import FlyinPanel
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent, SourceRef
from autosportlabs.racecapture.views.analysis.linechart import LineChart
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup, progress_popup
from autosportlabs.uix.color.colorsequence import ColorSequence
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.racecapture.settings.prefs import UserPrefs
from autosportlabs.help.helpmanager import HelpInfo
from kivy.core.window import Window


RC_LOG_FILE_EXTENSION = '.log'

ANALYSIS_VIEW_KV = '''
<AnalysisView>:
    AnchorLayout:
        BoxLayout:
            orientation: 'vertical'
            BoxLayout:
                padding: (sp(10), sp(10), sp(10), sp(5))
                spacing: sp(10)       
                size_hint_y: 0.5
                orientation: 'horizontal'
                AnalysisMap:
                    id: analysismap
            AnchorLayout:
                spacing: sp(10)       
                padding: (sp(10), sp(5), sp(10), sp(10))
                size_hint_y: 0.5            
                AnchorLayout:
                    LineChart:
                        id: mainchart
                        on_channel_selected: root.on_channel_selected(*args)
                        on_marker: root.on_marker(*args)
                AnchorLayout:
                    anchor_x: 'right'
                    anchor_y: 'top'
                    ChannelValuesView:
                        size_hint_x: None
                        width: min(dp(390), 0.55 * root.width)
                        id: channelvalues

        FlyinPanel:
            id: laps_flyin
            BoxLayout:
                orientation: 'vertical'
                SessionListView:
                    size_hint_y: 0.9
                    id: sessions_view
                IconButton:
                    size_hint_y: 0.1
                    font_size: root.height * 0.1
                    text: u'\uf0fe'
                    on_release: root.on_add_stream()

            Label:
                text: 'Sessions'
                size_hint_y: 0.05
'''


class AnalysisView(Screen):
    SUGGESTED_CHART_CHANNELS = ['Speed']
    INIT_DATASTORE_TIMEOUT = 10.0
    _settings = None
    _databus = None
    _track_manager = None
    _popup = None
    _color_sequence = ColorSequence()
    sessions = ObjectProperty(None)
    Builder.load_string(ANALYSIS_VIEW_KV)

    def __init__(self, datastore, databus, settings, track_manager, session_recorder, **kwargs):
        super(AnalysisView, self).__init__(**kwargs)
        self._datastore = datastore
        self.register_event_type('on_tracks_updated')
        self._databus = databus
        self._settings = settings
        self._track_manager = track_manager
        self._session_recorder = session_recorder
        self.ids.sessions_view.bind(on_lap_selection=self.lap_selection)
        self.ids.sessions_view.bind(on_session_updated=self.session_updated)
        self.ids.sessions_view.bind(on_sessions_loaded=self.sessions_loaded)
        self.ids.channelvalues.color_sequence = self._color_sequence
        self.ids.mainchart.color_sequence = self._color_sequence
        self.stream_connecting = False
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_motion=self.on_motion)
        self._layout_complete = False

    def on_motion(self, instance, event, motion_event):
        flyin = self.ids.laps_flyin
        if self.collide_point(motion_event.x, motion_event.y):
            if not flyin.flyin_collide_point(motion_event.x, motion_event.y):
                flyin.schedule_hide()

    def on_mouse_pos(self, x, pos):
        flyin = self.ids.laps_flyin
        x = pos[0]
        y = pos[1]
        self_collide = self.collide_point(x, y)
        flyin_collide = flyin.flyin_collide_point(x, y)
        laps_selected = self.ids.sessions_view.selected_count > 0

        if self_collide and not flyin_collide and laps_selected:
            flyin.schedule_hide()
        return False

    def on_pre_enter(self, *args):
        # immediately stop any session recording if we're entering analysis view
        self._session_recorder.stop(stop_now=True)

    def on_sessions(self, instance, value):
        self.ids.channelvalues.sessions = value

    def session_updated(self, instance, session):
        self.ids.channelvalues.refresh_view()
        self.ids.analysismap.refresh_view()

    def sessions_loaded(self, instance):
        if self.ids.sessions_view.session_count == 0:
            self.show_add_stream_dialog()

    def lap_selection(self, instance, source_ref, selected):
        source_key = str(source_ref)
        if selected:
            self.ids.mainchart.add_lap(source_ref)
            self.ids.channelvalues.add_lap(source_ref)
            map_path_color = self._color_sequence.get_color(source_key)
            self.ids.analysismap.add_reference_mark(source_key, map_path_color)
            self._sync_analysis_map(source_ref.session)
            self._datastore.get_location_data(source_ref, lambda x: self.ids.analysismap.add_map_path(source_ref, x, map_path_color))

        else:
            self.ids.mainchart.remove_lap(source_ref)
            self.ids.channelvalues.remove_lap(source_ref)
            self.ids.analysismap.remove_reference_mark(source_key)
            self.ids.analysismap.remove_map_path(source_ref)

    def on_tracks_updated(self, track_manager):
        self.ids.analysismap.track_manager = track_manager

    def on_channel_selected(self, instance, value):
        channels = self.ids.channelvalues.merge_selected_channels(value)
        self._set_suggested_channels(channels)

    def on_marker(self, instance, marker):
        source = marker.sourceref
        self.ids.channelvalues.update_reference_mark(source, marker.data_index)
        cache = self._datastore.get_location_data(source)
        if cache != None:
            try:
                point = cache[marker.data_index]
            except IndexError:
                point = cache[len(cache) - 1]
            self.ids.analysismap.update_reference_mark(source, point)

    def _sync_analysis_map(self, session):
        analysis_map = self.ids.analysismap
        current_track = analysis_map.track

        lat_avg, lon_avg = self._datastore.get_location_center([session])
        new_track = analysis_map.select_map(lat_avg, lon_avg)

        if current_track != new_track:
            # if a new track is selected, then
            # unselect all laps for all other sessions
            sessions_view = self.ids.sessions_view
            sessions_view.deselect_other_laps(session)

    def open_datastore(self):
        pass

    def on_add_stream(self, *args):
        self.show_add_stream_dialog()

    def on_stream_connected(self, instance, new_session_id):
        self.stream_connecting = False
        self._dismiss_popup()
        if new_session_id:
            session = self._datastore.get_session_by_id(new_session_id)
            self.ids.sessions_view.append_session(session)
            self.check_load_suggested_lap(new_session_id)

    def _set_suggested_channels(self, channels):
        self._settings.userPrefs.set_pref_list('analysis_preferences', 'selected_analysis_channels', channels)

    # The following selects a best lap if there are no other laps currently selected
    def check_load_suggested_lap(self, new_session_id):
        sessions_view = self.ids.sessions_view
        if len(sessions_view.selected_laps) == 0:
            if self._datastore.session_has_laps(new_session_id):
                best_lap = self._datastore.get_channel_min('LapTime', [new_session_id], ['LapCount'])
                best_lap_id = best_lap[1]
                if best_lap_id:
                    Logger.info('AnalysisView: Convenience selected a suggested session {} / lap {}'.format(new_session_id, best_lap_id))
                    main_chart = self.ids.mainchart
                    sessions_view.select_lap(new_session_id, best_lap_id, True)
                    HelpInfo.help_popup('suggested_lap', main_chart, arrow_pos='left_mid')
                else:
                    Logger.info('AnalysisView: No best lap could be determined; selecting first lap by default for session {}'.format(new_session_id))
                    sessions_view.select_lap(new_session_id, 1, True)
            else:
                sessions_view.select_lap(new_session_id, 1, True)


    def on_stream_connecting(self, *args):
        self.stream_connecting = True

    def show_add_stream_dialog(self):
        self.stream_connecting = False
        content = AddStreamView(settings=self._settings, datastore=self._datastore)
        content.bind(on_connect_stream_start=self.on_stream_connecting)
        content.bind(on_connect_stream_complete=self.on_stream_connected)
        content.bind(on_add_session=self.on_add_session)
        content.bind(on_delete_session=self.on_delete_session)
        content.bind(on_export_session=self.on_export_session)
        content.bind(on_close=self.close_popup)

        popup = Popup(title="Add Session", content=content, size_hint=(0.95, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup

    def close_popup(self, *args):
        if self._popup:
            self._popup.dismiss()

    def on_add_session(self, instance, session):
        self.ids.sessions_view.append_session(session)
        self.check_load_suggested_lap(session.session_id)

    def on_delete_session(self, instance, session):
        self.ids.sessions_view.session_deleted(session)


    def on_export_session(self, instance, session):

        def _export_session(instance):

            def _do_export_session(filename):

                _do_export_session.cancelled = False

                def _progress_cb(pct):
                    if _do_export_session.cancelled == True:
                        return True
                    Clock.schedule_once(lambda dt: prog_popup.content.update_progress(pct))
                    return False

                def _progress_ok_cancel(instance, answer):
                    _do_export_session.cancelled = True
                    Clock.schedule_once(lambda dt: prog_popup.dismiss(), 2.0 if instance.progress < 100 else 0.0)

                def _export_complete(title, text):
                    progress = prog_popup.content
                    progress.title = title
                    progress.text = text
                    progress.progress = 100

                def _export_session_worker(filename, session_id, progress_cb):
                    try:
                        export_file = open(filename, 'w')
                        with export_file:
                            records = self._datastore.export_session(session_id, export_file, progress_cb)
                            Clock.schedule_once(lambda dt: _export_complete('Export complete', '{} samples exported'.format(records)))
                            Clock.schedule_once(lambda dt: self._settings.userPrefs.set_pref('preferences', 'export_file_dir', os.path.dirname(filename)))
                    except Exception as e:
                        Logger.error('AnalysisView: Error exporting: {}'.format(e))
                        Logger.error(traceback.format_exc())
                        Clock.schedule_once(lambda dt: _export_complete('Error Exporting',
                            "There was an error exporting the session. Please check the destination and file name\n\n{}".format(e)))

                export_popup.dismiss()

                prog_popup = progress_popup('Exporting session', 'Exporting Session', _progress_ok_cancel)
                t = Thread(target=_export_session_worker, args=(filename, session.session_id, _progress_cb))
                t.daemon = True
                t.start()

            filename = os.path.join(instance.path, instance.filename)
            if not filename.endswith(RC_LOG_FILE_EXTENSION): filename += RC_LOG_FILE_EXTENSION
            if os.path.isfile(filename):
                def _on_overwrite_answer(instance, answer):
                    if answer:
                        _do_export_session(filename)
                    ow_popup.dismiss()
                ow_popup = confirmPopup('Confirm', 'File Exists - overwrite?', _on_overwrite_answer)
            else:
                _do_export_session(filename)

        export_dir = self._settings.userPrefs.get_pref('preferences', 'export_file_dir')
        content = SaveDialog(ok=_export_session,
                             cancel=lambda *args: export_popup.dismiss(),
                             filters=['*' + RC_LOG_FILE_EXTENSION],
                             user_path=export_dir)

        export_popup = Popup(title="Export Session", content=content, size_hint=(0.9, 0.9))
        export_popup.open()

    def init_view(self):
        mainchart = self.ids.mainchart
        mainchart.settings = self._settings
        mainchart.datastore = self._datastore
        mainchart.settings = self._settings
        channelvalues = self.ids.channelvalues
        channelvalues.datastore = self._datastore
        channelvalues.settings = self._settings
        self.ids.analysismap.track_manager = self._track_manager
        self.ids.analysismap.datastore = self._datastore
        self.ids.analysismap.settings = self._settings
        self.ids.sessions_view.datastore = self._datastore
        self.ids.sessions_view.settings = self._settings
        self.ids.sessions_view.init_view()
        Clock.schedule_once(lambda dt: HelpInfo.help_popup('analysis_welcome', self, arrow_pos='right_mid'), 0.5)

    def do_layout(self, *largs):
        super(AnalysisView, self).do_layout(largs)
        if not self._layout_complete:
            Clock.schedule_once(lambda dt: self.init_view(), 0.5)
        self._layout_complete = True

    def popup_dismissed(self, *args):
        if self.stream_connecting:
            return True
        self._popup = None

    def _dismiss_popup(self, *args):
        if self._popup is not None:
            self._popup.dismiss()
            self._popup = None

