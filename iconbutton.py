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
from kivy.event import EventDispatcher
kivy.require('1.10.0')
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.app import Builder
from kivy.graphics import Color
from kivy.metrics import sp, dp
from kivy.properties import NumericProperty, ListProperty, StringProperty, ObjectProperty, BooleanProperty
from fieldlabel import FieldLabel
from math import sin, cos, pi
from autosportlabs.racecapture.theme.color import ColorScheme
from kivy.clock import Clock
from kivy.core.window import Window

ICON_BUTTON_KV = """
<RoundedRect>:
    line_width: max(1, self.height * 0.15)
    radius: max(1, self.height * 0.007)
    canvas:
        Color: 
            rgba: self.rect_color
        Line:
            rounded_rectangle: (self.x + (self.line_width), self.y + (self.line_width), self.right - self.x - self.line_width * 2, self.top - self.y - self.line_width *2, self.radius)      
            width: self.line_width
        Rectangle:
            pos: (self.x + self.line_width * 2, self.y + self.line_width * 2) 
            size: (max(1,self.width - self.line_width * 4), max(1,self.height - self.line_width * 4))

<TileIconButton>:
    RoundedRect:
        rect_color: root.tile_color
    BoxLayout:
        orientation: 'vertical'
        Label:
            id: icon
            font_name: 'resource/fonts/fa.ttf'            
            color: root.icon_color
            size_hint_y: 0.7
            font_size: self.height * 0.7
            text: root.icon
        Label:
            id: label
            font_name: root.title_font
            font_size: root.title_font_size
            color: root.title_color
            size_hint_y: 0.3
            text: root.title    
            
<LabelIconButton>:
    RoundedRect:
        rect_color: root.tile_color
    BoxLayout:
        orientation: 'horizontal'
        padding: (dp(8), 0)
        spacing: dp(8)
        Label:
            id: icon
            size_hint_x: 0.25
            font_name: 'resource/fonts/fa.ttf'
            color: root.icon_color
            font_size: root.icon_size
            text: root.icon
        Label:
            id: label
            valign: 'middle'
            halign: 'left'
            text_size: (self.width, None)
            font_name: root.title_font
            font_size: root.title_font_size
            color: root.title_color
            size_hint_x: 0.75
            text: root.title    

<IconButton>:
    background_color: [0, 0, 0, 0]
    background_down: ''
    font_size: self.height
    
    color: [1.0, 1.0, 1.0, 0.8]
    font_name: 'resource/fonts/fa.ttf'
"""

Builder.load_string(ICON_BUTTON_KV)

class FadeableWidget(EventDispatcher):
    FADED_ALPHA = 0.1
    BRIGHT_ALPHA = 1.0
    FADE_STEP = 0.05
    FADE_INTERVAL = 0.05
    FADE_DELAY = 5.0
    fade_color = ObjectProperty([0, 0, 0, 0])
    pulsing = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(FadeableWidget, self).__init__(**kwargs)
        self._current_alpha = None
        self.brighten_mode = True
        self._schedule_fade = Clock.create_trigger(self._fade_back, FadeableWidget.FADE_DELAY)
        self._schedule_step = Clock.create_trigger(self._fade_step, FadeableWidget.FADE_INTERVAL)

    def _fade_step(self, *args):
        if self.disabled:
            return

        if self.brighten_mode == True:
            if self._current_alpha < FadeableWidget.BRIGHT_ALPHA:
                self._current_alpha += FadeableWidget.FADE_STEP
                self._schedule_step()
            elif self.pulsing:
                self.brighten_mode = False
                self._schedule_step()

        if self.brighten_mode == False:
            if self._current_alpha > FadeableWidget.FADED_ALPHA:
                self._current_alpha -= FadeableWidget.FADE_STEP
                self._schedule_step()
            elif self.pulsing:
                self.brighten_mode = True
                self._schedule_step()

        color = self.fade_color
        self.fade_color = [color[0], color[1], color[2], self._current_alpha]

    def _fade_back(self, *args):
        self.fade()

    def _start_transition(self):
        if self._current_alpha is None:
            self._current_alpha = self.fade_color[3]
        self._schedule_step()

    def fade(self):
        '''
        Fade this button away to a shadow with low alpha value
        '''
        self.brighten_mode = False
        self._start_transition()

    def brighten(self):
        '''
        Brighten this button
        '''
        self.brighten_mode = True
        self._start_transition()
        self._schedule_fade()

    def on_pulsing(self, instance, value):
        if value and not self.disabled:
            self.brighten()

    def on_disabled(self, instance, value):
        if not value and self.pulsing:
            self.brighten()

class IconButton(FadeableWidget, Button):

    def __init__(self, **kwargs):
        super(IconButton, self).__init__(**kwargs)

    def on_color(self, instance, value):
        self.fade_color = value

    def on_fade_color(self, instance, value):
        self.color = value

class RoundedRect(BoxLayout):
    rect_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))
    line_width = NumericProperty(dp(10))
    radius = NumericProperty(10)

class TileIconButton(FadeableWidget, ButtonBehavior, AnchorLayout):
    title_font = StringProperty('')
    title_font_size = NumericProperty(min(30,sp(30)))
    tile_color = ObjectProperty((0.5, 0.5, 0.5, 0.8))
    icon_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    title_color = ObjectProperty((1.0, 1.0, 1.0, 0.8))
    icon = StringProperty('')
    title = StringProperty('')

    def __init__(self, **kwargs):
        super(TileIconButton, self).__init__(**kwargs)

class LabelIconButton(FadeableWidget, ButtonBehavior, AnchorLayout):
    title_font = StringProperty('resource/fonts/ASL_regular.ttf')
    title_font_size = NumericProperty(sp(20))
    tile_color = ObjectProperty(ColorScheme.get_dark_accent())
    icon_color = ObjectProperty(ColorScheme.get_accent())
    title_color = ObjectProperty(ColorScheme.get_accent())
    icon = StringProperty('')
    icon_size = NumericProperty(sp(25))
    title = StringProperty('')

    def __init__(self, **kwargs):
        super(LabelIconButton, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_tile_color(self, instance, value):
        self.fade_color = value

    def on_mouse_pos(self, *args):
        pos = args[1]
        if self.pulsing:
            return

        if self.collide_point(*self.to_widget(*pos)):
            if not self.disabled:
                self.tile_color = ColorScheme.get_medium_accent()
        else:
            self.tile_color = ColorScheme.get_dark_accent()

    def on_press(self, *args):
        super(LabelIconButton, self).on_press(*args)
        if not self.disabled and not self.pulsing:
            self.tile_color = ColorScheme.get_medium_accent()

    def on_release(self, *args):
        super(LabelIconButton, self).on_release(*args)
        if not self.pulsing:
            self.tile_color = ColorScheme.get_dark_accent()

    def on_fade_color(self, instance, value):
        self.tile_color = value

    def on_pulsing(self, instance, value):
        self.tile_color = ColorScheme.get_medium_accent()
        super(LabelIconButton, self).on_pulsing(instance, value)

    def on_disabled(self, instance, value):
        super(LabelIconButton, self).on_disabled(instance, value)
        self.tile_color = ColorScheme.get_medium_accent()
