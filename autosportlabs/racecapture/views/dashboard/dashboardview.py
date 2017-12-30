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
import time
import datetime
import kivy
kivy.require('1.10.0')
from kivy.app import Builder
from kivy.core.window import Window, Keyboard
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from utils import kvFindClass
from kivy.uix.carousel import Carousel
from kivy.uix.settings import SettingsWithNoMenu
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.image import Image
from autosportlabs.racecapture.views.dashboard.widgets.digitalgauge import DigitalGauge
from autosportlabs.racecapture.views.dashboard.widgets.stopwatch import PitstopTimerView
from autosportlabs.racecapture.settings.systemsettings import SettingsListener
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
from autosportlabs.racecapture.views.configuration.rcp.track.trackbuilder import TrackBuilderView
from autosportlabs.racecapture.views.util.alertview import editor_popup
from autosportlabs.racecapture.config.rcpconfig import Track, TrackConfig, Capabilities, GpsConfig, GpsSample
from autosportlabs.racecapture.tracks.trackmanager import TrackMap, TrackManager

# Dashboard screens
from autosportlabs.racecapture.views.dashboard.gaugeview import *
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView
from autosportlabs.racecapture.views.dashboard.tractionview import TractionView
from autosportlabs.racecapture.views.dashboard.heatmapview import HeatmapView


from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.help.helpmanager import HelpInfo
from garden_androidtabs import AndroidTabsBase, AndroidTabs
from autosportlabs.racecapture.theme.color import ColorScheme
from fieldlabel import FieldLabel
from collections import OrderedDict
from copy import copy

# Dashboard screens
from autosportlabs.racecapture.views.dashboard.gaugeview import GaugeView2x, GaugeView3x, GaugeView5x, GaugeView8x
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView



class DashboardFactory(object):
    """
    Factory for creating dashboard screens. 
    Screens are instances of DashboardScreen
    Screens are referenced and managed by their key name. 
    """
    def __init__(self, databus, settings, track_manager, status_pump, **kwargs):
        self._view_builders = OrderedDict()
        self._view_previews = OrderedDict()
        self._databus = databus
        self._settings = settings
        self._track_manager = track_manager
        self._status_pump = status_pump
        self._init_factory()

    def create_screen(self, key):
        """
        Create a new dashboard screen instance by key
        :param key the key of the screen
        :type key String
        :return a new instance of a dashboard screen
        """
        view = self._view_builders[key]()
        return view

    def _add_screen(self, key, builder, title, preview_image):
        self._view_builders[key] = builder
        image_source = os.path.join(self._settings.base_dir, 'resource', 'dashboard', preview_image)
        self._view_previews[key] = (title, image_source)

    def _init_factory(self):
        self._add_screen('2x_gauge_view', self.build_2x_gauge_view, '2x Gauges', '2x_gauge_view.png')
        self._add_screen('3x_gauge_view', self.build_3x_gauge_view, '3x Gauges', '3x_gauge_view.png')
        self._add_screen('5x_gauge_view', self.build_5x_gauge_view, '5x Gauges', '5x_gauge_view.png')
        self._add_screen('8x_gauge_view', self.build_8x_gauge_view, '8x Gauges', '8x_gauge_view.png')
        self._add_screen('laptime_view', self.build_laptime_view, 'Predictive Timer', 'laptime_view.png')
        self._add_screen('tach_view', self.build_tachometer_view, 'Tachometer', 'tachometer_view.png')
        self._add_screen('rawchannel_view', self.build_raw_channel_view, 'Raw Channels', 'raw_channel_view.png')
        self._add_screen('traction_view', self.build_traction_view, 'Traction', 'traction_view.png')
        self._add_screen('heatmap_view', self.build_heatmap_view, 'Heatmap', 'heatmap_view.png')

    @property
    def available_dashboards(self):
        """
        Provide a list of available dashboards by key
        :return String
        """
        return self._view_builders.keys()

    def get_dashboard_preview_image_path(self, key):
        """
        Get the preview image source path for the specified dashboard key
        :param key the key of the dashboard
        :param key String
        :return String path to the preview image, or None if the preview is not found
        """
        return self._view_previews.get(key)

    def build_5x_gauge_view(self):
        return GaugeView5x(name='5x_gauge_view', databus=self._databus, settings=self._settings)

    def build_3x_gauge_view(self):
        return GaugeView3x(name='3x_gauge_view', databus=self._databus, settings=self._settings)

    def build_2x_gauge_view(self):
        return GaugeView2x(name='2x_gauge_view', databus=self._databus, settings=self._settings)

    def build_8x_gauge_view(self):
        return GaugeView8x(name='8x_gauge_view', databus=self._databus, settings=self._settings)

    def build_tachometer_view(self):
        return TachometerView(name='tach_view', databus=self._databus, settings=self._settings)

    def build_laptime_view(self):
        return LaptimeView(name='laptime_view', databus=self._databus, settings=self._settings)

    def build_raw_channel_view(self):
        return RawChannelView(name='rawchannel_view', databus=self._databus, settings=self._settings)

    def build_traction_view(self):
        return TractionView(name='traction_view', databus=self._databus, settings=self._settings)

    def build_heatmap_view(self):
        return HeatmapView(name='heatmap_view', databus=self._databus,
                           settings=self._settings,
                           track_manager=self._track_manager,
                           status_pump=self._status_pump)


