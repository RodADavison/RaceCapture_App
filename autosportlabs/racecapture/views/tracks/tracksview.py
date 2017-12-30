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
from autosportlabs.racecapture.theme.color import ColorScheme
from kivy.uix.behaviors import ToggleButtonBehavior
kivy.require('1.10.0')
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.metrics import dp
from kivy.logger import Logger
from kivy.core.window import Window
import json
import sets
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.uix.track.trackmap import TrackMapView
from autosportlabs.uix.track.racetrackview import RaceTrackView
from utils import *
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from iconbutton import LabelIconButton
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.tracks.trackmanager import TrackManager, TrackMap
from autosportlabs.racecapture.config.rcpconfig import Track

class SearchInput(TextInput):

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_search')
        super(SearchInput, self).__init__(*args, **kwargs)

    def on_text_validate(self, *args):
        self.dispatch('on_search')

    def on_search(self, *args):
        pass

class TracksUpdateStatusView(BoxLayout):
    Builder.load_string("""
<TracksUpdateStatusView>:
    orientation: 'vertical'
    ProgressBar:
        id: progress
    Label:
        id: updatemsg    
    """)
    progressView = None
    messageView = None
    def __init__(self, **kwargs):
        super(TracksUpdateStatusView, self).__init__(**kwargs)
        self.progressView = self.ids.progress
        self.messageView = self.ids.updatemsg

    def _update_progress(self, percent):
        self.progressView.value = percent

    def _update_message(self, message):
        self.messageView.text = message

    def on_progress(self, count=None, total=None, message=None):
        if count and total:
            progress_percent = (float(count) / float(total) * 100)
            Clock.schedule_once(lambda dt: self._update_progress(progress_percent))
        if message:
            Clock.schedule_once(lambda dt: self._update_message(message))

    def on_message(self, message):
        self.messageView.text = message

