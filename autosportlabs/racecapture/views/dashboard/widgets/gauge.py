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
from kivy.properties import ListProperty, StringProperty, NumericProperty, ObjectProperty, DictProperty, \
    BooleanProperty
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.bubble import BubbleButton
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from utils import kvFind, kvquery, dist
from functools import partial
from kivy.app import Builder
from kivy.logger import Logger
from autosportlabs.racecapture.views.channels.channelselectview import ChannelSelectDialog
from autosportlabs.racecapture.views.alerts.alerteditor import AlertRulesView
from autosportlabs.racecapture.alerts.alertrules import AlertRule, AlertRuleCollection
from autosportlabs.racecapture.alerts.alertactions import ColorAlertAction, PopupAlertAction, ShiftLightAlertAction, LedAlertAction

from autosportlabs.racecapture.views.popup.centeredbubble import CenteredBubble
from autosportlabs.racecapture.data.channels import *
from autosportlabs.racecapture.views.util.viewutils import format_laptime
from kivy.core.window import Window

DEFAULT_NORMAL_COLOR = [1.0, 1.0 , 1.0, 1.0]

DEFAULT_VALUE = None
DEFAULT_MIN = 0
DEFAULT_MAX = 100
DEFAULT_PRECISION = 0
DEFAULT_TYPE = CHANNEL_TYPE_SENSOR
MENU_ITEM_RADIUS = 100

Builder.load_string('''
<CustomizeGaugeBubble>
    orientation: 'vertical'
    size_hint: (None, None)
    #pos_hint: {'center_x': .5, 'y': .5}
    #arrow_pos: 'bottom_mid'
    #background_color: (1, 0, 0, 1.0) #50% translucent red
    #border: [0, 0, 0, 0]    
''')

class CustomizeGaugeBubble(CenteredBubble):
    pass

NULL_LAP_TIME = '--:--.---'

class Gauge(AnchorLayout):
    POPUP_DISMISS_TIMEOUT_SHORT = 10.0
    POPUP_DISMISS_TIMEOUT_LONG = 60.0
    rcid = None
    settings = ObjectProperty(None)
    value_size = NumericProperty(0)
    title_size = NumericProperty(0)
    title = StringProperty('')
    data_bus = ObjectProperty(None)
    dashboard_state = ObjectProperty(None)
    title_color = ObjectProperty(DEFAULT_NORMAL_COLOR)
    normal_color = ObjectProperty(DEFAULT_NORMAL_COLOR)
    visible = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(Gauge, self).__init__(**kwargs)
        self.rcid = kwargs.get('rcid', self.rcid)
        self.data_bus = kwargs.get('dataBus', self.data_bus)
        self.settings = kwargs.get('settings', self.settings)

    @property
    def titleView(self):
        return self.ids.title

    def on_title(self, instance, value):
        try:
            if value is not None:
                view = self.ids.title
                view.text = str(value)
        except:  # the gauge may not have a title
            pass

    def on_title_color(self, instance, value):
        self.titleView.color = value

    def on_title_size(self, instance, value):
        view = self.titleView
        if view:
            view.font_size = value

    def update_title(self, channel_name, channel_meta):
        try:
            title = ''
            if channel_name is not None and channel_meta is not None:
                title = channel_meta.name
                if channel_meta.units and len(channel_meta.units):
                    title += '\n({})'.format(channel_meta.units)
            self.title = title
        except Exception as e:
            Logger.error('Gauge: Failed to update gauge title & units ' + str(e) + ' ' + str(title))

    def on_channel_meta(self, channel_metas):
        pass

class SingleChannelGauge(Gauge):
    _valueView = None
    channel = StringProperty(None, allownone=True)
    value = NumericProperty(None, allownone=True)
    sensor_format = "{:.0f}"
    value_formatter = None
    precision = NumericProperty(DEFAULT_PRECISION)
    type = NumericProperty(DEFAULT_TYPE)
    halign = StringProperty(None)
    valign = StringProperty(None)

    def __init__(self, **kwargs):
        super(SingleChannelGauge, self).__init__(**kwargs)
        self.channel = kwargs.get('targetchannel', self.channel)
        self.value_formatter = self.sensor_formatter

    @property
    def valueView(self):
        if not self._valueView:
            self._valueView = self.ids.value
        return self._valueView

    def on_halign(self, instance, value):
        self.valueView.halign = value

    def on_valign(self, instance, value):
        self.valueView.valign = value

    def on_channel_meta(self, channel_metas):
        channel = self.channel
        channel_meta = channel_metas.get(channel)
        if channel_meta is not None:
            self._update_display(channel_meta)
            self.update_title(channel, channel_meta)

    def _update_gauge_meta(self):
        if self.settings:
            channel_meta = self.settings.runtimeChannels.channels.get(self.channel)
            self._update_display(channel_meta)
            self.update_title(self.channel, channel_meta)
            self._update_channel_binding()

    def on_settings(self, instance, value):
        # Do I have an id so I can track my settings?
        if self.rcid:
            channel = self.settings.userPrefs.get_gauge_config(self.rcid) or self.channel
            if channel:
                self.channel = channel
                self._update_gauge_meta()

    def on_data_bus(self, instance, value):
        self._update_channel_binding()

    def update_colors(self):
        view = self.valueView
        if view:
            view.color = self.normal_color

    def refresh_value(self, value):
        view = self.valueView
        if view:
            view.text = self.value_formatter(value)
            self.update_colors()

    def on_value(self, instance, value):
        self.refresh_value(value)

    def sensor_formatter(self, value):
        return "" if value is None else self.sensor_format.format(value)

    def update_value_format(self):
        if self.type == CHANNEL_TYPE_TIME:
            self.value_formatter = format_laptime
        else:
            self.sensor_format = '{:.' + str(self.precision) + 'f}'
            self.value_formatter = self.sensor_formatter

        self.refresh_value(self.value)

    def on_value_size(self, instance, value):
        view = self.valueView
        if view:
            view.font_size = value

    def on_channel(self, instance, value):
        self._update_gauge_meta()

    def _update_display(self, channel_meta):
        if channel_meta:
            self.min = channel_meta.min
            self.max = channel_meta.max
            self.precision = channel_meta.precision
            self.type = channel_meta.type if channel_meta.type is not CHANNEL_TYPE_UNKNOWN else self.type
        else:
            self.min = DEFAULT_MIN
            self.max = DEFAULT_MAX
            self.precision = DEFAULT_PRECISION
            self.value = DEFAULT_VALUE
            self.type = DEFAULT_TYPE
        self.update_value_format()

    def _update_channel_binding(self):
        dataBus = self.data_bus
        channel = self.channel
        if dataBus and channel:
            dataBus.addChannelListener(str(channel), self.setValue)
            dataBus.addMetaListener(self.on_channel_meta)

    def setValue(self, value):
        if self.visible is True:
            self.value = value

