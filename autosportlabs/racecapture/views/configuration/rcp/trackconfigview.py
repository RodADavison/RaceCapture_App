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
import time
kivy.require('1.10.0')

from kivy.properties import ObjectProperty
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.app import Builder
from helplabel import HelpLabel
from fieldlabel import FieldLabel
from settingsview import *
from valuefield import FloatValueField
from iconbutton import LabelIconButton
from autosportlabs.racecapture.config.rcpconfig import GpsConfig, GpsSample
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.tracks.tracksview import TrackInfoView, TrackSelectView, TrackCollectionScreen
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.uix.toast.kivytoast import toast
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.util.alertview import editor_popup
from autosportlabs.racecapture.tracks.trackmanager import TrackManager, TrackMap
from autosportlabs.racecapture.views.configuration.rcp.track.trackbuilder import TrackBuilderView

GPS_STATUS_POLL_INTERVAL = 1.0
GPS_NOT_LOCKED_COLOR = [0.7, 0.7, 0.0, 1.0]
GPS_LOCKED_COLOR = [0.0, 1.0, 0.0, 1.0]

SECTOR_POINT_VIEW_KV = """
<SectorPointView>:
    BoxLayout:
        orientation: 'horizontal'
        Label:
            text: "Sector"
            id: title
            size_hint_x: 0.25
        FieldLabel:
            size_hint_x: 0.25        
            id: lat
        FieldLabel:
            size_hint_x: 0.25
            id: lon
        IconButton:
            id: gps_target
            size_hint_x: 0.125
            text: u'\uf05b'
            font_size: self.height * 0.6
            on_release: root.on_update_target(*args)
        IconButton:
            size_hint_x: 0.125
            text: u'\uf013'
            font_size: self.height * 0.6
            on_release: root.on_customize(*args)
"""

class SectorPointView(BoxLayout):
    Builder.load_string(SECTOR_POINT_VIEW_KV)
    def __init__(self, **kwargs):
        super(SectorPointView, self).__init__(**kwargs)
        self.gps_sample = kwargs.get('gps_sample')
        self.register_event_type('on_config_changed')
        self.point = None
        title = kwargs.get('title', None)
        if title:
            self.set_title(title)
        Clock.schedule_interval(self.update_gps_status, GPS_STATUS_POLL_INTERVAL)

    def _get_gps_quality(self):
        return 0 if self.gps_sample is None else self.gps_sample.gps_qual

    def update_gps_status(self, *args):
        self.ids.gps_target.color = GPS_NOT_LOCKED_COLOR if self._get_gps_quality() < GpsConfig.GPS_QUALITY_2D else GPS_LOCKED_COLOR

    def on_config_changed(self):
        pass

    def set_title(self, title):
        self.ids.title.text = title

    def on_update_target(self, *args):
        try:
            if self._get_gps_quality() >= GpsConfig.GPS_QUALITY_2D:
                point = self.point
                point.latitude = self.gps_sample.latitude
                point.longitude = self.gps_sample.longitude
                self._refresh_point_view()
                self.dispatch('on_config_changed')
                toast('Target updated')
            else:
                toast('No GPS Fix', True)
        except Exception as e:
            toast('Error reading GPS target')

    def _on_edited(self, instance, value):
        self.set_point(value)
        self.dispatch('on_config_changed')

    def on_customize(self, *args):
        if self.point:
            content = GeoPointEditor(self.point, self.gps_sample)
            popup = Popup(title='Edit Track Target',
                          content=content,
                          size_hint=(None, None), size=(dp(500), dp(220)))
            content.bind(on_close=lambda *args:popup.dismiss())
            content.bind(on_point_edited=self._on_edited)
            popup.open()

    def _refresh_point_view(self):
        self.ids.lat.text = str(self.point.latitude)
        self.ids.lon.text = str(self.point.longitude)

    def set_point(self, point):
        self.point = point
        self._refresh_point_view()

