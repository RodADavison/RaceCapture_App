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

from autosportlabs.racecapture.alerts.alertactions import *

class BaseAlertActionController(object):

    @classmethod
    def new_instance(cls, dashboard_state):
        return cls(dashboard_state=dashboard_state)

    def __init__(self, dashboard_state, **kwargs):
        self.dashboard_state = dashboard_state

    def activate(self, alertaction, channel):
        pass

    def deactivate(self, alertaction, channel):
        pass


class ColorAlertActionController(BaseAlertActionController):

    def __init__(self, dashboard_state, **kwargs):
        super(ColorAlertActionController, self).__init__(dashboard_state, **kwargs)

    def activate(self, alertaction, channel):
        self.dashboard_state.set_channel_color(channel, alertaction)

    def deactivate(self, alertaction, channel):
        self.dashboard_state.clear_channel_color(channel, alertaction)


class PopupAlertActionController(BaseAlertActionController):

    def __init__(self, dashboard_state, **kwargs):
        super(PopupAlertActionController, self).__init__(dashboard_state, **kwargs)

    def activate(self, alertaction, channel):
        # reset if alert was previously squelched, so it pops up again
        alertaction.is_squelched = False
        self.dashboard_state.set_popupalert(channel, alertaction)

    def deactivate(self, alertaction, channel):
        self.dashboard_state.clear_popupalert(channel, alertaction)


class LedAlertActionController(BaseAlertActionController):

    def __init__(self, dashboard_state, **kwargs):
        super(LedAlertActionController, self).__init__(dashboard_state, **kwargs)


class ShiftLightAlertActionController(BaseAlertActionController):

    def __init__(self, dashboard_state, **kwargs):
        super(ShiftLightAlertActionController, self).__init__(dashboard_state, **kwargs)


class AlertActionControllerFactory(BaseAlertActionController):
    factory = {
            ColorAlertAction.__name__:ColorAlertActionController.new_instance,
            PopupAlertAction.__name__:PopupAlertActionController.new_instance,
            LedAlertAction.__name__:LedAlertActionController.new_instance,
            ShiftLightAlertAction.__name__:ShiftLightAlertActionController.new_instance
        }

    @staticmethod
    def create_controller(alertaction, dashboard_state):
        return AlertActionControllerFactory.factory[alertaction.__class__.__name__](dashboard_state)