class BaseTrackItemView(BoxLayout):
    def __init__(self, **kwargs):
        super(BaseTrackItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        self.ids.trackinfo.setTrack(track)
        self.track = track
        self.register_event_type('on_track_selected')

    def on_track_selected(self, selected, trackId):
        pass

class TrackItemView(BaseTrackItemView):
    Builder.load_string("""
<TrackItemView>:
    BoxLayout:
        orientation: 'horizontal'
        CheckBox:
            size_hint_x: 0.10
            on_active: root.track_select(*args)
            id: select
        TrackInfoView:
            id: trackinfo    
    """)
    def track_select(self, instance, value):
        self.dispatch('on_track_selected', value, self.track.track_id)

    def setSelected(self, selected):
        self.ids.active = selected

class SingleTrackItemView(ToggleButtonBehavior, BaseTrackItemView):
    Builder.load_string("""
<SingleTrackItemView>:
    group: 'track'
    TrackInfoView:
        canvas.before:
            Color:
                rgba: root.selected_color
            Rectangle:
                pos: self.pos
                size: self.size
        id: trackinfo    
    """)
    
    selected_color = ListProperty(ColorScheme.get_dark_background())

    def on_state(self, instance, value):
        selected = value == 'down'
        self.selected_color = ColorScheme.get_medium_background() if selected else ColorScheme.get_dark_background()
        self.dispatch('on_track_selected', selected, self.track.track_id)

class TrackInfoView(BoxLayout):
    Builder.load_string("""
<TrackInfoView>:
    orientation: 'vertical'
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: 0.1, 0.1, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size
    FieldLabel:
        halign: 'center'
        font_size: dp(20)
        size_hint_y: 0.1
        text: ''
        id: name
    BoxLayout:
        orientation: 'horizontal'
        BoxLayout:
            size_hint_x: 0.8
            padding: (dp(10), dp(10))
            spacing: dp(30)
            orientation: 'horizontal'
            RaceTrackView:
                id: track
                size_hint_x: 0.7
        BoxLayout:
            size_hint_x: 0.2
            orientation: 'vertical'
            BoxLayout:
                size_hint_y: 0.2
            AnchorLayout:
                anchor_x: 'center'
                size_hint_y: 0.4
                Image:
                    id: flag
                    allow_stretch: True
                    size_hint_x: None                   
            FieldLabel:
                id: length
                valign: 'top'
                halign: 'center'
                size_hint_y: 0.1                
            BoxLayout:
                size_hint_y: 0.3    
    """)
    track = None
    def __init__(self, **kwargs):
        super(TrackInfoView, self).__init__(**kwargs)

    def setTrack(self, track):
        if track is None:  # create a default, empty track if none provided
            track = TrackMap()

        raceTrackView = self.ids.track
        raceTrackView.loadTrack(track)

        name = track.name
        configuration = '' if len(track.configuration) == 0 else ' ({})'.format(track.configuration)
        self.ids.name.text = name + configuration

        self.ids.length.text = '' if track.length == 0 else '{} mi.'.format(track.length)

        flag_image = self.ids.flag
        cc = track.country_code
        if cc:
            cc = cc.lower()
            try:
                flagImagePath = 'resource/flags/' + str(track.country_code.lower()) + '.png'
                flag_image.source = flagImagePath
            except Exception as detail:
                Logger.warn('Error loading flag for country code: {}'.format(detail))
        else:
            flag_image.source = 'resource/flags/blank.png'
        self.track = track

class TracksBrowser(BoxLayout):
    Builder.load_string("""
<TracksBrowser>:
    orientation: 'vertical'
    spacing: dp(5)
    BoxLayout:
        height: dp(30)
        size_hint_y: None
        padding: (dp(20), dp(2))
        spacing: sp(10)
        orientation: 'horizontal'
        Label:
            size_hint_x: 0.1
            text: 'Search'
        SearchInput:
            size_hint_x: 0.50
            id: namefilter
            multiline: False
        IconButton:
            size_hint_x: 0.05
            id: search
            disabled: True
            text: u'\uf002'
            color: ColorScheme.get_accent()
            on_press: root.on_search_track_name()
        Label:
            size_hint_x: 0.15
            text: 'Region'
        Spinner:
            size_hint_x: 0.25
            id: regions
            on_text: root.on_region_selected(*args)
                        
    BoxLayout:
        size_hint_y: 0.84
        ScrollContainer:
            on_scroll_move: root.on_scroll(*args)
            id: scrltracks
            do_scroll_x:False
            do_scroll_y:True
            GridLayout:
                id: tracksgrid
                padding: [dp(20), dp(20)]
                spacing: [dp(10), dp(10)]
                size_hint_y: None
                cols: 1
            
    BoxLayout:
        height: dp(30)
        size_hint_y: None
        padding: (dp(20), dp(2))
        orientation: 'horizontal'
        Widget:
            size_hint_x: 0.56

        LabelIconButton:
            size_hint_x: None
            width: dp(120)
            id: updatecheck
            disabled: True
            title: 'Update'
            icon: '\357\203\255'
            on_press: root.on_update_check()                                
    """)
    INITIAL_DISPLAY_LIMIT = 10
    LAZY_DISPLAY_CHUNK_COUNT = 1
    LOOK_AHEAD_TRACKS = 10
    TRACK_HEIGHT_PADDING = dp(10)

    multi_select = BooleanProperty(True)
    trackHeight = NumericProperty(dp(200))
    current_location = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super(TracksBrowser, self).__init__(**kwargs)
        self.register_event_type('on_track_selected')
        self.current_location = kwargs.get('current_location')
        self.trackmap = None
        self.trackManager = None
        self.tracksUpdatePopup = None
        self.initialized = False
        self.tracksGrid = None
        self.tracks_loading = False
        self.last_scroll_y = 1.0
        self.selectedTrackIds = set()

    def on_track_selected(self, value):
        pass

    def on_scroll(self, instance, value):
        scroll_y = self.ids.scrltracks.scroll_y
        last_scroll_y = self.last_scroll_y
        self.last_scroll_y = scroll_y
        # only check to lazy load if we're scrolling towards the bottom
        if  scroll_y < last_scroll_y:
            self.lazy_load_more_maybe()

    def lazy_load_more_maybe(self):
        sb = self.ids.scrltracks
        current_index = self.load_limit
        tracks_count = len(self.current_track_ids)
        current_pct_loaded = 1.0 - (float(current_index - self.LOOK_AHEAD_TRACKS) / float(tracks_count))
        if sb.scroll_y < current_pct_loaded and current_index < tracks_count:
            if not self.tracks_loading:
                new_load_limit = current_index + self.LAZY_DISPLAY_CHUNK_COUNT
                if new_load_limit > tracks_count:
                    new_load_limit = tracks_count
                self.load_limit = new_load_limit
                self.tracks_loading = True
                self.addNextTrack(current_index, self.current_track_ids)
            Clock.schedule_once(lambda dt: self.lazy_load_more_maybe(), 1.0)

    def set_trackmanager(self, track_manager):
        self.trackManager = track_manager

    def init_view(self):
        self.initRegionsList()
        self.refreshTrackList()
        self.ids.namefilter.bind(on_search=self.on_search_track_name)
        self.initialized = True

    def setViewDisabled(self, disabled):
        self.ids.updatecheck.disabled = disabled
        self.ids.regions.disabled = disabled
        self.ids.namefilter.disabled = disabled
        self.ids.search.disabled = disabled
        if disabled == False and is_mobile_platform() == False:
            self.ids.namefilter.focus = True

    def dismissPopups(self):
        if self.tracksUpdatePopup:
            self.tracksUpdatePopup.dismiss()

    def loadAll(self, dt):
        self.initTracksList(self.trackManager.get_track_ids_in_region())

    def on_search_track_name(self, *args):
        if self.initialized:
            Clock.schedule_once(lambda dt: self.refreshTrackList())

    def on_region_selected(self, instance, search):
        if self.initialized:
            Clock.schedule_once(lambda dt: self.refreshTrackList())

    def showProgressPopup(self, title, content):
        self.dismissPopups()
        if type(content) is str:
            content = Label(text=content)
        popup = Popup(title=title, content=content, auto_dismiss=False, size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()
        self.tracksUpdatePopup = popup

    def on_update_check_success(self):
        def success():
            # do this in the UI thread
            self.tracksUpdatePopup.content.on_message('Processing...')
            Clock.schedule_once(lambda dt: self.refreshTrackList())
        Clock.schedule_once(lambda dt: success())


    def on_update_check_error(self, details):
        def error(details):
            self.dismissPopups()
            Clock.schedule_once(lambda dt: self.refreshTrackList())
            Logger.error('TracksBrowser: Error updating: {}'.format(details))
            alertPopup('Error Updating', 'There was an error updating the track list.\n\nPlease check your network connection and try again')
        Clock.schedule_once(lambda dt: error(details))

    def on_update_check(self):
        self.setViewDisabled(True)
        tracksUpdateView = TracksUpdateStatusView()
        self.showProgressPopup('Checking for updates', tracksUpdateView)
        self.trackManager.refresh(tracksUpdateView.on_progress, self.on_update_check_success, self.on_update_check_error)

    def addNextTrack(self, index, keys):
        if index < self.load_limit:
            track = self.trackManager.tracks[keys[index]]

            trackView = TrackItemView(track=track) if self.multi_select == True else SingleTrackItemView(track=track)
            trackView.bind(on_track_selected=self.track_selected)
            trackView.size_hint_y = None
            trackView.height = self.trackHeight
            self.tracksGrid.add_widget(trackView)
            Clock.schedule_once(lambda dt: self.addNextTrack(index + 1, keys), 0.1)
        else:
            self.dismissPopups()
            self.setViewDisabled(False)
            self.last_scroll_y = self.ids.scrltracks.scroll_y
            self.tracks_loading = False

    def refreshTrackList(self):
        region = self.ids.regions.text
        if region == 'Nearby':
            found_ids = [t.track_id for t in self._get_nearby_tracks()]
        else:
            found_ids = self.trackManager.filter_tracks_by_region(region)
        search = self.ids.namefilter.text
        if search != None and len(search) > 0:
            found_ids = self.trackManager.filter_tracks_by_name(search, found_ids)
        self.initTracksList(found_ids)

    def initTracksList(self, track_ids=None):
        self.setViewDisabled(True)
        if track_ids is None:
            track_ids = self.trackManager.track_ids
        track_count = len(track_ids)
        grid = self.ids.tracksgrid
        grid.clear_widgets()
        self.tracksGrid = grid
        self.ids.tracksgrid.height = ((track_count) * (self.trackHeight + self.TRACK_HEIGHT_PADDING))
        self.ids.scrltracks.height = 0
        self.ids.scrltracks.scroll_y = 1.0
        self.last_scroll_y = 1.0
        self.loading = False

        self.dismissPopups()
        if track_count == 0:
            Logger.info("TracksViews: no tracks")
            self.tracksGrid.add_widget(Label(text="No tracks found - try checking for updates"))
            self.setViewDisabled(False)
            self.ids.namefilter.focus = True
        else:
            self.load_limit = self.INITIAL_DISPLAY_LIMIT if len(track_ids) > self.INITIAL_DISPLAY_LIMIT else len(track_ids)
            self.current_track_ids = track_ids
            self.addNextTrack(0, track_ids)
            self.tracks_loading = True

    def _get_nearby_tracks(self):
        if self.current_location is not None:
            return self.trackManager.find_nearby_tracks(self.current_location)
        else:
            return []

    def initRegionsList(self):
        regions = self.trackManager.regions
        regions_spinner = self.ids.regions
        values = []
        # if we're specifying our current location, then the first option is to
        # show nearby tracks
        if len(self._get_nearby_tracks()) > 0:
            values.append('Nearby')

        for region in regions:
            name = region.name
            if regions_spinner.text == '':
                regions_spinner.text = name
            values.append(name)

        regions_spinner.values = values
        regions_spinner.text = values[0]

    def track_selected(self, instance, selected, trackId):
        if selected:
            self.selectedTrackIds.add(trackId)
        else:
            self.selectedTrackIds.discard(trackId)
        self.dispatch('on_track_selected', self.selectedTrackIds)

class TrackSelectView(StackLayout):

    Builder.load_string("""
<TrackSelectView>:
    TracksBrowser:
        id: track_browser
""")

    def __init__(self, **kwargs):
        super(TrackSelectView, self).__init__(**kwargs)
        current_location = kwargs.get('current_location')
        track_manager = kwargs.get('track_manager')
        self.selected_track = None
        self.register_event_type('on_track_selected')
        self.init_view(track_manager, current_location)

    def init_view(self, track_manager, current_location):
        if track_manager is None:
            # can't init if we don't have track_manager
            # presumably it will happen later
            return
        self.ids.track_browser.multi_select = False
        self.ids.track_browser.bind(on_track_selected=self.track_selected)
        self.ids.track_browser.set_trackmanager(track_manager)
        self._track_manager = track_manager
        self.ids.track_browser.current_location = current_location
        self.ids.track_browser.init_view()

    def on_track_selected(self, track):
        pass

    def track_selected(self, instance, tracks):
        if len(tracks) > 0:
            # Tracks are a set, we only want 1 but we don't want to modify the original
            tracks_copy = tracks.copy()
            track_id = tracks_copy.pop()
            track = self._track_manager.get_track_by_id(track_id)
            self.selected_track = track
            self.dispatch('on_track_selected', track)
        else:
            self.selected_track = None

class EmptyTrackDbView(BoxLayout):
    Builder.load_string("""
<EmptyTrackDbView>:
    BoxLayout:
        orientation: 'vertical'
        pos_hint: {'center_x': .5, 'center_y': .5}
        Widget:
            size_hint_y: 0.5
        FieldLabel:
            font_size: dp(25)
            text: 'No tracks selected'
            halign: 'center'
            size_hint_y: 0.1
        Widget:
            size_hint_y: 0.3
        FieldLabel:
            text: 'Press (+) to select your favorite tracks'
            color: ColorScheme.get_dark_primary_text()
            font_size: dp(25)
            halign: 'center'
            size_hint_y: 0.1
    """)
    def __init__(self, **kwargs):
        super(EmptyTrackDbView, self).__init__(**kwargs)

class TrackSelectionPopup(BoxLayout):
    Builder.load_string("""
<TrackSelectionPopup>:
    orientation: 'vertical'
    TracksBrowser:
        trackHeight: dp(200)
        id: browser
        size_hint_y: 0.90
    BoxLayout:
        size_hint_y: 0.1
        orientation: 'horizontal'
        IconButton:
            text: '\357\200\214'
            color: ColorScheme.get_accent()
            on_release: root.confirm_add_tracks()    
    """)
    def __init__(self, **kwargs):
        super(TrackSelectionPopup, self).__init__(**kwargs)
        self.register_event_type('on_tracks_selected')
        track_manager = kwargs.get('track_manager', None)
        track_browser = self.ids.browser
        track_browser.set_trackmanager(track_manager)
        track_browser.init_view()
        self.track_browser = track_browser

    def on_tracks_selected(self, selectedTrackIds):
        pass

    def confirm_add_tracks(self):
        self.dispatch('on_tracks_selected', self.track_browser.selectedTrackIds)

TRACK_DB_ITEM_VIEW_KV = """
<TrackDbItemView>:
    BoxLayout:
        orientation: 'horizontal'
        TrackInfoView:
            size_hint_x: 0.92
            id: trackinfo
        AnchorLayout:
            size_hint_x: 0.08
            IconButton:
                size_hint: (0.5, 0.15)
                text: '\357\200\224'
                on_release: root.remove_track()
"""

class TrackDbItemView(BoxLayout):
    Builder.load_string(TRACK_DB_ITEM_VIEW_KV)
    def __init__(self, **kwargs):
        super(TrackDbItemView, self).__init__(**kwargs)
        track = kwargs.get('track', None)
        self.index = kwargs.get('index', 0)
        self.ids.trackinfo.setTrack(track)
        self.track = track
        self.register_event_type('on_remove_track')

    def on_remove_track(self, index):
        pass

    def remove_track(self):
        self.dispatch('on_remove_track', self.index)

class TrackCollectionScreen(AnchorLayout):
    Builder.load_string("""
<TrackCollectionScreen>:
    AnchorLayout:
        spacing: dp(10)
        ScrollContainer:
            canvas.before:
                Color:
                    rgba: 0.05, 0.05, 0.05, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            size_hint_y: 0.95
            id: scrltracks
            do_scroll_x:False
            do_scroll_y:True
            GridLayout:
                id: tracksgrid
                padding: [dp(10), dp(10)]
                spacing: [dp(10), dp(10)]
                size_hint_y: None
                cols: 1
    AnchorLayout:
        anchor_y: 'bottom'
        IconButton:
            color: ColorScheme.get_accent()
            size_hint: (None, None)
            height: root.height * .15
            text: u'\uf055'
            on_release: root.on_add_track_db()
            disabled: True
            id: addtrack    
    """)
    track_manager = ObjectProperty(None)
    TRACK_ITEM_MIN_HEIGHT = 200

    def __init__(self, **kwargs):
        super(TrackCollectionScreen, self).__init__(**kwargs)
        self.track_db = None
        self.register_event_type('on_modified')

    def on_modified(self, *args):
        pass

    def on_config_updated(self, track_db):
        self.track_db = track_db
        self.init_tracks_list()

    def on_track_manager(self, instance, value):
        self.track_manager = value
        self.init_tracks_list()

    def on_add_track_db(self):

        def on_tracks_selected(instance, selected_track_ids):
            if self.track_db:
                failures = False
                for trackId in selected_track_ids:
                    trackMap = self.track_manager.get_track_by_id(trackId)
                    if trackMap:
                        startFinish = trackMap.start_finish_point
                        if startFinish and startFinish.latitude and startFinish.longitude:
                            Logger.info("TrackConfigView:  adding track " + str(trackMap))
                            track = Track.fromTrackMap(trackMap)
                            self.track_db.tracks.append(track)
                        else:
                            failures = True
                if failures:
                    alertPopup('Cannot Add Tracks', 'One or more tracks could not be added due to missing start/finish points.\n\nPlease check for track map updates and try again.')
                self.init_tracks_list()
                popup.dismiss()
                self.track_db.stale = True
                self.dispatch('on_modified')

        content = TrackSelectionPopup(track_manager=self.track_manager)
        popup = Popup(title='Add Race Tracks', content=content, size_hint=(0.9, 0.9))
        content.bind(on_tracks_selected=on_tracks_selected)
        popup.open()

    def init_tracks_list(self):
        if self.track_manager and self.track_db:
            matched_tracks = []
            for track in self.track_db.tracks:
                matched_track = self.track_manager.find_track_by_short_id(track.trackId)
                if matched_track:
                    matched_tracks.append(matched_track)

            grid = self.ids.tracksgrid
            grid.clear_widgets()
            if len(matched_tracks) == 0:
                grid.add_widget(EmptyTrackDbView())
                grid.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
            else:
                grid.height = dp(self.TRACK_ITEM_MIN_HEIGHT) * (len(matched_tracks) + 1)
                index = 0
                for track in matched_tracks:
                    track_db_view = TrackDbItemView(track=track, index=index)
                    track_db_view.bind(on_remove_track=self.on_remove_track)
                    track_db_view.size_hint_y = None
                    track_db_view.height = dp(self.TRACK_ITEM_MIN_HEIGHT)
                    grid.add_widget(track_db_view)
                    index += 1

            self.disableView(False)

    def on_remove_track(self, instance, index):
            try:
                del self.track_db.tracks[index]
                self.init_tracks_list()
                self.track_db.stale = True
                self.dispatch('on_modified')

            except Exception as detail:
                Logger.error('AutomaticTrackConfigScreen: Error removing track from list ' + str(detail))

    def disableView(self, disabled):
        self.ids.addtrack.disabled = disabled

