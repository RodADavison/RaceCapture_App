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
from iconbutton import TileIconButton
from autosportlabs.racecapture.theme.color import ColorScheme
from kivy.app import Builder
from kivy.core.window import Window
from kivy.properties import ListProperty

class FeatureButton(TileIconButton):
    Builder.load_string("""
<FeatureButton>
    title_font: 'resource/fonts/ASL_regular.ttf'
    icon_color: (0.0, 0.0, 0.0, 1.0)
    title_color: (0.2, 0.2, 0.2, 1.0)
    line_width: 5
    """)

    disabled_color = ListProperty(ColorScheme.get_dark_accent())
    highlight_color = ListProperty(ColorScheme.get_medium_accent())

    def __init__(self, **kwargs):
        super(FeatureButton, self).__init__(**kwargs)
        self.tile_color = (1.0, 1.0, 1.0, 1.0)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        pos = args[1]
        if self.pulsing:
            return

        if self.collide_point(*self.to_widget(*pos)):
            if not self.disabled:
                self.tile_color = self.highlight_color
        else:
            self.tile_color = self.disabled_color

    def on_press(self, *args):
        super(FeatureButton, self).on_press(*args)
        if not self.disabled and not self.pulsing:
            self.tile_color = self.highlight_color

    def on_release(self, *args):
        super(FeatureButton, self).on_release(*args)
        if not self.pulsing:
            self.tile_color = self.disabled_color

    def on_fade_color(self, instance, value):
        self.tile_color = value

    def on_pulsing(self, instance, value):
        self.tile_color = self.highlight_color
        super(FeatureButton, self).on_pulsing(instance, value)

    def on_disabled(self, instance, value):
        super(FeatureButton, self).on_disabled(instance, value)
        self.tile_color = self.disabled_color
