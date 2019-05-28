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

from utils import get_color_from_hex

class ColorScheme(object):

    @staticmethod
    def get_alert():
        return get_color_from_hex("FFCC00")

    @staticmethod
    def get_error():
        return get_color_from_hex("E00000")

    @staticmethod
    def get_error_background():
        return get_color_from_hex("FF7F7F")

    @staticmethod
    def get_normal_background():
        return get_color_from_hex("FFFFFF")

    @staticmethod
    def get_happy():
        return get_color_from_hex("00E000")

    @staticmethod
    def get_primary():
        return get_color_from_hex("F44336")

    @staticmethod
    def get_dark_primary():
        return get_color_from_hex("D32F2F")

    @staticmethod
    def get_light_primary():
        return get_color_from_hex("FFCDD2")

    @staticmethod
    def get_accent():
        return get_color_from_hex("00BCD4")

    @staticmethod
    def get_dark_accent():
        return get_color_from_hex("001e23")

    @staticmethod
    def get_medium_accent():
        return get_color_from_hex("006775")

    @staticmethod
    def get_dark_primary_text():
        return get_color_from_hex("313131")

    @staticmethod
    def get_light_primary_text():
        return get_color_from_hex("FFFFFF")

    @staticmethod
    def get_disabled_primary_text():
        return get_color_from_hex("202020")

    @staticmethod
    def get_secondary_text():
        return get_color_from_hex("727272")

    @staticmethod
    def get_divider():
        return get_color_from_hex("B6B6B6")

    @staticmethod
    def get_dark_background():
        return get_color_from_hex("202020")

    @staticmethod
    def get_medium_background():
        return get_color_from_hex("505050")

    @staticmethod
    def get_dark_background_translucent():
        return [0.1, 0.1, 0.1, 0.5]

    @staticmethod
    def get_widget_translucent_background():
        return [0.05, 0.05, 0.05, 0.8]

    @staticmethod
    def get_background():
        return get_color_from_hex("000000")

    @staticmethod
    def get_shadow():
        return [1.0, 1.0, 1.0, 0.2]