DASHBOARD_VIEW_KV = """
<DashboardView>:
    AnchorLayout:
        FieldLabel:
            id: dash_notice
            halign: 'center'
            font_size: self.height * 0.05
        BoxLayout:
            orientation: 'vertical'
            Carousel:
                id: carousel
                on_current_slide: root.on_current_slide(args[1])                
                size_hint_y: 0.90
                loop: True
            BoxLayout:
                size_hint_y: 0.10
                orientation: 'horizontal'
                IconButton:
                    color: [1.0, 1.0, 1.0, 1.0]
                    font_size: self.height * 1.2
                    text: ' \357\203\231'
                    size_hint_x: 0.4
                    size_hint_y: 1.1
                    on_release: root.on_nav_left()
                DigitalGauge:
                    rcid: 'left_bottom'
                DigitalGauge:
                    rcid: 'center_bottom'
                DigitalGauge:
                    rcid: 'right_bottom'
                IconButton:
                    color: [1.0, 1.0, 1.0, 1.0]
                    font_size: self.height * 1.2
                    text: '\357\203\232 '
                    size_hint_x: 0.4
                    size_hint_y: 1.1
                    on_release: root.on_nav_right()
        AnchorLayout:
            anchor_x: 'left'
            anchor_y: 'top'
            IconButton:
                id: preferences_button
                size_hint_y: 0.1
                size_hint_x: 0.1
                text: u'\uf013'
                halign: 'left'
                color: [1.0, 1.0, 1.0, 0.2]
                on_press: root.on_preferences()
"""

