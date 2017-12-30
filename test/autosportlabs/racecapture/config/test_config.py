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
import json
from autosportlabs.racecapture.config.rcpconfig import VersionConfig


class SampleDataTest(unittest.TestCase):

    def test_version_info(self):
        version_config = VersionConfig()

        self.assertFalse(version_config.is_valid)

        version_config.name = 'RCP_MK2'
        version_config.major = '3'
        version_config.serial = '123456'
        version_config.friendlyName = 'RaceCapture/Pro MK2'

        self.assertTrue(version_config.is_valid)

def main():
    unittest.main()

if __name__ == "__main__":
    main()
