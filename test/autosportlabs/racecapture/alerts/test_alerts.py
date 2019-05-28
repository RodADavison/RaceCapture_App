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

import unittest
import time
from datetime import datetime, timedelta
from autosportlabs.racecapture.alerts.alertrules import AlertRule, AlertRuleCollection
from autosportlabs.racecapture.alerts.alertactions import *


class AlertRuleTest(unittest.TestCase):

    def test_activate_deactivate(self):
        ar = AlertRule(True, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)

        timeref = datetime.now()
        self.assertFalse(ar.should_activate(100, timeref))
        timeref += timedelta(seconds=2)
        self.assertTrue(ar.should_activate(100, timeref))


        self.assertFalse(ar.should_activate(90, timeref))
        self.assertFalse(ar.should_deactivate(90, timeref))
        # should still be active

        # wait until the deactivate threhold is tripped
        timeref += timedelta(seconds=2)
        self.assertFalse(ar.should_activate(90, timeref))
        self.assertTrue(ar.should_deactivate(90, timeref))

    def test_enabled_disabled(self):
        # Test activating a disabled rule
        ar = AlertRule(False, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)
        timeref = datetime.now()
        self.assertFalse(ar.should_activate(100, timeref))
        timeref += timedelta(seconds=2)
        self.assertFalse(ar.should_activate(100, timeref))

        # Test disabling after it's been activated
        ar2 = AlertRule(True, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)
        self.assertFalse(ar2.should_activate(100, timeref))
        timeref += timedelta(seconds=2)
        self.assertTrue(ar2.should_activate(100, timeref))
        ar2.enabled = False

    def test_within_threshold(self):
        ar = AlertRule(True, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)
        self.assertTrue(ar.is_within_threshold(100))
        self.assertTrue(ar.is_within_threshold(150))
        self.assertTrue(ar.is_within_threshold(200))

        self.assertFalse(ar.is_within_threshold(99))
        self.assertFalse(ar.is_within_threshold(201))

        ar.range_type = AlertRule.RANGE_LESS_THAN_EQUAL
        self.assertTrue(ar.is_within_threshold(5))
        self.assertTrue(ar.is_within_threshold(200))
        self.assertFalse(ar.is_within_threshold(300))

        ar.range_type = AlertRule.RANGE_GREATHER_THAN_EQUAL
        self.assertFalse(ar.is_within_threshold(50))
        self.assertTrue(ar.is_within_threshold(100))
        self.assertTrue(ar.is_within_threshold(300))


class AlertRuleCollectionTest(unittest.TestCase):

    def test_alert_single(self):
        ar = AlertRule(True, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)
        arc = AlertRuleCollection("RPM", [ar])

        timeref = datetime.now()
        active, deactive = arc.check_rules(50, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive, [])

        timeref += timedelta(seconds=2)

        active, deactive = arc.check_rules(50, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive[0], ar)
        self.assertEqual(len(deactive), 1)

        active, deactive = arc.check_rules(150, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive, [])

        timeref += timedelta(seconds=2)

        active, deactive = arc.check_rules(150, timeref)
        self.assertEqual(active[0], ar)
        self.assertEqual(len(active), 1)
        self.assertEqual(deactive, [])

        timeref += timedelta(seconds=2)

        active, deactive = arc.check_rules(250, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive, [])

        timeref += timedelta(seconds=2)

        active, deactive = arc.check_rules(250, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive[0], ar)
        self.assertEqual(len(deactive), 1)

    def test_alert_multiple(self):
        ar1 = AlertRule(True, AlertRule.RANGE_BETWEEN, 100, 200, 1, 1)
        ar2 = AlertRule(True, AlertRule.RANGE_BETWEEN, 300, 400, 1, 1)
        ar3 = AlertRule(True, AlertRule.RANGE_BETWEEN, 500, 600, 1, 1)
        arc = AlertRuleCollection("RPM", [ar1, ar2, ar3])

        timeref = datetime.now()
        active, deactive = arc.check_rules(50, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive, [])

        timeref += timedelta(seconds=2)
        active, deactive = arc.check_rules(50, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive[0], ar1)
        self.assertEqual(deactive[1], ar2)
        self.assertEqual(deactive[2], ar3)
        self.assertEqual(len(deactive), 3)

        active, deactive = arc.check_rules(100, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive[0], ar2)
        self.assertEqual(deactive[1], ar3)
        self.assertEqual(len(deactive), 2)

        timeref += timedelta(seconds=2)
        active, deactive = arc.check_rules(100, timeref)
        self.assertEqual(active[0], ar1)
        self.assertEqual(len(active), 1)
        self.assertEqual(deactive[0], ar2)
        self.assertEqual(deactive[1], ar3)
        self.assertEqual(len(deactive), 2)

        active, deactive = arc.check_rules(300, timeref)
        self.assertEqual(active, [])
        self.assertEqual(deactive[0], ar3)
        self.assertEqual(len(deactive), 1)

        timeref += timedelta(seconds=2)
        active, deactive = arc.check_rules(300, timeref)
        self.assertEqual(active[0], ar2)
        self.assertEqual(len(active), 1)
        self.assertEqual(deactive[0], ar1)
        self.assertEqual(deactive[1], ar3)
        self.assertEqual(len(deactive), 2)


    def test_serialize(self):

        actions1 = get_alertaction_default_collection()
        rules = [AlertRule(enabled=True, range_type=AlertRule.RANGE_BETWEEN, low_threshold=1, high_threshold=2, activate_sec=3, deactivate_sec=4, alert_actions=actions1)]
        arc = AlertRuleCollection(channel_name='RPM', alert_rules=rules)
        # serialize to and from JSON
        arc2 = AlertRuleCollection.from_json(arc.to_json())

        self.assertEqual(arc2.channel_name, arc.channel_name)

        rules2 = arc2.alert_rules
        rules_len = len(rules)

        for i in range (0, rules_len):
            r1 = rules[i]
            r2 = rules2[i]
            self.assertTrue(r1.value_equals(r2))

def main():
    unittest.main()

if __name__ == "__main__":
    main()
