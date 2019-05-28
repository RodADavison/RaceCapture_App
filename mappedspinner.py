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

from kivy.uix.spinner import Spinner
from kivy import Logger
from kivy.properties import ObjectProperty

class MappedSpinner(Spinner):
    value_map = ObjectProperty()
    def __init__(self, **kwargs):
        self.valueMappings = {}
        self.keyMappings = {}
        self.values = []
        self.defaultValue = ''
        super(MappedSpinner, self).__init__(**kwargs)
        self.register_event_type('on_value')

    def on_value_map(self, instance, value):
        self.setValueMap(value)
        
    def setValueMap(self, valueMap, defaultValue=None, sort_key=None):
        """
        Sets the displayed and actual values for the spinner
        :param valueMap: Dict of value: Display Value items to display
        :param defaultValue: Default value
        :param sort_key: Optional function that will return the actual value to sort on. See
                        https://docs.python.org/2/howto/sorting.html#key-functions
        :return: None
        """
        keyMappings = {}
        values = []
        sortedValues = sorted(valueMap, key=sort_key)
        
        for item in sortedValues:
            values.append(valueMap[item])
            keyMappings[valueMap[item]] = item

        try:
            if defaultValue is None:
                defaultValue = values[0]
        except IndexError:
            defaultValue = ''
            
        self.defaultValue = defaultValue
        self.valueMappings = valueMap
        self.keyMappings = keyMappings
        self.values = values
        self.text = defaultValue

    def setFromValue(self, value):
        self.text = str(self.valueMappings.get(value, self.defaultValue))

    def getValueFromKey(self, key):
        return self.keyMappings.get(key, None)

    def getSelectedValue(self):
        return self.getValueFromKey(self.text)

    def on_value(self, value):
        pass

    def on_text(self, instance, value):
        self.dispatch('on_value', self.getValueFromKey(value))