class DashboardView(Screen):
    """
    The main dashboard view.
    Provides the framework for adding and managing various dashboard screens.
    """
    _POPUP_SIZE_HINT = (0.75, 0.9)
    _POPUP_DISMISS_TIMEOUT_LONG = 60.0
    AUTO_CONFIGURE_WAIT_PERIOD_DAYS = 1
    Builder.load_string(DASHBOARD_VIEW_KV)

    def __init__(self, status_pump, track_manager, rc_api, rc_config, databus, settings, **kwargs):
        self._initialized = False
        super(DashboardView, self).__init__(**kwargs)
        self._dashboard_factory = DashboardFactory(databus, settings, track_manager, status_pump)
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_config_updated')
        self.register_event_type('on_config_written')
        self._screens = []
        self._loaded_screens = {}
        self._status_pump = status_pump
        self._databus = databus
        self._settings = settings
        self._track_manager = track_manager
        self._rc_api = rc_api
        self._rc_config = rc_config
        self._alert_widgets = {}
        self._dismiss_popup_trigger = Clock.create_trigger(self._dismiss_popup, DashboardView._POPUP_DISMISS_TIMEOUT_LONG)
        self._popup = None
        self._track_config = None
        self._gps_sample = GpsSample()
        status_pump.add_listener(self.status_updated)

    def status_updated(self, status):
        """
        Process a status update
        """
        status = status['status']['GPS']
        quality = status['qual']
        latitude = status['lat']
        longitude = status['lon']
        current_gps_qual = self._gps_sample.gps_qual
        self._gps_sample.gps_qual = quality
        self._gps_sample.latitude = latitude
        self._gps_sample.longitude = longitude

        if quality > GpsConfig.GPS_QUALITY_NO_FIX and current_gps_qual <= GpsConfig.GPS_QUALITY_NO_FIX:
            # We have transition to having valid GPS
            self._race_setup()

    def on_tracks_updated(self, trackmanager):
        pass

    def on_config_updated(self, rc_config):
        self._rc_config = rc_config
        self._race_setup()

    def on_config_written(self, rc_config):
        self._rc_config = rc_config
        self._race_setup()

    def _init_global_gauges(self):
        databus = self._databus
        settings = self._settings

        activeGauges = list(kvFindClass(self, Gauge))

        for gauge in activeGauges:
            gauge.settings = settings
            gauge.data_bus = databus

    def _init_view(self):
        databus = self._databus
        settings = self._settings

        self._init_global_gauges()

        # add the initial set of empty screens
        screens = self._screens
        screens += self._filter_dashboard_screens(self._settings.userPrefs.get_dashboard_screens())
        for i in range (0, len(screens)):
            self.ids.carousel.add_widget(AnchorLayout())

        # Find all of the global and set the objects they need
        gauges = list(kvFindClass(self, DigitalGauge))
        for gauge in gauges:
            gauge.settings = settings
            gauge.data_bus = databus

        # Initialize our alert type widgets
        self._alert_widgets['pit_stop'] = PitstopTimerView(databus, 'Pit Stop')

        self._notify_preference_listeners()
        self._show_last_view()

        if self._rc_api.connected:
            self._race_setup()

        self._rc_api.add_connect_listener(self._on_rc_connect)
        self._initialized = True

        Clock.schedule_once(lambda dt: HelpInfo.help_popup('dashboard_gauge_help', self, arrow_pos='right_mid'), 2.0)

    def _update_screens(self, new_screens):
        """
        Remove and re-adds screens to match the new configuration
        """

        # Prevent events from triggering and interfering with this update process
        self._initialized = False
        carousel = self.ids.carousel
        current_screens = self._screens
        loaded_screens = self._loaded_screens

        new_screen_count = len(new_screens)
        current_screen_count = len(current_screens)
        original_screen_count = current_screen_count

        # Note, our lazy loading scheme has the actual dashboard
        # screens as part of the outer screen containers
        # screen containers - placeholders.

        # clear all of the dashboard screens from the outer container
        for screen in loaded_screens.values():
            parent = screen.parent
            if parent is not None:
                parent.remove_widget(screen)

        # add more carousel panes as needed
        while True:
            if current_screen_count == new_screen_count:
                break
            if current_screen_count < new_screen_count:
                carousel.add_widget(AnchorLayout())
                current_screen_count += 1
            if current_screen_count > new_screen_count:
                carousel.remove_widget(carousel.slides[0])
                current_screen_count -= 1

        # Now re-add the screens for the new screen keys
        for (screen_key, container) in zip(new_screens, carousel.slides):
            screen = loaded_screens.get(screen_key)
            if screen is not None:
                container.add_widget(screen)

        self._screens = new_screens

        if original_screen_count == 0 and new_screen_count > original_screen_count:
            carousel.index = 0

        self._check_load_screen(carousel.current_slide)

        self._initialized = True

    def _on_rc_connect(self, *args):
        Clock.schedule_once(lambda dt: self._race_setup())

    def _race_setup(self):
        """
        Logic tree for setting up a race event, including track map selection and
        automatic configuration
        """
        # skip if this screen is not active
        if self.manager is not None and self.manager.current_screen != self:
            return

        # skip if we're not connected
        if not self._rc_api.connected:
            return

        # skip if GPS data is not good
        if self._gps_sample.gps_qual <= GpsConfig.GPS_QUALITY_NO_FIX:
            return

        track_cfg = self._rc_config.trackConfig
        auto_detect = track_cfg.autoDetect

        # skip if we haven't enabled auto detection
        if not auto_detect:
            return

        # what track is currently configured?
        current_track = TrackMap.from_track_cfg(track_cfg.track)

        # is the currently configured track in the list of nearby tracks?
        # if so, just keep this one
        tracks = self._track_manager.find_nearby_tracks(self._gps_sample.geopoint)

        prefs = self._settings.userPrefs
        last_track_set_time = datetime.datetime.fromtimestamp(prefs.get_last_selected_track_timestamp())
        track_set_a_while_ago = datetime.datetime.now() > last_track_set_time + datetime.timedelta(days=DashboardView.AUTO_CONFIGURE_WAIT_PERIOD_DAYS)

        # is the currently configured track in the area?
        current_track_is_nearby = current_track.short_id in (t.short_id for t in tracks)

        # no need to re-detect a nearby track that was recently set
        if current_track_is_nearby and not track_set_a_while_ago:
            Logger.info('DashboardView: Nearby track was recently set, skipping auto configuration')
            return

        # we found only one track nearby, so select it and be done.
        if len(tracks) == 1:
            new_track = tracks[0]
            Logger.info('DashboardView: auto selecting track {}({})'.format(new_track.name, new_track.short_id))
            track_cfg.track.import_trackmap(new_track)
            self._set_rc_track(track_cfg)
            return

        # ok. To prevent repeatedly pestering the user about asking to configure a track
        # check if the user last cancelled near the same location
        last_cancelled_location = GeoPoint.from_string(prefs.get_user_cancelled_location())
        radius = last_cancelled_location.metersToDegrees(TrackManager.TRACK_DEFAULT_SEARCH_RADIUS_METERS,
                                                         TrackManager.TRACK_DEFAULT_SEARCH_BEARING_DEGREES)
        if last_cancelled_location.withinCircle(self._gps_sample.geopoint, radius):
            Logger.info("DashboardView: Still near the same location where the user last cancelled track configuration. Not pestering again")
            return

        # if we made it this far, we're going to ask the user to help select or create a track
        Clock.schedule_once(lambda dt: self._load_track_setup_view(track_cfg))

    def _load_track_setup_view(self, track_cfg):
        """
        Present the user with the track setup view
        """

        def cancelled_track():
            # user cancelled, store current location as where they cancelled
            # so we prevent bugging the user again
            self._settings.userPrefs.set_last_selected_track(0, 0, str(self._gps_sample.geopoint))
            HelpInfo.help_popup('lap_setup', self)

        def on_track_complete(instance, track_map):
            if track_map is None:
                cancelled_track()
            else:
                Logger.debug("DashboardView: setting track_map: {}".format(track_map))
                self._track_manager.add_track(track_map)
                track_cfg.track.import_trackmap(track_map)
                track_cfg.stale = True
                self._set_rc_track(track_cfg)

            if self._popup:
                self._popup.dismiss()
            self._popup = None

        def on_close(instance, answer):
            if not answer:
                cancelled_track()

            if self._popup:
                self._popup.dismiss()
            self._popup = None

        if self._popup is not None:
            # can't open dialog multiple times
            return

        content = TrackBuilderView(self._rc_api, self._databus, self._track_manager, current_point=self._gps_sample.geopoint, prompt_track_creation=True)
        self._popup = editor_popup("Race track setup", content, on_close, hide_ok=True, size_hint=(0.9, 0.9))
        content.bind(on_track_complete=on_track_complete)
        self._popup.open()

    def _set_rc_track(self, track_cfg):
        self._rc_api.setTrackCfg(track_cfg.toJson())
        self._rc_api.sendFlashConfig()
        self._settings.userPrefs.set_last_selected_track(track_cfg.track.trackId, int(time.mktime(datetime.datetime.now().timetuple())))

    def on_enter(self):
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_key_down=self.on_key_down)
        if not self._initialized:
            self._init_view()

    def on_leave(self):
        Window.unbind(mouse_pos=self.on_mouse_pos)
        Window.unbind(on_key_down=self.on_key_down)

    def _got_activity(self):
        self.ids.preferences_button.brighten()

    def on_touch_down(self, touch):
        self._got_activity()
        return super(DashboardView, self).on_touch_down(touch)

    def on_mouse_pos(self, x, pos):
        if self.collide_point(pos[0], pos[1]):
            self._got_activity()
            self.ids.preferences_button.brighten()
        return False

    def on_key_down(self, window, key, *args):
        if key == Keyboard.keycodes['left']:
            self.on_nav_left()
        elif key == Keyboard.keycodes['right']:
            self.on_nav_right()
        return False

    def _filter_dashboard_screens(self, screens):
        """
        Filter the supplied list of screens against the actual list of available screens, including normalizing for order
        """
        all_screens = self._dashboard_factory.available_dashboards
        # re-order selected screens based on native order
        return [x for x in all_screens if x in screens]

    def on_preferences(self, *args):
        """
        Display the dashboard preferences view 
        """
        settings_view = DashboardPreferences(self._settings, self._dashboard_factory)

        def popup_dismissed(*args):
            self._notify_preference_listeners()
            screens = settings_view.get_selected_screens()
            screens = self._filter_dashboard_screens(screens)
            self._settings.userPrefs.set_dashboard_screens(screens)
            self._update_screens(screens)

        popup = ModalView(size_hint=DashboardView._POPUP_SIZE_HINT)
        popup.add_widget(settings_view)
        popup.bind(on_dismiss=popup_dismissed)
        popup.open()


    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None

    def _notify_preference_listeners(self):
        listeners = list(kvFindClass(self, SettingsListener)) + self._alert_widgets.values()
        for listener in listeners:
            listener.user_preferences_updated(self._settings.userPrefs)

    def _exit_screen(self):
        slide_screen = self.ids.carousel.current_slide
        if (slide_screen.children) > 0:
            slide_screen.children[0].on_exit()

    def on_nav_left(self):
        self._exit_screen()
        self.ids.carousel.load_previous()

    def on_nav_right(self):
        self._exit_screen()
        self.ids.carousel.load_next()

    def _check_load_screen(self, slide_screen):
        # checks the current slide if we need to build the dashboard
        # screen on the spot

        self.ids.dash_notice.text = '' if len(self.ids.carousel.slides) > 0 else 'No dashboard screens selected'

        if slide_screen is None:
            return

        if len(slide_screen.children) == 0:
            # if the current screen has no children build and add the screen
            index = self.ids.carousel.index
            # call the builder to actually build the screen
            screen_key = self._screens[index]
            # was this screen created before?
            view = self._loaded_screens.get(screen_key)
            if view is None:
                view = self._dashboard_factory.create_screen(screen_key)
            slide_screen.add_widget(view)
            self._loaded_screens[screen_key] = view
            view.on_enter()

    def on_current_slide(self, slide_screen):
        if self._initialized == True:
            self._check_load_screen(slide_screen)
            view = slide_screen.children[0]
            self._settings.userPrefs.set_pref('dashboard_preferences', 'last_dash_screen', view.name)

    def _show_screen(self, screen_name):
        # Find the index of the screen based on the screen name
        # and use that to select the index of the carousel
        carousel = self.ids.carousel
        screens = self._screens
        carousel.index = 0 if screen_name not in screens else self._screens.index(screen_name)
        self._check_load_screen(carousel.current_slide)

    def _show_last_view(self):
        """
        Select the last configured screen
        """
        last_screen_name = self._settings.userPrefs.get_pref('dashboard_preferences', 'last_dash_screen')
        Clock.schedule_once(lambda dt: self._show_screen(last_screen_name))

