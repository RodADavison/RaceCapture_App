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
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.app import Builder
from kivy.properties import StringProperty
from kivy.clock import Clock

__all__ = ('format_laptime', 'clock_sequencer', 'autoformat_number')

NULL_LAP_TIME = '--:--.---'
MIN_LAP_TIME = 0

def format_laptime(time):
    if time == None:
        return NULL_LAP_TIME

    int_minute_value = int(time)
    fraction_minute_value = 60.0 * (time - float(int_minute_value))
    if time == MIN_LAP_TIME:
        return NULL_LAP_TIME
    else:
        return '{}:{}'.format(int_minute_value, '{0:05.2f}'.format(fraction_minute_value))

def clock_sequencer(items, start_delay=0.2, spread=0.2):
    start = start_delay
    for i in items:
        Clock.schedule_once(i, start)
        start += spread

def autoformat_number(value):
    return str(int(value)) if value == int(value) else str(value)
