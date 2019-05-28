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
from kivy.uix.behaviors.button import ButtonBehavior
kivy.require('1.10.0')

from kivy.uix.label import Label
from kivy.metrics import sp
from kivy.app import Builder
from kivy.clock import Clock
from kivy.logger import Logger

class FieldLabel(Label):
    def __init__(self, **kwargs):
        super(FieldLabel, self).__init__(**kwargs)
        self.bind(width=self.width_changed)
        self.spacing = (20, 3)
        self.font_name = "resource/fonts/ASL_regular.ttf"
        self.font_size = sp(20)
        self.shorten = True
        self.shorten_from = 'right'

    def width_changed(self, instance, size):
        self.text_size = (size, None)

class ClickFieldLabel(ButtonBehavior, FieldLabel):
    pass

class AutoShrinkFieldLabel(Label):
    Builder.load_string("""
<AutoShrinkFieldLabel>:
    _scale: 1. if self.texture_size[0] < self.width else float(self.width) / max(self.texture_size[0], 1)
    canvas.before:
        PushMatrix
        Scale:
            origin: self.center
            x: self._scale or 1.
            y: self._scale or 1.
    canvas.after:
        PopMatrix
    font_name: "resource/fonts/ASL_regular.ttf"
""")
