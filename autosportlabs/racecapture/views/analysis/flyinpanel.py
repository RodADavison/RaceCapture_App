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
from kivy.logger import Logger
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.window import Window
import datetime

FLYIN_PANEL_LAYOUT = '''
<FlyinPanel>:
    size_hint: (1,1)
    BoxLayout:
        id: flyin
        orientation: 'vertical'
        size_hint: (0.25,1)
        pos: (root.width - self.width, self.height)
        canvas.before:
            Color:
                rgba: (0,0,0,1)
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            id: content
            size_hint: (1,0.95)
        FlyinHandle:
            canvas.before:
                Color:
                    rgba: ColorScheme.get_primary()
                Rectangle:
                    pos: self.pos
                    size: self.size
            id: handle
            size_hint: (1,0.05)
            on_press: root.toggle()
'''

class FlyinPanelException(Exception):
    '''Raised when add_widget is called incorrectly on FlyinPanel
    '''

class FlyinHandle(ButtonBehavior, AnchorLayout):
    pass

class FlyinPanel(FloatLayout):

    content = ObjectProperty()
    handle = ObjectProperty()

    # how long we wait to auto-dismiss session list
    # after a perioud of disuse
    SESSION_HIDE_DELAY = 1.0
    MINIMUM_OPEN_TIME = datetime.timedelta(seconds=0.5)
    TRANSITION_STYLE = 'in_out_elastic'
    SHOW_POSITION = 0

    def __init__(self, **kwargs):
        Builder.load_string(FLYIN_PANEL_LAYOUT)
        super(FlyinPanel, self).__init__(**kwargs)
        self.hide_decay = Clock.create_trigger(lambda dt: self.hide(), self.SESSION_HIDE_DELAY)
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_motion=self.on_motion)
        Clock.schedule_once(lambda dt: self.show())
        self._shown_at = None

    def flyin_collide_point(self, x, y):
        return self.ids.flyin.collide_point(x, y)

    def on_motion(self, instance, event, motion_event):
        if self.ids.flyin.collide_point(motion_event.x, motion_event.y):
            self.cancel_hide()

    def on_mouse_pos(self, x, pos):
        if self.ids.flyin.collide_point(pos[0], pos[1]):
            self.cancel_hide()
            return True
        return False

    def add_widget(self, widget):
        if len(self.children) == 0:
            super(FlyinPanel, self).add_widget(widget)
        else:
            if len(self.ids.content.children) == 0:
                self.ids.content.add_widget(widget)
            elif len(self.ids.handle.children) == 0:
                self.ids.handle.add_widget(widget)
            else:
                raise FlyinPanelException('Can only add one content widget and one handle widget to FlyinPanel')

    def schedule_hide(self):
        # do not dismiss before the minimum open time. prevents false triggers
        if self._shown_at is not None and FlyinPanel.MINIMUM_OPEN_TIME + self._shown_at > datetime.datetime.now():
            return
        self.hide_decay()

    def cancel_hide(self):
        Clock.unschedule(self.hide_decay)

    def hide(self):
        b_height = self.ids.handle.height
        anim = Animation(y=(self.height - b_height), t=self.TRANSITION_STYLE)
        anim.start(self.ids.flyin)

    def show(self):
        anim = Animation(y=self.SHOW_POSITION, t=self.TRANSITION_STYLE)
        anim.start(self.ids.flyin)
        self._shown_at = datetime.datetime.now()

    @property
    def is_hidden(self):
        return self.ids.flyin.y != self.SHOW_POSITION

    def toggle(self):
        self.show() if self.is_hidden else self.hide()
