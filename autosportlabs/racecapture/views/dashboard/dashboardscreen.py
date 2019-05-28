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
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty
from utils import kvFindClass
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge

class DashboardScreen(AnchorLayout):
    """
    A base class to for all dashboard screens.
    """
    name = StringProperty()

    def on_enter(self):
        """
        Called when the screen is shown. 
        """
        gauges = list(kvFindClass(self, Gauge))
        for gauge in gauges:
            gauge.visible = True

    def on_exit(self):
        """
        Called when the screen is hidden. 
        """
        gauges = list(kvFindClass(self, Gauge))
        for gauge in gauges:
            gauge.visible = False

