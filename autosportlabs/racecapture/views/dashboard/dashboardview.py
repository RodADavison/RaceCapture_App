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
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, ListProperty, BooleanProperty
from utils import kvFindClass
from kivy.animation import Animation
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
from autosportlabs.racecapture.views.dashboard.racestatus_view import RaceStatusView


from autosportlabs.telemetry.telemetryconnection import TelemetryManager
from autosportlabs.racecapture.alerts.alertengine import AlertEngine
from autosportlabs.racecapture.alerts.alertactions import PopupAlertAction
from autosportlabs.racecapture.geo.geopoint import GeoPoint
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.help.helpmanager import HelpInfo
from garden_androidtabs import AndroidTabsBase, AndroidTabs
from autosportlabs.racecapture.theme.color import ColorScheme
from fieldlabel import FieldLabel
from collections import OrderedDict
from copy import copy
import math

# Dashboard screens
from autosportlabs.racecapture.views.dashboard.gaugeview import GaugeView2x, GaugeView3x, GaugeView5x, GaugeView8x
from autosportlabs.racecapture.views.dashboard.tachometerview import TachometerView
from autosportlabs.racecapture.views.dashboard.laptimeview import LaptimeView
from autosportlabs.racecapture.views.dashboard.rawchannelview import RawChannelView

class DashboardState(object):
    def __init__(self, **kwargs):
        self._gauge_colors = {}
        self._active_alerts = {}

    def set_channel_color(self, channel, color_alertaction):
        color_stack = self._gauge_colors.get(channel)
        if color_stack is None:
            self._gauge_colors[channel] = [color_alertaction]
        else:
            color_stack.insert(0, color_alertaction)

    def get_gauge_color(self, channel):
        color_stack = self._gauge_colors.get(channel)
        return next(iter(color_stack), None) if color_stack is not None else None

    def clear_channel_color(self, channel, color_alertaction):
        color_stack = self._gauge_colors.get(channel)
        if color_stack is None:
            return

        for aa in color_stack:
            if aa == color_alertaction:
                color_stack.remove(aa)
                return

    def set_popupalert(self, channel, popup_alertaction):
        self._active_alerts[channel] = popup_alertaction

    def clear_popupalert(self, channel, popup_alertaction):
        if popup_alertaction == self._active_alerts.get(channel):
            # ensure we're removing *this* popup_alertaction, not
            self._active_alerts.pop(channel, None)

    def get_popupalerts(self):
        return self._active_alerts

    def clear_channel_states(self, channel):
        color_stack = self._gauge_colors.pop(channel, None)
        if color_stack is not None:
            for aa in color_stack:
                aa.is_active = False

        popup_alertaction = self._active_alerts.pop(channel, None)
        if popup_alertaction is not None:
            popup_alertaction.is_active = False

class DashboardFactory(object):
    """
    Factory for creating dashboard screens. 
    Screens are instances of DashboardScreen
    Screens are referenced and managed by their key name. 
    """
    def __init__(self, dashboard_state, databus, settings, track_manager, status_pump, **kwargs):
        self._view_builders = OrderedDict()
        self._view_previews = OrderedDict()
        self._databus = databus
        self._settings = settings
        self._track_manager = track_manager
        self._status_pump = status_pump
        self._dashboard_state = dashboard_state
        self._init_factory()
        self._gauge_colors = {}

    def get_gauge_color(self, channel):
        return self._gauge_colors.get(channel)

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

        # Disabled until ready for use
        # self._add_screen('racestatus_view', self.build_racestatus_view, 'Race Status', '')

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
        return GaugeView5x(name='5x_gauge_view',
                           databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state)

    def build_3x_gauge_view(self):
        return GaugeView3x(name='3x_gauge_view',
                           databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state)

    def build_2x_gauge_view(self):
        return GaugeView2x(name='2x_gauge_view',
                           databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state)

    def build_8x_gauge_view(self):
        return GaugeView8x(name='8x_gauge_view',
                           databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state)

    def build_tachometer_view(self):
        return TachometerView(name='tach_view',
                              databus=self._databus,
                              settings=self._settings,
                              dashboard_state=self._dashboard_state)

    def build_laptime_view(self):
        return LaptimeView(name='laptime_view',
                           databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state)

    def build_raw_channel_view(self):
        return RawChannelView(name='rawchannel_view',
                              databus=self._databus,
                              settings=self._settings,
                              dashboard_state=self._dashboard_state)

    def build_traction_view(self):
        return TractionView(name='traction_view',
                            databus=self._databus,
                            settings=self._settings,
                            dashboard_state=self._dashboard_state)

    def build_racestatus_view(self):
        return RaceStatusView(name='racestatus_view',
                              databus=self._databus,
                              settings=self._settings,
                              dashboard_state=self._dashboard_state,
                              track_manager=self._track_manager,
                              status_pump=self._status_pump)

    def build_heatmap_view(self):
        return HeatmapView(name='heatmap_view', databus=self._databus,
                           settings=self._settings,
                           dashboard_state=self._dashboard_state,
                           track_manager=self._track_manager,
                           status_pump=self._status_pump)