GEOPOINT_EDITOR_KV = """
<GeoPointEditor>:
    orientation: 'vertical'
    BoxLayout:
        size_hint_y: 0.75
        orientation: 'horizontal'
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: 0.8
            BoxLayout:
                size_hint_y: 0.3
                orientation: 'horizontal'
                FieldLabel:
                    halign: 'center'
                    text: 'Latitude'
                FieldLabel:
                    halign: 'center'
                    text: 'Longitude'
            BoxLayout:
                size_hint_y: 0.3
                orientation: 'horizontal'
                FloatValueField:
                    id: lat
                    on_text: root.on_latitude(*args)                
                FloatValueField:
                    id: lon
                    on_text: root.on_longitude(*args)
            BoxLayout:
                size_hint_y: 0.4
                
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(20)
            padding: (dp(5), dp(5))
            size_hint_x: 0.2
            IconButton: 
                text: u'\uf0ea'
                id: paste
                on_press: root.on_paste_point()
            IconButton:
                text: u'\uf05b'
                id: gps_target
                on_press: root.on_update_target()
    IconButton:
        size_hint_y: 0.25
        text: "\357\200\214"
        on_press: root.close()
"""

class GeoPointEditor(BoxLayout):
    Builder.load_string(GEOPOINT_EDITOR_KV)
    def __init__(self, point, gps_sample, **kwargs):
        super(GeoPointEditor, self).__init__(**kwargs)
        self.point = point
        self._gps_sample = gps_sample
        self.register_event_type('on_point_edited')
        self.register_event_type('on_close')
        self._refresh_view(self.point.latitude, self.point.longitude)
        self.ids.lat.set_next(self.ids.lon)
        self.ids.lon.set_next(self.ids.lat)
        Clock.schedule_interval(self.update_gps_status, GPS_STATUS_POLL_INTERVAL)

    def on_latitude(self, instance, value):
        pass

    def on_longitude(self, instance, value):
        pass

    def _refresh_view(self, latitude, longitude):
        self.ids.lat.text = str(latitude)
        self.ids.lon.text = str(longitude)

    def on_point_edited(self, *args):
        pass

    def on_close(self, *args):
        pass

    def on_paste_point(self, *args):
        try:
            point_string = Clipboard.get('UTF8_STRING')
            lat_lon = point_string.split(",")
            lat = float(lat_lon[0])
            lon = float(lat_lon[1])
            self.ids.lat.text = str(lat)
            self.ids.lon.text = str(lon)
        except ValueError as e:
            Logger.error("GeoPointEditor: error handling paste: {}".format(e))
            toast('Required format is: Latitude, Longitude\nin NN.NNNNN decimal format', True)

    def update_gps_status(self, *args):
        gps_quality = self._get_gps_quality()
        self.ids.gps_target.color = GPS_NOT_LOCKED_COLOR if gps_quality < GpsConfig.GPS_QUALITY_2D else GPS_LOCKED_COLOR

    def _get_gps_quality(self):
        return 0 if self._gps_sample is None else self._gps_sample.gps_qual

    def on_update_target(self, *args):
        try:
            if self._get_gps_quality() >= GpsConfig.GPS_QUALITY_2D:
                self._refresh_view(self._gps_sample.latitude, self._gps_sample.longitude)
            else:
                toast('No GPS Fix', True)
        except Exception:
            toast('Error reading GPS target')

    def close(self):
        Clock.unschedule(self.update_gps_status)
        point = self.point
        try:
            point.latitude = float(self.ids.lat.text)
            point.longitude = float(self.ids.lon.text)
            self.dispatch('on_point_edited', self.point)
        except ValueError as e:
            Logger.error("GeoPointEditor: error closing: {}".format(e))
            toast('NN.NNNNN decimal latitude/longitude format required', True)
        self.dispatch('on_close')