class CustomizableGauge(ButtonBehavior, SingleChannelGauge):
    _popup = None
    _customizeGaugeBubble = None
    min = NumericProperty(DEFAULT_MIN)
    max = NumericProperty(DEFAULT_MAX)
    _dismiss_customization_popup_trigger = None
    is_removable = BooleanProperty(True)
    is_channel_selectable = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(CustomizableGauge, self).__init__(**kwargs)
        self._dismiss_customization_popup_trigger = Clock.create_trigger(self._dismiss_popup, Gauge.POPUP_DISMISS_TIMEOUT_LONG)

    def _remove_customization_bubble(self, *args):
        try:
            if self._customizeGaugeBubble:
                self._customizeGaugeBubble.dismiss()
                self._customizeGaugeBubble = None
        except:
            pass

    def removeChannel(self):
        self._remove_customization_bubble()
        channel = self.channel
        if channel:
            self.data_bus.removeChannelListener(channel, self.setValue)
        self.channel = None
        self.settings.userPrefs.set_gauge_config(self.rcid, None)

    def customizeGauge(self, *args):
        self._remove_customization_bubble()
        self.showChannelConfigDialog()

    def selectChannel(self, *args):
        self._remove_customization_bubble()
        self.showChannelSelectDialog()

    def select_alert_color(self):
        ds = self.dashboard_state
        if ds is None:
            return self.normal_color

        color = ds.get_gauge_color(self.channel)
        return self.normal_color if color is None else color.color_rgb

    def update_colors(self):
        view = self.valueView
        if view:
            view.color = self.select_alert_color()

    def showChannelSelectDialog(self):
        content = ChannelSelectDialog(settings=self.settings, channel=self.channel)
        content.bind(on_channel_selected=self.channel_selected)
        content.bind(on_channel_cancel=self._dismiss_popup)

        popup = Popup(title="Select Channel", content=content, size_hint=(0.5, 0.7))
        popup.bind(on_dismiss=self.popup_dismissed)
        popup.open()
        self._popup = popup
        self._dismiss_customization_popup_trigger()

    def showChannelConfigDialog(self):

        def popup_dismissed(instance):
            self.settings.userPrefs.set_alertrules(self.channel, alertrules)
            self.dashboard_state.clear_channel_states(self.channel)

        alertrules = self.settings.userPrefs.get_alertrules(self.channel)

        content = AlertRulesView(alertrules, channel=self.channel)
        content.min_value = self.min
        content.max_value = self.max
        content.precision = self.precision

        popup = Popup(title='Customize {}'.format(self.channel),
                      content=content,
                      size=(min(Window.width, dp(700)), min(Window.height, dp(400))),
                      size_hint=(None, None))
        popup.bind(on_dismiss=popup_dismissed)
        content.bind(title=lambda i, t: setattr(popup, 'title', t))
        popup.open()

    def channel_selected(self, instance, value):
        if self.channel:
            self.data_bus.removeChannelListener(self.channel, self.setValue)
        self.value = None
        self.channel = value
        self.settings.userPrefs.set_gauge_config(self.rcid, value)
        self._dismiss_popup()

    def popup_dismissed(self, *args):
        self._popup = None

    def _dismiss_popup(self, *args):
        if self._popup:
            self._popup.dismiss()
            self._popup = None

    def on_release(self):
        if not self.channel:
            self.showChannelSelectDialog()
        else:
            bubble = CustomizeGaugeBubble()
            buttons = []
            if self.is_removable: buttons.append(BubbleButton(text='Remove', on_press=lambda a:self.removeChannel()))
            if self.is_channel_selectable: buttons.append(BubbleButton(text='Select Channel', on_press=lambda a:self.selectChannel()))
            buttons.append(BubbleButton(text='Customize', on_press=lambda a:self.customizeGauge()))
            if len(buttons) == 1:
                buttons[0].dispatch('on_press')
            else:
                for b in buttons:
                    bubble.add_widget(b)

                bubble_height = dp(150)
                bubble_width = dp(200)
                bubble.size = (bubble_width, bubble_height)
                bubble.auto_dismiss_timeout(Gauge.POPUP_DISMISS_TIMEOUT_SHORT)
                self._customizeGaugeBubble = bubble
                self.add_widget(bubble)
                bubble.center_on_limited(self)

