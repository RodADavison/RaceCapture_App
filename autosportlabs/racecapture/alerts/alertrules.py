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

from datetime import datetime

"""
Describes a rule for an individual alert. Defines the sensor channel 
low and high threshold value (inclusive) as well as the timing 
activation / deactivation thresholds used for triggering
"""
import json
from autosportlabs.racecapture.alerts.alertactions import AlertActionFactory

class AlertRule(object):
    RANGE_BETWEEN = '-'
    RANGE_LESS_THAN_EQUAL = '<='
    RANGE_GREATHER_THAN_EQUAL = '>='

    def __init__(self, enabled, range_type, low_threshold, high_threshold, activate_sec=0, deactivate_sec=0, alert_actions=[]):
        """
        :param bool enabled: Set to True if the rule is enabled
        :param string range_type: The type of Range - AlertRule.RANGE_BETWEEN, AlertRule.RANGE_LESS_THAN_EQUAL, AlertRule.RANGE_GREATHER_THAN_EQUAL
        :param float low_threshold: the low range of the threshold
        :param float high_threshold: the high range of the threshold
        :param float activate_sec: the number of seconds before the rule is activated
        :param float deactivate_sec: the number of seconds before the rule is deactivated
        """
        self.enabled = enabled
        self.range_type = range_type
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.activate_sec = activate_sec
        self.deactivate_sec = deactivate_sec
        self.alert_actions = alert_actions

        self.activate_start = None
        self.deactivate_start = None
        self.is_active = False

    def __repr__(self):
        return 'AlertRule: ({}-{}) ({}sec/{}sec) ({})'.format(self.low_threshold, self.high_threshold, self.activate_sec, self.deactivate_sec, 'enabled' if self.enabled else 'disabled')

    def should_activate(self, value, time_ref):
        """ Test for alert activation, sets the is_active property if active
        :param float value: The value to test
        :return: True if the alert rule is activated
        :rtype bool
        """
        if not self.enabled:
            return False

        if not self.is_within_threshold(value):
            self.activate_start = None
            return False

        if not self.activate_start:
            self.activate_start = time_ref
            return False

        return int((time_ref - self.activate_start).total_seconds()) >= self.activate_sec

    def should_deactivate(self, value, time_ref):
        """ Test for alert de-activation
        :param float value: The value to test
        :return: True if the alert rule is de-activated
        :rtype bool
        """
        if not self.enabled:
            return False

        if self.is_within_threshold(value):
            self.deactivate_start = None
            return False

        if not self.deactivate_start:
            self.deactivate_start = time_ref
            return False

        return int((time_ref - self.deactivate_start).total_seconds()) >= self.deactivate_sec

    def is_within_threshold(self, value):
        """ Test if the value is within the alert threshold
        :param float value: The value to test
        :return: True if the value is within the threshold
        :rtype bool 
        """
        if self.range_type == AlertRule.RANGE_BETWEEN:
            return value <= self.high_threshold and value >= self.low_threshold
        elif self.range_type == AlertRule.RANGE_GREATHER_THAN_EQUAL:
            return value >= self.low_threshold
        elif self.range_type == AlertRule.RANGE_LESS_THAN_EQUAL:
            return value <= self.high_threshold
        else:
            return False

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
        alert_actions = []
        for aa in self.alert_actions:
            alert_actions.append(aa.to_dict())

        return {'enabled':self.enabled,
                'range_type': self.range_type,
                'low_threshold': self.low_threshold,
                'high_threshold': self.high_threshold,
                'activate_sec': self.activate_sec,
                'deactivate_sec': self.deactivate_sec,
                'alert_actions': alert_actions}

    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return AlertRule object
        '''
        return AlertRule.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param range_dict dict representing Range object
        :type range_dict dict
        :return AlertRule object
        '''
        alertactions = []
        aa_d = d.get('alert_actions')
        if aa_d is not None:
            for aa in aa_d:
                name = next(iter(aa))
                if name is not None:
                    alertactions.append(AlertActionFactory.create_alertaction_from_dict(name, aa))

        return AlertRule(enabled=d['enabled'],
                         range_type=d['range_type'],
                         low_threshold=d['low_threshold'],
                         high_threshold=d['high_threshold'],
                         activate_sec=d['activate_sec'],
                         deactivate_sec=d['deactivate_sec'],
                         alert_actions=alertactions)

    def value_equals(self, other):
        if isinstance(other, AlertRule):
            return (self.enabled == other.enabled and
                        self.range_type == other.range_type and
                        self.low_threshold == other.low_threshold and
                        self.high_threshold == other.high_threshold and
                        self.activate_sec == other.activate_sec and
                        self.deactivate_sec == other.deactivate_sec and
                        self.alert_actions == self.alert_actions)
        return False

"""
Describes a collection of rules for a specified channel
"""
class AlertRuleCollection(object):
    def __init__(self, channel_name, alert_rules=[]):
        """
        :param string channel_name: The name of the channel the rules will be applied against
        :param bool enabled: True if this rule collection is enabled
        :param array alert_rules: The array of rules to use 
        """
        self.channel_name = channel_name
        self.alert_rules = alert_rules

    def append(self, alertrule):
        self.alert_rules.append(alertrule)

    def check_rules(self, value, time_ref=None):
        """
        Get a set of rules that should be active for the specified value
        :param float value: The value to test
        :return: Array of AlertRules that should be active, Array of AlertRules that should be deactive    
        :rtype array, array
        """
        active_rules = []
        deactive_rules = []

        if time_ref is None:
            time_ref = datetime.now()
        for r in self.alert_rules:
            if r.should_activate(value, time_ref):
                active_rules.append(r)
            if r.should_deactivate(value, time_ref):
                deactive_rules.append(r)

        return active_rules, deactive_rules

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
        alertrules = []
        for ar in self.alert_rules:
            alertrules.append(ar.to_dict())

        return {'channel': self.channel_name, 'alert_rules':alertrules}

    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return AlertRuleCollection object
        '''
        return AlertRuleCollection.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param d dict representing AlertRuleCollection object
        :type d dict
        :return AlertRuleCollection object
        '''

        alertrules = []
        ar_d = d.get('alert_rules')
        if ar_d is not None:
            for ar in ar_d:
                alertrules.append(AlertRule.from_dict(ar))

        return AlertRuleCollection(channel_name=d['channel'], alert_rules=alertrules)