class AlertScreen(Screen):
    popup_alertaction = ObjectProperty()

    timeout = NumericProperty()
    key = StringProperty()
    popup_alert_view = ObjectProperty()
    source = ObjectProperty(None)
    high_priority = BooleanProperty()
    background_color = ListProperty()
    shape_color = ListProperty()
    shape_vertices = ListProperty()
    shape_indices = ListProperty()

    Builder.load_string("""
<AlertScreen>
    BoxLayout:
            
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: root.background_color
            Rectangle:
                size: self.size
                pos: self.pos
        
        AnchorLayout:
            canvas.before:
                Color:
                    rgba: root.shape_color
                Mesh:
                    vertices: root.shape_vertices
                    indices: root.shape_indices
                    mode: 'triangle_fan'
            size_hint_y: 0.5
            id: alert_container
            FieldLabel:
                text: root.popup_alertaction.message
                id: alert_msg
                halign: 'center'
                font_size: min(dp(90), self.height)
            
        BoxLayout:
            size_hint_y: 0.5
            IconButton:
                text: u'\uf00d'
                id: alert_msg_no
                on_press: root._alert_msg_no()
            IconButton:
                text: u'\uf00c'
                id: alert_msg_yes
                on_press: root._alert_msg_yes()
            
    """)

    def __init__(self, **kwargs):
        super(AlertScreen, self).__init__(**kwargs)
        Clock.schedule_once(self._init_view)
        self.anim = None
        self.ack_msg = 'OK'

    def on_popup_alertaction(self, instance, value):
        self._update_shape()
        self._update_colors()

    def _init_view(self, *args):
        is_question = self.popup_alertaction.message.endswith('?')
        self.ids.alert_msg_yes.size_hint = (1.0, 1.0) if is_question else (0, 0)
        self.ack_msg = 'NO' if is_question else 'OK'

        self.ids.alert_container.bind(size=self._update_shape)

        if self.high_priority:
            anim = Animation(color=(1, 1, 1, 0), duration=0.2) + Animation(color=(1, 1, 1, 0), duration=0.2)
            anim += Animation(color=(1, 1, 1, 1), duration=0.2) + Animation(color=(1, 1, 1, 1), duration=0.2)
            anim.repeat = True
            anim.start(self.ids.alert_msg)
            self.anim = anim

    def _update_colors(self):
        color = self.popup_alertaction.color_rgb
        dim_color = [color[0] * 0.5, color[1] * 0.5, color[2] * 0.5, 1.0]
        bright_color = color
        shape = self.popup_alertaction.shape

        self.shape_color = bright_color if shape is not None else dim_color
        self.background_color = bright_color if shape is None else dim_color

    def _update_shape(self, *args):
        if len(args) != 2:
            return
        ac = self.ids.alert_container
        size = ac.size
        pos = ac.pos
        shape = self.popup_alertaction.shape
        if shape is None:
            self.shape_vertices = []
            self.shape_indices = []
        elif shape == 'triangle':
            # calculate points for a centered triangle
            center = (size[0] / 2, size[1] / 2)
            length = size[1] * 1
            size_half = length / 2
            triangle_height = size_half * math.sqrt(3)
            x = center[0] - size_half + pos[0]
            y = center[1] - triangle_height / 2 + pos[1]
            self.shape_vertices = [x, y, 0, 0, center[0], y + triangle_height, 0, 0, x + length, y, 0, 0]
            self.shape_indices = [0, 1, 2]
        elif shape == 'octagon':
            # calculate points for a centered octagon
            center = (size[0] / 2, size[1] / 2)
            length = size[1] * .9
            size_half = length / 2
            size_13rd = length / 3
            size_23rds = size_13rd * 2
            x = center[0] - size_half + pos[0]
            y = center[1] - size_half + pos[1]
            self.shape_vertices = [x + size_13rd, y, 0, 0,
                                   x, y + size_13rd, 0, 0,
                                   x, y + size_23rds, 0, 0,
                                   x + size_13rd, y + length, 0, 0,
                                   x + size_23rds, y + length, 0, 0,
                                   x + length, y + size_23rds, 0, 0,
                                   x + length, y + size_13rd, 0, 0,
                                   x + size_23rds, y, 0, 0
                                   ]
            self.shape_indices = [0, 1, 2, 3, 4, 5, 6, 7]
        else:
            self.shape_vertices = []
            self.shape_indices = []

    def on_enter(self):
        if self.anim is not None:
            self.anim.start(self.ids.alert_msg)

    def on_leave(self):
        self.stop_screen()

    def stop_screen(self):
        if self.anim is not None:
           self.anim.repeat = False

    def _hide(self, *args):
        self.popup_alertaction.is_squelched = True
        self.popup_alert_view.remove_alert(self.key)

    def _alert_msg_yes(self):
        self.popup_alert_view.send_api_alert_msg(self.source, 'YES')
        self._hide()

    def _alert_msg_no(self):
        self.popup_alert_view.send_api_alert_msg(self.source, self.ack_msg)
        self._hide()

