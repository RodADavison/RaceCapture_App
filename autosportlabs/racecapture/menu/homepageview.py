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
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.app import Builder
from kivy.metrics import dp
import mainfonts
from utils import kvFind
from autosportlabs.uix.button.featurebutton import FeatureButton

from autosportlabs.widgets.separator import HLineSeparator

HOMPAGE_VIEW_KV = """
<HomePageFeatureButton@FeatureButton>
    title_font: 'resource/fonts/ASL_regular.ttf'
    icon_color: [0.0, 0.0, 0.0, 1.0]
    title_color: [0.2, 0.2, 0.2, 1.0]
    disabled_color: [1.0, 1.0, 1.0, 1.0]
    highlight_color: [0.7, 0.7, 0.7, 1.0]
    
<HomePageView>:
    BoxLayout:
        orientation: 'horizontal'
        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'
            Image:
                size_hint: (0.7, 0.7)
                source: 'resource/images/app_icon_512x512.png'
                nocache: True
        BoxLayout:
            orientation: 'vertical'
            padding: [self.height * 0.05, self.height * 0.05]
            spacing: dp(15)
            HomePageFeatureButton:
                size_hint_y: 0.5
                icon: '\357\203\244'
                title: 'Dashboard'
                on_press: root.show_view('dash')
            BoxLayout:
                orientation: 'horizontal'
                size_hint_y: 0.5
                spacing: dp(15)
                HomePageFeatureButton:
                    icon: '\357\202\200'
                    title: 'Analysis'
                    on_press: root.show_view('analysis')
                HomePageFeatureButton:
                    icon: '\357\202\205'
                    title: 'Setup'
                    on_press: root.show_view('config')

"""

class HomePageView(Screen):
    Builder.load_string(HOMPAGE_VIEW_KV)

    def __init__(self, **kwargs):
        super(HomePageView, self).__init__(**kwargs)
        self.register_event_type('on_select_view')

    def on_select_view(self, viewKey):
        pass

    def show_view(self, viewKey):
        self.dispatch('on_select_view', viewKey)
