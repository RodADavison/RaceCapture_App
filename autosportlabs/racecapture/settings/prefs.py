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

from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.config import ConfigParser
from ConfigParser import NoOptionError
from kivy.logger import Logger
import json
import os
from os import path
from os.path import dirname, expanduser, sep
from utils import is_android, is_ios, is_mobile_platform
from copy import copy

class Range(EventDispatcher):
    '''
    Represents a object to manage ranges to facilitate warning / alert functions
    '''
    DEFAULT_WARN_COLOR = [1.0, 0.84, 0.0, 1.0]
    DEFAULT_ALERT_COLOR = [1.0, 0.0, 0.0, 1.0]
    max = NumericProperty(None)
    min = NumericProperty(None)
    color = ListProperty([1.0, 1.0, 1.0, 1.0])

    def __init__(self, minimum=None, maximum=None, **kwargs):
        self.min = minimum
        self.max = maximum
        self.color = kwargs.get('color', self.color)

    def is_in_range(self, value):
        '''
        Query if value is in range
        :param value value to compare
        :type float
        :return bool if value is in range
        '''
        min = self.min
        max = self.max
        return (min is not None and max is not None) and self.min <= value <= self.max

    def to_json(self):
        '''
        Serialize to a json string
        :return string 
        '''
        return json.dumps(self.to_dict())

    def to_dict(self):
        '''
        Get dictionary representation of object
        :return dict
        '''
        return {'min': self.min,
                'max': self.max,
                'color': self.color
                }

    @staticmethod
    def from_json(range_json):
        '''
        Factory method to create an instance from JSON
        :param range_json JSON string
        :type range_json string
        :return Range object
        '''
        range_dict = json.loads(range_json)
        return Range.from_dict(range_dict)

    @staticmethod
    def from_dict(range_dict):
        '''
        Factory method to create an instance from a dict
        :param range_dict dict representing Range object
        :type range_dict dict
        :return Range object
        '''
        return Range(minimum=range_dict['min'], maximum=range_dict['max'], color=range_dict['color'])

class UserPrefs(EventDispatcher):
    '''
    A class to manage user preferences for the RaceCapture app
    '''
    DEFAULT_DASHBOARD_SCREENS = ['5x_gauge_view', 'laptime_view', 'tach_view', 'rawchannel_view']
    DEFAULT_PREFS_DICT = {'range_alerts': {},
                          'gauge_settings':{},
                          'screens':DEFAULT_DASHBOARD_SCREENS}

    DEFAULT_ANALYSIS_CHANNELS = ['Speed']

    prefs_file_name = 'prefs.json'

    def __init__(self, data_dir, user_files_dir, save_timeout=0.2, **kwargs):
        self._prefs_dict = UserPrefs.DEFAULT_PREFS_DICT
        self.config = ConfigParser()
        self.data_dir = data_dir
        self.user_files_dir = user_files_dir
        self.prefs_file = path.join(self.data_dir, self.prefs_file_name)
        self._schedule_save = Clock.create_trigger(self.save, save_timeout)
        self.register_event_type("on_pref_change")
        self.load()

    def on_pref_change(self, section, option, value):
        pass

    def set_range_alert(self, key, range_alert):
        '''
        Sets a range alert with the specified key
        :param key the key for the range alert
        :type string
        :param range_alert the range alert
        :type object
        '''
        self._prefs_dict["range_alerts"][key] = range_alert
        self._schedule_save()

    def get_range_alert(self, key, default=None):
        '''
        Retrives a range alert for the specified key
        :param key the key for the range alert
        :type key string
        :param default the default value, optional
        :type default user specified
        :return the range alert, or the default value 
        '''
        return self._prefs_dict["range_alerts"].get(key, default)

    def set_gauge_config(self, gauge_id, channel):
        '''
        Stores a gauge configuration for the specified gauge_id
        :param gauge_id the key for the gauge
        :type gauge_id string
        :param channel the configuration for the channel
        :type channel object
        '''
        self._prefs_dict["gauge_settings"][gauge_id] = channel
        self._schedule_save()

    def get_gauge_config(self, gauge_id):
        '''
        Get the gauge configuration for the specified gauge_id
        :param gauge_id the key for the gauge
        :type string
        :return the gauge configuration
        '''
        return self._prefs_dict["gauge_settings"].get(gauge_id, False)

    def get_dashboard_screens(self):
        return copy(self._prefs_dict['screens'])

    def set_dashboard_screens(self, screens):
        self._prefs_dict['screens'] = copy(screens)
        self._schedule_save()