class PopupAlertView(BoxLayout):
    Builder.load_string("""
<PopupAlertView>:
    size_hint_x: None
    width: dp(600)
    pos_hint:{"center_x":0.5}
    id: alertbar
    size_hint_y: None
    height: 0
    orientation: 'vertical'
    BoxLayout:
        ScreenManager:
            id: screens
    """)

    MSG_CHAR_WIDTH = 60
    MIN_POPUP_WIDTH = dp(600)
    def __init__(self, **kwargs):
        super(PopupAlertView, self).__init__(**kwargs)
        self.minimize = None
        self._current_screens = {}
        Clock.schedule_interval(self._show_next_screen, 2.0)
        self.minimize_trigger = Clock.create_trigger(self._minimize, 4.0)


    def _adjust_width(self):
        min_width = PopupAlertView.MIN_POPUP_WIDTH
        for screen in self._current_screens.itervalues():
            min_width = max(min_width, len(screen.popup_alertaction.message) * PopupAlertView.MSG_CHAR_WIDTH)
        self.width = min(min_width, Window.width)

    def _show_next_screen(self, *args):
        next_screen = self.ids.screens.next()
        if next_screen is not None:
            self.ids.screens.current = next_screen

    def send_api_alert_msg(self, source, msg):
        source.send_api_msg({'alertmsgReply':{'priority':1, 'message':msg}})

    def send_api_alert_msg_ack(self, source, msg_id):
        source.send_api_msg({'alertmsgAck':{'id':msg_id}})

    def _hide(self, screen):
        if self.minimize is not None:
            Clock.unschedule(self._minimize)
        a = Animation(height=0, duration=0.5)
        a.bind(on_complete=lambda x, y: self.ids.screens.clear_widgets([screen]))
        a.start(self)

    def _minimize(self, *args):
        a = Animation(height=self.height * DashboardView.ALERT_BAR_HEIGHT_NORMAL_PCT, duration=1.0, t=DashboardView.TRANSITION_STYLE).start(self)

    def remove_alert(self, key):
        screen = self._current_screens.pop(key, None)
        self._adjust_width()
        if screen is None:
            return

        screen.stop_screen()

        if not bool(self._current_screens):
            # if there no other screens showing, defer until
            # hide animation is complete
            self._hide(screen)
        else:
            # remove the screen immediately
            self.ids.screens.clear_widgets([screen])


    def get_active_alerts(self):
        return self._current_screens.itervalues()

    def add_alert(self, key, popup_alertaction, source, high_priority, msg_id, timeout):
        current_screen = self._current_screens.get(key)
        if current_screen is not None:
            return

        screen = AlertScreen(name=key,
                             key=key,
                             source=source,
                             high_priority=high_priority,
                             msg_id=msg_id,
                             timeout=timeout,
                             popup_alert_view=self,
                             popup_alertaction=popup_alertaction)

        self._current_screens[key] = screen
        self.ids.screens.add_widget(screen)
        self.ids.screens.current = screen.name

        self._show_alert()
        self.send_api_alert_msg_ack(source, msg_id)

        # reset the minimize timer
        self.minimize_trigger.cancel()
        self.minimize_trigger()
        self._adjust_width()

    def _show_alert(self):
        target_height = self.parent.height * (DashboardView.ALERT_BAR_HEIGHT_URGENT_PCT)  # if is_high_priority else DashboardView.ALERT_BAR_HEIGHT_NORMAL_PCT)
        Animation(height=target_height, duration=0.5, t=DashboardView.TRANSITION_STYLE).start(self)


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
                size_hint_y: None
                height: dp(50)
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
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'bottom'
            
            BoxLayout:
                orientation: 'vertical'
                PopupAlertView:
                    id: popup_alert
                BoxLayout:
                    size_hint_y: None
                    height: dp(50)
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
    ALERT_BAR_HEIGHT_URGENT_PCT = 0.8
    ALERT_BAR_HEIGHT_NORMAL_PCT = 0.25
    ALERT_BAR_GROW_RATE = dp(20)
    ALERT_BAR_UPDATE_INTERVAL = 0.02
    TRANSITION_STYLE = 'in_out_expo'
    ALERT_ENGINE_INTERVAL = 0.1

    def __init__(self, status_pump, track_manager, rc_api, rc_config, databus, settings, **kwargs):
        self._initialized = False
        super(DashboardView, self).__init__(**kwargs)

        dashboard_state = self._dashboard_state = DashboardState()
        self._alert_engine = AlertEngine(self._dashboard_state)
        self._dashboard_factory = DashboardFactory(dashboard_state, databus, settings, track_manager, status_pump)
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_config_updated')
        self.register_event_type('on_config_written')
        self._screens = []
        self._current_screen = None
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
        self.alert_bar_height = 0
        self._start_alert_engine()
        self._current_sample = None

    def _start_alert_engine(self):
        self._databus.add_sample_listener(self._on_sample)

        Clock.schedule_interval(self._check_alerts, DashboardView.ALERT_ENGINE_INTERVAL)

    def _on_sample(self, sample):
        self._current_sample = sample

    def _check_alerts(self, *args):
        prefs = self._settings.userPrefs
        current_sample = self._current_sample
        if current_sample is not None:
            for channel, value in current_sample.iteritems():
                alertrules = prefs.get_alertrules(channel)
                self._alert_engine.process_rules(alertrules, channel, value)


        dashboard_state = self._dashboard_state
        active_alerts = dashboard_state.get_popupalerts()
        popup_alert = self.ids.popup_alert

        # add screens as necessary
        displayed_alert_screens = popup_alert.get_active_alerts()
        displayed_alertactions = [s.popup_alertaction for s in displayed_alert_screens]
        for channel, popup_alertaction in active_alerts.iteritems():
            if not popup_alertaction.is_squelched and not popup_alertaction in displayed_alertactions:
                popup_alert.add_alert(key=channel,
                                               source=self._alert_engine,
                                               high_priority=False,
                                               msg_id=0,
                                               timeout=1.0,
                                               popup_alertaction=popup_alertaction)

        # remove screens as necessary
        # only remove screens that are generated by AlertEngione
        displayed_alert_screens = popup_alert.get_active_alerts()
        alert_screens_to_remove = [s for s in displayed_alert_screens
                                   if not s.popup_alertaction in active_alerts.itervalues()
                                   and s.source == self._alert_engine]
        for s in alert_screens_to_remove:
            popup_alert.remove_alert(s.key)

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
        dashboard_state = self._dashboard_state

        activeGauges = list(kvFindClass(self, Gauge))

        for gauge in activeGauges:
            gauge.settings = settings
            gauge.data_bus = databus
            gauge.dashboard_state = dashboard_state

    def _init_view(self):
        databus = self._databus
        settings = self._settings
        dashboard_state = self._dashboard_state

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
            gauge.dashboard_state = dashboard_state

        # Initialize our alert type widgets
        self._alert_widgets['pit_stop'] = PitstopTimerView(databus, 'Pit Stop')

        self._notify_preference_listeners()
        self._show_last_view()

        if self._rc_api.connected:
            self._race_setup()

        self._rc_api.add_connect_listener(self._on_rc_connect)
        self._rc_api.addListener('alertmessage', self._on_alertmessage)
        self._initialized = True

        Clock.schedule_once(lambda dt: HelpInfo.help_popup('dashboard_gauge_help', self, arrow_pos='right_mid'), 2.0)

    def _on_alertmessage(self, alertmessage, source):

        msg = alertmessage.get('alertmessage')
        if msg:
            alertmessage = msg.get('message')
            pri = msg.get('priority') == 1
            msg_id = msg.get('id')
            self.ids.popup_alert.add_alert('podium_{}'.format(msg_id), PopupAlertAction(message=alertmessage), source, pri, msg_id, 4.0)
        else:
            Logger.warning('DashboardView: got malformed alert message: {}'.format(alertmessage))

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

    def _exit_screen(self, screen=None):
        if screen is None:
            screen = self.ids.carousel.current_slide
        if len(screen.children) > 0:
            screen.children[0].on_exit()

    def _pre_enter_screen(self, screen):
        if screen is not None and len(screen.children) > 0:
            screen.children[0].on_enter()

    def on_nav_left(self):
        self._exit_screen()
        carousel = self.ids.carousel
        self._pre_enter_screen(carousel.previous_slide)
        carousel.load_previous()

    def on_nav_right(self):
        self._exit_screen()
        carousel = self.ids.carousel
        self._pre_enter_screen(carousel.next_slide)
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
        slide_screen.children[0].on_enter()

    def on_current_slide(self, slide_screen):
        if self._initialized == True:
            self._check_load_screen(slide_screen)
            view = slide_screen.children[0]

            if self._current_screen is not None:
                self._exit_screen(self._current_screen)
            self._current_screen = slide_screen

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
