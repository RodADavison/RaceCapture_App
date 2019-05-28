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

from autosportlabs.racecapture.alerts.alertcontrollers import AlertActionControllerFactory

class AlertEngine(object):

    def __init__(self, dashboard_state, **kwargs):
        self.dashboard_state = dashboard_state
        # Map of AlertRuleCollection by channel name

        self.alert_controllers = {}

    def send_api_msg(self, *args):
        # NOOP
        pass

    def process_rules(self, alertrules, channel, value):

        if alertrules is None:
            return

        # check what might be activated or deactivated
        active_rules, deactive_rules = alertrules.check_rules(value)

        for rule in deactive_rules:
            for alertaction in rule.alert_actions:
                if alertaction.is_active:
                    # disable the action once
                    controller = self._get_alert_controller(self.dashboard_state, alertaction)
                    controller.deactivate(alertaction, channel)
                    alertaction.is_active = False

        for rule in active_rules:
            for alertaction in rule.alert_actions:
                if not alertaction.is_active:
                    # trigger the action once
                    controller = self._get_alert_controller(self.dashboard_state, alertaction)
                    controller.activate(alertaction, channel)
                    alertaction.is_active = True


    def _get_alert_controller(self, dashboard_state, alertaction):
        name = alertaction.__class__.__name__
        controller = self.alert_controllers.get(name)
        if controller is None:
            controller = AlertActionControllerFactory.create_controller(alertaction, dashboard_state)
            self.alert_controllers[name] = controller

        return controller