# Regular preferences below here

    def get_last_selected_track_id(self):
        return self.get_pref('track_detection', 'last_selected_track_id')

    def get_last_selected_track_timestamp(self):
        return self.get_pref_int('track_detection', 'last_selected_track_timestamp')

    def get_user_cancelled_location(self):
        return self.get_pref('track_detection', 'user_cancelled_location')

    def set_last_selected_track(self, track_id, timestamp, user_cancelled_location='0,0'):
        self.set_pref('track_detection', 'last_selected_track_id', track_id)
        self.set_pref('track_detection', 'last_selected_track_timestamp', timestamp)
        self.set_pref('track_detection', 'user_cancelled_location', user_cancelled_location)
        self._schedule_save()

    @property
    def datastore_location(self):
        return os.path.join(self.data_dir, 'datastore.sq3')

    def save(self, *largs):
        '''
        Saves the current configuration
        '''
        Logger.info('UserPrefs: Saving preferences')
        with open(self.prefs_file, 'w+') as prefs_file:
            data = self.to_json()
            prefs_file.write(data)

    def set_config_defaults(self):
        '''
        Set defaults for preferences 
        '''
        # Base system preferences
        self.config.adddefaultsection('help')
        self.config.adddefaultsection('preferences')
        self.config.setdefault('preferences', 'distance_units', 'miles')
        self.config.setdefault('preferences', 'temperature_units', 'Fahrenheit')
        self.config.setdefault('preferences', 'show_laptimes', 1)
        self.config.setdefault('preferences', 'startup_screen', 'Home Page')
        default_user_files_dir = self.user_files_dir
        self.config.setdefault('preferences', 'config_file_dir', default_user_files_dir)
        self.config.setdefault('preferences', 'export_file_dir', default_user_files_dir)
        self.config.setdefault('preferences', 'firmware_dir', default_user_files_dir)
        self.config.setdefault('preferences', 'import_datalog_dir', default_user_files_dir)
        self.config.setdefault('preferences', 'send_telemetry', '0')
        self.config.setdefault('preferences', 'record_session', '1')
        self.config.setdefault('preferences', 'global_help', True)

        # Connection type for mobile
        if is_mobile_platform():
            if is_android():
                self.config.setdefault('preferences', 'conn_type', 'Bluetooth')
            elif is_ios():
                self.config.setdefault('preferences', 'conn_type', 'WiFi')
        else:
            self.config.setdefault('preferences', 'conn_type', 'Serial')

        # Dashboard preferences
        self.config.adddefaultsection('dashboard_preferences')
        self.config.setdefault('dashboard_preferences', 'last_dash_screen', '5x_gauge_view')
        self.config.setdefault('dashboard_preferences', 'pitstoptimer_enabled', 1)
        self.config.setdefault('dashboard_preferences', 'pitstoptimer_trigger_speed', 5)
        self.config.setdefault('dashboard_preferences', 'pitstoptimer_alert_speed', 25)
        self.config.setdefault('dashboard_preferences', 'pitstoptimer_exit_speed', 55)

        # Track detection pref
        self.config.adddefaultsection('track_detection')
        self.config.setdefault('track_detection', 'last_selected_track_id', 0)
        self.config.setdefault('track_detection', 'last_selected_track_timestamp', 0)
        self.config.setdefault('track_detection', 'user_cancelled_location', '0,0')

        self.config.adddefaultsection('analysis_preferences')
        self.config.setdefault('analysis_preferences', 'selected_sessions_laps', '{"sessions":{}}')
        self.config.setdefault('analysis_preferences', 'selected_analysis_channels', ','.join(UserPrefs.DEFAULT_ANALYSIS_CHANNELS))

        self.config.adddefaultsection('setup')
        self.config.setdefault('setup', 'setup_enabled', 1)
        self._schedule_save()

    def load(self):
        Logger.info('UserPrefs: Data Dir is: {}'.format(self.data_dir))
        self.config.read(os.path.join(self.data_dir, 'preferences.ini'))
        self.set_config_defaults()

        try:
            with open(self.prefs_file, 'r') as data:
                content = data.read()
                content_dict = json.loads(content)

                if content_dict.has_key("range_alerts"):
                    for name, settings in content_dict["range_alerts"].iteritems():
                        self._prefs_dict["range_alerts"][name] = Range.from_dict(settings)

                if content_dict.has_key("gauge_settings"):
                    for id, channel in content_dict["gauge_settings"].iteritems():
                        self._prefs_dict["gauge_settings"][id] = channel

                if content_dict.has_key('screens'):
                    self._prefs_dict['screens'] = content_dict['screens']

        except Exception:
            pass

    def init_pref_section(self, section):
        '''
        Initializes a preferences section with the specified name. 
        if the section already exists, there is no effect. 
        :param section the name of the preference section
        :type string
        '''
        self.config.adddefaultsection(section)

    def get_pref_bool(self, section, option, default=None):
        '''
        Retrieve a preferences value as a bool. 
        return default value if preference does not exist
        :param section the configuration section for the preference
        :type section string
        :param option the option for the section
        :type option string
        :param default
        :type default bool
        :return bool preference value
        '''
        try:
            return self.config.getboolean(section, option)
        except (NoOptionError, ValueError):
            return default

    def get_pref_float(self, section, option, default=None):
        '''
        Retrieve a preferences value as a float. 
        return default value if preference does not exist
        :param section the configuration section for the preference
        :type section string
        :param option the option for the section
        :type option string
        :param default
        :type default float
        :return float preference value
        '''
        try:
            return self.config.getfloat(section, option)
        except (NoOptionError, ValueError):
            return default

    def get_pref_int(self, section, option, default=None):
        '''
        Retrieve a preferences value as an int. 
        return default value if preference does not exist
        :param section the configuration section for the preference
        :type section string
        :param option the option for the section
        :type option string
        :param default
        :type default user specified
        :return int preference value
        '''
        try:
            return self.config.getint(section, option)
        except (NoOptionError, ValueError):
            return default

    def get_pref(self, section, option, default=None):
        '''
        Retrieve a preferences value as a string. 
        return default value if preference does not exist
        :param section the configuration section for the preference
        :type section string
        :param option the option for the section
        :type option string
        :param default
        :type default user specified
        :return string preference value
        '''
        try:
            return self.config.get(section, option)
        except (NoOptionError, ValueError):
            return default

    def get_pref_list(self, section, option, default=[]):
        """
        Retrieve a preferences value as a list. 
        return default value if preference does not exist
        :param section the configuration section for the preference
        :type section string
        :param option the option for the section
        :type option string
        :param default
        :type default user specified
        :return list of string values
        """
        try:
            return self.config.get(section, option).split(',')
        except (NoOptionError, ValueError):
            return default

    def set_pref(self, section, option, value):
        '''
        Set a preference value
        :param section the configuration section for the preference
        :type string
        :param option the option for the section
        :type string
        :param value the preference value to set
        :type value user specified
        '''
        current_value = None
        try:
            current_value = self.config.get(section, option)
        except NoOptionError:
            pass
        self.config.set(section, option, value)
        self.config.write()
        if value != current_value:
            self.dispatch('on_pref_change', section, option, value)

    def set_pref_list(self, section, option, value):
        """
        Set a preference value by list
        :param section the configuration section for the preference
        :type string
        :param option the option for the section
        :type string
        :param value the preference value to set
        :type value list (list of strings)
        """
        try:
            self.set_pref(section, option, ','.join(value))
        except TypeError:
            Logger.error('UserPrefs: failed to set preference list for {}:{} - {}'.format(section, option, value))

    def to_json(self):
        '''
        Serialize preferences to json
        '''
        data = {'range_alerts': {}, 'gauge_settings':{}, 'screens': []}

        for name, range_alert in self._prefs_dict["range_alerts"].iteritems():
            data["range_alerts"][name] = range_alert.to_dict()

        for id, channel in self._prefs_dict["gauge_settings"].iteritems():
            data["gauge_settings"][id] = channel

        data['screens'] = self._prefs_dict['screens']

        return json.dumps(data)