AUTOMATIC_TRACK_CONFIG_SCREEN_KV = """
<AutomaticTrackConfigScreen>:
    TrackCollectionScreen:
        id: track_collection
"""
class AutomaticTrackConfigScreen(Screen):
    Builder.load_string(AUTOMATIC_TRACK_CONFIG_SCREEN_KV)
    track_manager = ObjectProperty(None)
    TRACK_ITEM_MIN_HEIGHT = 200
    def __init__(self, **kwargs):
        super(AutomaticTrackConfigScreen, self).__init__(**kwargs)
        tracks_view = self.ids.track_collection
        tracks_view._track_db = None
        tracks_view.bind(on_modified=self._on_modified)
        self.register_event_type('on_modified')

    def _on_modified(self, *args):
        self.dispatch('on_modified', args)

    def on_modified(self, *args):
        pass

    def on_config_updated(self, track_db):
        tracks_view = self.ids.track_collection
        tracks_view.on_config_updated(track_db)
        tracks_view.disableView(False)

    def on_track_manager(self, instance, value):
        tracks_view = self.ids.track_collection
        tracks_view.track_manager = value
        tracks_view.init_tracks_list()

    def disableView(self, disabled):
        self.ids.track_collection.disableView(disabled)

SINGLE_AUTO_CONFIG_SCREEN_KV = """
<SingleAutoConfigScreen>:
    AnchorLayout:
        TrackInfoView:
            id: track_info        
        FieldLabel:
            id: info_message
            size_hint_y: 0.2
            halign: 'center'
            text: ''    
        
        AnchorLayout:
            anchor_x: 'right'
            anchor_y: 'bottom'
            padding: (sp(10), sp(10))
            IconButton:
                color: ColorScheme.get_accent()
                size_hint: (None, None)
                height: root.height * .15
                text: u'\uf044'
                on_release: root.on_set_track_press()
"""

class SingleAutoConfigScreen(Screen):
    Builder.load_string(SINGLE_AUTO_CONFIG_SCREEN_KV)
    def __init__(self, track_manager, gps_sample, **kwargs):
        super(SingleAutoConfigScreen, self).__init__(**kwargs)
        self.register_event_type('on_modified')
        self._track_manager = track_manager
        self._gps_sample = gps_sample
        self._track_cfg = None

    def on_modified(self, *args):
        pass

    def _update_track(self):
        if self._track_cfg is None:
            return
        track = self._track_manager.find_track_by_short_id(self._track_cfg.track.trackId)
        self.ids.track_info.setTrack(track)
        self.ids.info_message.text = 'Waiting to detect track' if track is None else ''

    def on_config_updated(self, track_cfg):
        self._track_cfg = track_cfg
        self._update_track()

    def on_pre_enter(self, *args):
        self._update_track()

    def on_set_track_press(self, *args):
        def on_track_select_close(instance, answer):
            if answer:
                selected_track = content.selected_track
                if selected_track is None:
                    toast('Please select a track')
                    return
                if self._track_cfg:
                    Logger.info("SingleAutoConfigScreen: setting track: {}".format(selected_track.name))
                    track_cfg = Track.fromTrackMap(selected_track)
                    self._track_cfg.track = track_cfg
                    self._track_cfg.stale = True
                    self._update_track()
                    self.dispatch('on_modified')
            popup.dismiss()

        # use the current location, if available
        current_point = self._gps_sample.geopoint if self._gps_sample.is_locked else None
        content = TrackSelectView(track_manager=self._track_manager, current_location=current_point)
        popup = editor_popup("Select a track", content, on_track_select_close, size_hint=(0.9, 0.9))
        popup.open()


CUSTOM_TRACK_CONFIG_SCREEN_KV = """
<CustomTrackConfigScreen>:
    AnchorLayout:
        TrackInfoView:
            id: track_info
        AnchorLayout:
            anchor_x: 'right'
            anchor_y: 'bottom'
            padding: (sp(10), sp(10))

            IconButton:
                color: ColorScheme.get_accent()
                size_hint: (None, None)
                height: root.height * .15
                text: u'\uf044'
                on_release: root.on_advanced_track_editor()
        AnchorLayout:
            anchor_x: 'left'
            anchor_y: 'bottom'
            padding: (sp(10), sp(10))
            
            IconButton:
                color: ColorScheme.get_accent()
                size_hint: (None, None)
                height: root.height * .15
                text: u'\uf055'
                on_release: root.track_builder()
        FieldLabel:
            id: info_message
            size_hint_y: 0.2
            halign: 'center'
            text: ''    
"""

