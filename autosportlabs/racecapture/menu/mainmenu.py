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
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.properties import StringProperty, BooleanProperty
from autosportlabs.racecapture.theme.color import ColorScheme
from fieldlabel import FieldLabel
from utils import kvFind
import mainfonts

MAIN_MENU_KV = """
<MainMenuItem>:
    orientation: 'horizontal'
    spacing: sp(5)
    Label:
        size_hint_x: 0.05
    FieldLabel:
        size_hint_x: 0.25
        font_size: sp(40)
        rcid: 'icon'
        font_name: 'resource/fonts/fa.ttf'
    FieldLabel:
        size_hint_x: 0.75
        font_size: sp(27)
        rcid: 'desc'

<MainMenu>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: ColorScheme.get_dark_background()
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        GridLayout:
            size_hint: 1, .9
            spacing: sp(5)
            cols: 1
            row_default_height: root.height * 0.1
            row_force_default: True
            MainMenuItem:
                rcid: 'dash'
                icon: '\357\203\244'
                description: 'Dashboard'
                on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
            MainMenuItem:
                rcid: 'analysis'
                icon: '\357\202\200'
                description: 'Analysis'
                on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
            MainMenuItem:
                rcid: 'config'
                icon: '\357\202\205'
                description: 'Setup'
                on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
            MainMenuItem:
                rcid: 'preferences'
                icon: '\357\200\207'
                description: 'Preferences'
                on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
            MainMenuItem:
                rcid: 'status'
                icon: u'\uf05a'
                description: 'System Status'
                on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
        MainMenuItem:
            size_hint: 1, .1
            rcid: 'exit'
            icon: '\357\200\221'
            description: 'Exit'
            on_main_menu_item_selected: root.on_main_menu_item_selected(*args)
"""
class MainMenu(BoxLayout):
    Builder.load_string(MAIN_MENU_KV)

    def __init__(self, **kwargs):
        super(MainMenu, self).__init__(**kwargs)
        self.register_event_type('on_main_menu_item')

    def on_main_menu_item(self, value):
        pass

    def on_main_menu_item_selected(self, instance, value):
        self.dispatch('on_main_menu_item', value)

class MainMenuItem(BoxLayout):
    disabledColor = (0.3, 0.3, 0.3, 1.0)
    enabledColor = (1.0, 1.0, 1.0, 1.0)
    rcid = None
    icon = StringProperty('')
    description = StringProperty('')
    enabled = BooleanProperty(True)

    def __init__(self, **kwargs):
        super(MainMenuItem, self).__init__(**kwargs)
        self.bind(icon=self.on_icon_text)
        self.bind(description=self.on_description_text)
        rcid = kwargs.get('rcid', None)
        self.register_event_type('on_main_menu_item_selected')

    def setEnabledDisabledColor(self, widget):
        if self.enabled:
            widget.color = self.enabledColor
        else:
            widget.color = self.disabledColor

    def on_main_menu_item_selected(self, value):
        pass

    def on_icon_text(self, instance, value):
        icon = kvFind(self, 'rcid', 'icon')
        icon.text = value
        self.setEnabledDisabledColor(icon)

    def on_description_text(self, instance, value):
        label = kvFind(self, 'rcid', 'desc')
        label.text = value
        self.setEnabledDisabledColor(label)

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_main_menu_item_selected', self.rcid)
            return True
        return super(MainMenuItem, self).on_touch_up(touch)

class DisabledMainMenuItem(MainMenuItem):
    def __init__(self, **kwargs):
        super(DisabledMainMenuItem, self).__init__(**kwargs)
        self.enabled = False