DASHBOARD_PREFERENCES_SCREEN_KV = """
<DashboardPreferenceScreen>:
    tab_font_name: "resource/fonts/ASL_light.ttf"
    tab_font_size: sp(20)
"""

class DashboardPreferenceScreen(AnchorLayout, AndroidTabsBase):
    """
    Wrapper class to allow customization and styling
    """
    Builder.load_string(DASHBOARD_PREFERENCES_SCREEN_KV)
    tab_font_name = StringProperty()
    tab_font_size = NumericProperty()

    def on_tab_font_name(self, instance, value):
        self.tab_label.font_name = value

    def on_tab_font_size(self, instance, value):
        self.tab_label.font_size = value

DASHBOARD_SCREEN_ITEM_KV = """
<DashboardScreenItem>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_widget_translucent_background()
        Rectangle:
            pos: self.pos
            size: self.size
    padding: (dp(5), dp(5))
"""
class DashboardScreenItem(BoxLayout):
    """
    Contains the line-item for a dashboard screen 
    """
    Builder.load_string(DASHBOARD_SCREEN_ITEM_KV)

DASHBOARD_SCREEN_PREFERENCES_KV = """
<DashboardScreenPreferences>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background()
        Rectangle:
            pos: self.pos
            size: self.size
    text: 'Screens'
    
    ScrollContainer:
        id: scroll
        size_hint_y: 1.0
        do_scroll_x:False
        do_scroll_y:True
        GridLayout:
            id: grid
            padding: (dp(10), dp(10))
            spacing: dp(10)
            row_default_height: root.height * 0.3
            size_hint_y: None
            height: self.minimum_height
            cols: 1        
"""
class DashboardScreenPreferences(DashboardPreferenceScreen):
    """
    Provides the interface for selecting screens to enable
    """
    Builder.load_string(DASHBOARD_SCREEN_PREFERENCES_KV)

    def __init__(self, settings, dashboard_factory, **kwargs):
        super(DashboardScreenPreferences, self).__init__(**kwargs)
        self._settings = settings

        current_screens = self._settings.userPrefs.get_dashboard_screens()
        screen_keys = dashboard_factory.available_dashboards
        for key in screen_keys:
            [name, image] = dashboard_factory.get_dashboard_preview_image_path(key)
            checkbox = CheckBox()
            checkbox.active = True if key in current_screens else False
            checkbox.bind(active=lambda i, v, k=key:self._screen_selected(k, v))
            screen_item = DashboardScreenItem()
            screen_item.add_widget(checkbox)
            screen_item.add_widget(FieldLabel(text=name))
            screen_item.add_widget(Image(source=image))
            self.ids.grid.add_widget(screen_item)
        self._current_screens = current_screens

    def _screen_selected(self, key, selected):
        screens = self._current_screens
        if key in screens and not selected:
            screens.remove(key)
        if key not in screens and selected:
            screens.append(key)

    @property
    def selected_screens(self):
        return self._current_screens