class CustomTrackConfigScreen(Screen):
    Builder.load_string(CUSTOM_TRACK_CONFIG_SCREEN_KV)
    def __init__(self, track_manager, databus, rc_api, **kwargs):
        super(CustomTrackConfigScreen, self).__init__(**kwargs)
        self._track_manager = track_manager
        self._databus = databus
        self._rc_api = rc_api
        self.register_event_type('on_advanced_editor')
        self._track_cfg = None
        self.register_event_type('on_modified')

    def on_modified(self, *args):
        pass

    def on_advanced_track_editor(self, *args):
        self.dispatch('on_advanced_editor')

    def on_advanced_editor(self):
        pass

    def track_builder(self, *args):
        def popup_dismissed(instance):
            content.cleanup()

        def on_track_complete(instance, track_map):
            popup.dismiss()
            self._track_manager.add_track(track_map)
            self._track_cfg.track.import_trackmap(track_map)
            self._track_cfg.stale = True
            self._update_track()
            self.dispatch('on_modified')

        def on_close(instance, answer):
            popup.dismiss()

        content = TrackBuilderView(databus=self._databus, rc_api=self._rc_api, track_manager=self._track_manager)
        popup = editor_popup("Track Builder", content, on_close, hide_ok=True, size_hint=(0.9, 0.9))
        content.bind(on_track_complete=on_track_complete)
        popup.open()

    def _update_track(self):
        if self._track_cfg is None:
            return

        track = self._track_manager.find_track_by_short_id(self._track_cfg.track.trackId)
        self.ids.track_info.setTrack(track)
        self.ids.info_message.text = 'Press (+) to create your first track map' if track is None else ''

    def on_pre_enter(self, *args):
        self._update_track()

    def on_config_updated(self, track_cfg):
        self._track_cfg = track_cfg
        self._update_track()

MANUAL_TRACK_CONFIG_SCREEN_KV = """
<ManualTrackConfigScreen>:
    AnchorLayout:
        BoxLayout:
            orientation: 'vertical'
            SettingsView:
                size_hint_y: 0.2
                id: sep_startfinish
                label_text: 'Separate start and finish lines'
                help_text: 'Enable for Stage, Hill Climb or AutoX type courses'
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: 0.8
    
                SectorPointView:
                    id: start_line
                    size_hint_y: 0.15
                SectorPointView:
                    id: finish_line
                    size_hint_y: 0.15
    
                ScrollContainer:
                    id: scroller
                    size_hint_y: 0.6
                    do_scroll_x: False
                    GridLayout:
                        canvas.before:
                            Color:
                                rgba: 0.1, 0.1, 0.1, 1.0
                            Rectangle:
                                pos: self.pos
                                size: self.size
                        id: sectors_grid
                        row_default_height: root.height * 0.12
                        row_force_default: True
                        size_hint_y: None
                        height: max(self.minimum_height, scroller.height)
                        cols: 1
        AnchorLayout:
            anchor_x: 'left'
            anchor_y: 'bottom'
            padding: (sp(10), sp(10))
            IconButton:
                color: ColorScheme.get_accent()
                size_hint: (None, None)
                height: root.height * .15
                text: u'\uf0a8'
                on_release: root.custom_editor()
                    
"""
class ManualTrackConfigScreen(Screen):
    Builder.load_string(MANUAL_TRACK_CONFIG_SCREEN_KV)
    def __init__(self, gps_sample, **kwargs):
        super(ManualTrackConfigScreen, self).__init__(**kwargs)
        self._track_cfg = None
        self._gps_sample = gps_sample
        self.ids.sep_startfinish.bind(on_setting=self.on_separate_start_finish)
        self.ids.sep_startfinish.setControl(SettingsSwitch())

        self.ids.start_line.gps_sample = gps_sample
        self.ids.finish_line.gps_sample = gps_sample

        self.separate_startfinish = False
        self._init_sector_views()

        sectors_container = self.ids.sectors_grid
        sectors_container.height = dp(35) * CONFIG_SECTOR_COUNT
        sectors_container.size_hint = (1.0, None)

        self.register_event_type('on_modified')
        self.register_event_type('on_custom_editor')

    def on_modified(self, *args):
        pass

    def on_custom_editor(self, *args):
        pass

    def custom_editor(self):
        self.dispatch('on_custom_editor')

    def on_separate_start_finish(self, instance, value):
        if self._track_cfg:
            self._track_cfg.track.trackType = 1 if value else 0
            self._track_cfg.stale = True
            self.dispatch('on_modified')
            self.separate_startfinish = value
            self.update_trackview_state()

    def _init_sector_views(self):

        self.ids.sectors_grid.clear_widgets()

        self.ids.start_line.bind(on_config_changed=self.on_config_changed)
        self.ids.finish_line.bind(on_config_changed=self.on_config_changed)

        self.update_trackview_state()

    def on_config_changed(self, *args):
        self._track_cfg.stale = True
        self.dispatch('on_modified')

    def update_trackview_state(self):
        if not self.separate_startfinish:
            self.ids.start_line.set_title('Start / Finish')
            self.ids.finish_line.set_title('- - -')
            self.ids.finish_line.disabled = True
        else:
            self.ids.start_line.set_title('Start Line')
            self.ids.finish_line.set_title('Finish Line')
            self.ids.finish_line.disabled = False

    def on_config_updated(self, track_cfg):
        separateStartFinishSwitch = self.ids.sep_startfinish
        self.separate_startfinish = track_cfg.track.trackType == TRACK_TYPE_STAGE
        separateStartFinishSwitch.setValue(self.separate_startfinish)

        sectors_container = self.ids.sectors_grid

        sectors_container.clear_widgets()
        for i in range(0, len(track_cfg.track.sectors)):
            sectorView = SectorPointView(title='Sector {}'.format(i + 1), gps_sample=self._gps_sample)
            sectorView.bind(on_config_changed=self.on_config_changed)
            sectors_container.add_widget(sectorView)
            sectorView.set_point(track_cfg.track.sectors[i])

        self.ids.start_line.set_point(track_cfg.track.startLine)
        self.ids.finish_line.set_point(track_cfg.track.finishLine)

        self._track_cfg = track_cfg
        self.update_trackview_state()

