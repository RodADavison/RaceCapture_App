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
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from fieldlabel import FieldLabel
from autosportlabs.racecapture.views.setup.setupfactory import setup_factory
from autosportlabs.racecapture.views.util.alertview import confirmPopup
from autosportlabs.racecapture.theme.color import ColorScheme
import os
import json

SETUP_VIEW_KV = """
<SetupItem>:
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background_translucent()
        Rectangle:
            pos: self.pos
            size: self.size    
    orientation: 'horizontal'
    IconButton:
        id: complete
        text: ''
        size_hint_x: 0.25
        font_size: self.height * 0.5
        color: ColorScheme.get_accent()
    FieldLabel:
        id: title
        size_hint_x: 0.75
        text: root.title
        color: root.title_color
        font_size: self.height * 0.4
    
<SetupView>:
    BoxLayout:
        orientation: 'horizontal'
        ScrollContainer:
            id: steps_scroll
            size_hint_x: 0.25
            do_scroll_x: False
            do_scroll_y: True
            bar_width: 0
            GridLayout:
                id: steps
                cols: 1
                row_default_height: dp(50)
                row_force_default: True
                size_hint_y: None
                padding: (dp(5), dp(5), dp(2.5), dp(5))
                spacing: dp(5)
                height: self.minimum_height
        BoxLayout:
            padding: (dp(2.5), dp(5), dp(5), dp(5))
            size_hint_x: 0.75     
            AnchorLayout:       
                ScreenManager:
                    id: screen_manager
                AnchorLayout:
                    anchor_x: 'left'
                    anchor_y: 'bottom'
                    padding: (dp(10), dp(10))
                    LabelIconButton:
                        id: next
                        title: 'Skip'
                        icon_size: self.height * 0.5
                        title_font_size: self.height * 0.6
                        icon: u'\uf052'
                        size_hint_x: None
                        size_hint_y: None
                        height: dp(50) 
                        width: dp(100) 
                        on_release: root.on_skip()
"""


class SetupItem(BoxLayout):
    """
    An individual setup item view that shows the state of the current step
    """
    title = StringProperty('')
    complete = BooleanProperty(False)
    active = BooleanProperty(False)
    title_color = ListProperty(ColorScheme.get_secondary_text())

    def __init__(self, **kwargs):
        super(SetupItem, self).__init__(**kwargs)

    def on_complete(self, instance, value):
        self.ids.complete.text = u'\uf00c' if value else ''

    def on_active(self, instance, value):
        self.title_color = ColorScheme.get_light_primary_text(
        ) if value else ColorScheme.get_secondary_text()


class SetupView(Screen):
    """
    The view for setting up RaceCapture features
    """
    SETUP_COMPLETE_DELAY_SEC = 1.0
    Builder.load_string(SETUP_VIEW_KV)

    def __init__(self, track_manager, preset_manager, settings, databus, base_dir, rc_api, rc_config, **kwargs):
        super(SetupView, self).__init__(**kwargs)
        self.register_event_type('on_setup_complete')
        self._preset_manager = preset_manager
        self._track_manager = track_manager
        self._settings = settings
        self._base_dir = base_dir
        self._databus = databus
        self._rc_api = rc_api
        self._rc_config = rc_config
        self._setup_config = None
        self._current_screen = None
        self._current_step = None
        self._steps = {}
        self._init_setup_config()

    def on_setup_complete(self):
        pass

    def on_enter(self):
        Clock.schedule_once(self.init_view)

    def _skip_request(self):
        def confirm_skip(instance, skip):
            popup.dismiss()
            self._setup_complete(skip)
        popup = confirmPopup('Skip', 'Continue setup next time?', confirm_skip)

    def on_skip(self):
        self._skip_request()

    def _init_setup_config(self):
        json_data = open(
            os.path.join(self._base_dir, 'resource', 'setup', 'setup.json'))
        setup_config = json.load(json_data)
        self._setup_config = setup_config

    def init_view(self, *args):
        steps = self._setup_config['steps']
        for step in steps:
            content = SetupItem(title=step['title'], complete=step['complete'])
            self.ids.steps.add_widget(content)
            self._steps[step['key']] = content

        self._show_next_screen()

    def _show_next_screen(self):
        screen, step = self._select_next_view()
        if screen and step:
            self.ids.screen_manager.switch_to(screen)
            self._current_step = step
            self._current_screen = screen
            screen.bind(on_next=self._on_next_screen)
            step = self._steps[step['key']]
            step.active = True
            self.ids.steps_scroll.scroll_to(step)

        else:
            self._setup_complete(show_next_time=False)

    def _on_next_screen(self, instance):
        step = self._current_step
        step['complete'] = True
        self._steps[step['key']].complete = True
        self._show_next_screen()

    def _select_next_view(self):
        setup_config = self._setup_config
        steps = setup_config['steps']
        for step in steps:
            if step['complete'] == False:
                screen, step = self._select_view(step), step
                screen.is_last = step == steps[-1]
                return screen, step
        return None, None

    def _select_view(self, step):
        screen = setup_factory(step['key'])
        screen.preset_manager = self._preset_manager
        screen.rc_api = self._rc_api
        screen.settings = self._settings
        screen.rc_config = self._rc_config
        screen.track_manager = self._track_manager
        screen.setup_config = self._setup_config
        return screen

    def _setup_complete(self, show_next_time=False):
        self._settings.userPrefs.set_pref(
            'setup', 'setup_enabled', show_next_time)
        Clock.schedule_once(lambda dt: self.dispatch(
            'on_setup_complete'), SetupView.SETUP_COMPLETE_DELAY_SEC)
