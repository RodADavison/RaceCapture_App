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
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.app import Builder

class BetterButton(Button):
    """An improved button class with customizations we want.
    """
    Builder.load_string("""
<BetterButton>:
    font_name: 'resource/fonts/ASL_regular.ttf'
    font_size: self.height * 0.35
    """)
    def __init__(self, **kwargs):
        super(BetterButton, self).__init__(**kwargs)

class BetterToggleButton(ToggleButton):
    """An improved toggle button class with customizations we want.
    """
    Builder.load_string("""
<BetterToggleButton>:
    font_name: 'resource/fonts/ASL_regular.ttf'
    font_size: self.height * 0.35     
    """)
    def __init__(self, **kwargs):
        super(BetterToggleButton, self).__init__(**kwargs)