DASHBOARD_MAIN_PREFERENCES_KV = """
<DashboardMainPreferences>:
    text: 'Behavior'
    SettingsWithNoMenu:
        id: settings
"""
class DashboardMainPreferences(DashboardPreferenceScreen):
    """
    Provides the interface for the main behavioral preferences for the dashboard
    """
    Builder.load_string(DASHBOARD_MAIN_PREFERENCES_KV)

    def __init__(self, settings, **kwargs):
        super(DashboardMainPreferences, self).__init__(**kwargs)
        self.ids.settings.add_json_panel('Dashboard', settings.userPrefs.config, os.path.join(settings.base_dir, 'resource', 'settings', 'dashboard_settings.json'))

DASHBOARD_PREFERENCES_KV = """
<DashboardPreferences>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_accent()
        Rectangle:
            pos: self.pos
            size: self.size
    AndroidTabs:
        tab_indicator_color: ColorScheme.get_light_primary()
        id: tabs
"""
class DashboardPreferences(AnchorLayout):
    """
    Main container for the Dashboard preferences screen
    """
    Builder.load_string(DASHBOARD_PREFERENCES_KV)

    def __init__(self, settings, dashboard_factory, **kwargs):
        super(DashboardPreferences, self).__init__(**kwargs)
        main_prefs = DashboardMainPreferences(settings)
        self.ids.tabs.add_widget(main_prefs)

        screen_prefs = DashboardScreenPreferences(settings, dashboard_factory)
        self.ids.tabs.add_widget(screen_prefs)
        self._screen_prefs = screen_prefs

    def get_selected_screens(self):
        return self._screen_prefs.selected_screens