TRACK_CONFIG_VIEW_KV = """
<TrackConfigView>:
    orientation: 'vertical'
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.20
        SettingsView:
            id: auto_detect
            label_text: 'Automatic race track detection'
            help_text: 'Automatically detect and configure your favorite tracks'
    ScreenManager:
        id: screen_manager
        size_hint_y: 0.80
"""
class TrackConfigView(BaseConfigView):
    Builder.load_string(TRACK_CONFIG_VIEW_KV)

    def __init__(self, status_pump, settings, databus, rc_api, track_manager, **kwargs):
        super(TrackConfigView, self).__init__(**kwargs)

        self._track_db_capable = False

        self._track_cfg = None
        self._track_db = None

        self._databus = databus
        self._rc_api = rc_api
        self._settings = settings
        self._track_manager = track_manager

        self._auto_config_screen = None
        self._advanced_config_screen = None
        self._single_autoconfig_screen = None
        self._custom_track_screen = None

        self.register_event_type('on_config_updated')

        self.ids.auto_detect.bind(on_setting=self.on_auto_detect)
        self.ids.auto_detect.setControl(SettingsSwitch())

        self._gps_sample = GpsSample()
        status_pump.add_listener(self.status_updated)

    def status_updated(self, status):
        status = status['status']['GPS']

        quality = status['qual']
        latitude = status['lat']
        longitude = status['lon']
        self._gps_sample.gps_qual = quality
        self._gps_sample.latitude = latitude
        self._gps_sample.longitude = longitude


    def _get_track_db_view(self):
        if self._auto_config_screen is None:
            self._auto_config_screen = AutomaticTrackConfigScreen()
            self._auto_config_screen.bind(on_modified=self.on_editor_modified)
            self._auto_config_screen.track_manager = self._track_manager
            if self._track_db is not None:
                self._auto_config_screen.on_config_updated(self._track_db)
        return self._auto_config_screen

    def _get_single_track_view(self):
        if self._single_autoconfig_screen is None:
            self._single_autoconfig_screen = SingleAutoConfigScreen(track_manager=self._track_manager, gps_sample=self._gps_sample)
            self._single_autoconfig_screen.bind(on_modified=self.on_editor_modified)
            if self._track_cfg is not None:
                self._single_autoconfig_screen.on_config_updated(self._track_cfg)
        return self._single_autoconfig_screen

    def _get_custom_track_screen(self):
        if self._custom_track_screen is None:
            self._custom_track_screen = CustomTrackConfigScreen(track_manager=self._track_manager, rc_api=self._rc_api, databus=self._databus)
            self._custom_track_screen.bind(on_advanced_editor=self._on_advanced_editor)
            self._custom_track_screen.bind(on_modified=self.on_editor_modified)
            self._custom_track_screen.on_config_updated(self._track_cfg)
        return self._custom_track_screen

    def _get_advanced_editor_screen(self, *args):
        if self._advanced_config_screen is None:
            self._advanced_config_screen = ManualTrackConfigScreen(gps_sample=self._gps_sample, rc_api=self._rc_api)
            self._advanced_config_screen.bind(on_modified=self.on_editor_modified)
            self._advanced_config_screen.bind(on_custom_editor=self._on_custom_editor)
            if self._track_cfg is not None:
                self._advanced_config_screen.on_config_updated(self._track_cfg)
        return self._advanced_config_screen

    def on_editor_modified(self, *args):
        if self._advanced_config_screen is not None:
            # synchronize the advanced config view with the updated track config
            self._advanced_config_screen.on_config_updated(self._track_cfg)

        self.dispatch('on_modified')

    def on_tracks_updated(self, track_manager):
        if self._auto_config_screen is not None:
            self._auto_config_screen.track_manager = track_manager

    def on_config_updated(self, rcp_cfg):
        track_cfg = rcp_cfg.trackConfig
        track_db = rcp_cfg.trackDb

        self._track_db_capable = rcp_cfg.capabilities.storage.tracks > 0

        self.ids.auto_detect.setValue(track_cfg.autoDetect)

        if self._advanced_config_screen is not None:
            self._advanced_config_screen.on_config_updated(track_cfg)

        if self._auto_config_screen is not None:
            self._auto_config_screen.on_config_updated(track_db)

        if self._single_autoconfig_screen is not None:
            self._single_autoconfig_screen.on_config_updated(track_cfg)

        if self._custom_track_screen is not None:
            self._custom_track_screen.on_config_updated(track_cfg)

        self._track_cfg = track_cfg
        self._track_db = track_db

        self._select_screen()

    def _select_screen(self):
        auto_detect_enabled = self.ids.auto_detect.control.active

        # For a given mode and capability
        # a variety of screens are valid.
        valid_screens = []
        if auto_detect_enabled:
            if self._track_db_capable:
                valid_screens.append(self._get_track_db_view())
            else:
                valid_screens.append(self._get_single_track_view())
        else:
            valid_screens.append(self._get_custom_track_screen())
            valid_screens.append(self._get_advanced_editor_screen())

        # If the current screen is not in the list of valid screens,
        # then switch to the first valid screen
        if not self.ids.screen_manager.current_screen in valid_screens:
            self.ids.screen_manager.switch_to(valid_screens[0])

    def _switch_to_screen(self, screen):
        if self.ids.screen_manager.current_screen != screen:
            self.ids.screen_manager.switch_to(screen)

    def on_auto_detect(self, instance, value):
        track_cfg = self._track_cfg
        if track_cfg:
            track_cfg.autoDetect = value
            track_cfg.stale = True
            self.dispatch('on_modified')
            self.ids.auto_detect.help_text = 'Automatically detect and configure your favorite tracks' if value else 'Build and customize your own track map'
        self._select_screen()

    def _on_advanced_editor(self, *args):
        self._switch_to_screen(self._get_advanced_editor_screen())

    def _on_custom_editor(self, *args):
        self._switch_to_screen(self._get_custom_track_screen())
