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
from autosportlabs.racecapture.views.setup.introview import IntroView
from autosportlabs.racecapture.views.setup.selectdeviceview import SelectDeviceView
from autosportlabs.racecapture.views.setup.selectconnectionview import SelectConnectionView
from autosportlabs.racecapture.views.setup.selectpresetview import SelectPresetView
from autosportlabs.racecapture.views.setup.selecttracksview import SelectTracksView
from autosportlabs.racecapture.views.setup.finishsetupview import FinishSetupView
from autosportlabs.racecapture.views.setup.dashboardsetupview import DashboardSetupView
from autosportlabs.racecapture.views.setup.analysissetupview import AnalysisSetupView
from autosportlabs.racecapture.views.setup.configsetupview import ConfigSetupView
from autosportlabs.racecapture.views.setup.tourview import TourView
from autosportlabs.racecapture.views.setup.podiumview import PodiumSetupView
from autosportlabs.racecapture.views.setup.cellserviceview import CellServiceView

__all__ = 'setup_factory'


def setup_factory(key):
    # Connection type can be overridden by user or for testing purposes
    if key == 'intro':
        return IntroView()
    elif key == 'device':
        return SelectDeviceView()
    elif key == 'connection':
        return SelectConnectionView()
    elif key == 'preset':
        return SelectPresetView()
    elif key == 'tracks':
        return SelectTracksView()
    elif key == 'tour':
        return TourView()
    elif key == 'configsetup':
        return ConfigSetupView()
    elif key == 'dashboard':
        return DashboardSetupView()
    elif key == 'analysis':
        return AnalysisSetupView()
    elif key == 'finish':
        return FinishSetupView()
    elif key == 'podium':
        return PodiumSetupView()
    elif key == 'cellservice':
        return CellServiceView()
    return None
