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
import json

class BaseAlertAction(object):
    DEFAULT_COLOR = [1.0, 0.0, 0.0, 1.0]
    def __init__(self):
        self.is_active = False

    def to_json(self):
        '''
        Serialize to a json string
        :return string 
        '''
        return json.dumps(self.to_dict())

"""
Describes an an alert action that specifies a color to activate
"""
class ColorAlertAction(BaseAlertAction):
    PREVIEW_IMAGE = 'resource/alerts/color_alertaction_preview.jpg'
    name = 'color_alertaction'

    def __init__(self, color_rgb, **kwargs):
        super(ColorAlertAction, self).__init__(**kwargs)
        """
        :param array color_rgb: array of R,G,B values
        """
        self.color_rgb = BaseAlertAction.DEFAULT_COLOR if color_rgb is None else color_rgb

    @property
    def title(self):
        return 'Set Gauge Color'

    def to_dict(self):
        '''
        Get dictionary representation of object
        :return dict
        '''
        return {'color_alertaction':{'color':self.color_rgb}}

    def value_equals(self, other):
        if isinstance(other, ColorAlertAction):
            return (self.color_rgb == other.color_rgb)
        return False

    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return ColorAlertAction object
        '''
        return ColorAlertAction.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param d dict representing ColorAlertAction object
        :type d dict
        :return ColorAlertAction object
        '''

        aa = d.get('color_alertaction')
        if aa is None:
            return None

        return ColorAlertAction(color_rgb=aa.get('color', BaseAlertAction.DEFAULT_COLOR))

"""
Describes an alert action that takes the form of a popup message
"""
class PopupAlertAction(ColorAlertAction):
    PREVIEW_IMAGE = 'resource/alerts/popup_alertaction_preview.jpg'
    name = 'popup_alertaction'

    def __init__(self, message, shape=None, color_rgb=None, **kwargs):
        """
        :param string message: The message to display
        :param string shape: the name of the shape to display('triangle', 'octagon'). if None, no shape will be displayed
        :param array color_rgb: array of R,G,B values
        """
        super(PopupAlertAction, self).__init__(color_rgb, **kwargs)
        self.message = message
        self.shape = shape

        # hold the state of when the user will squelch an active popup
        self.is_squelched = False

    @property
    def title(self):
        return 'Popup: "{}"'.format(self.message)


    def to_dict(self):
        '''
        Get dictionary representation of object
        :return dict
        '''
        return {'popup_alertaction':{'message':self.message, 'shape':self.shape, 'color':self.color_rgb}}


    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return PopupAlertAction object
        '''
        return PopupAlertAction.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param d dict representing PopupAlertAction object
        :type d dict
        :return PopupAlertAction object
        '''

        aa = d.get('popup_alertaction')
        if aa is None:
            return None

        return PopupAlertAction(message=aa.get('message', ''),
                                shape=aa.get('shape', None),
                                color_rgb=aa.get('color', BaseAlertAction.DEFAULT_COLOR))

    def value_equals(self, other):
        if isinstance(other, PopupAlertAction):
            return (self.message == other.message and
                    self.shape == other.shape and
                    self.color_rgb == other.color_rgb)
        return False

class LedAlertAction(ColorAlertAction):
    PREVIEW_IMAGE = 'resource/alerts/led_alertaction_preview.jpg'
    name = 'led_alertaction'

    def __init__(self, color_rgb, led_position, flash_rate, **kwargs):
        """
        :param string led_position: The position of the led('left', 'right')
        :param integer flash_rate: The Rate of flash in Hz. 0 = solid (no flash)
        :param array color_rgb: array of R,G,B values
        """
        super(LedAlertAction, self).__init__(color_rgb, **kwargs)
        self.led_position = led_position
        self.flash_rate = flash_rate

    @property
    def title(self):
        return 'Set Alert LED'

    def to_dict(self):
        '''
        Get dictionary representation of object
        :return dict
        '''
        return {'led_alertaction':{'led_position': self.led_position,
                                   'flash_rate': self.flash_rate,
                                   'color':self.color_rgb}}

    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return LedAlertAction object
        '''
        return LedAlertAction.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param d dict representing LedAlertAction object
        :type d dict
        :return LedAlertAction object
        '''

        aa = d.get('led_alertaction')
        if aa is None:
            return None

        return LedAlertAction(led_position=aa.get('led_position', 0),
                                flash_rate=aa.get('flash_rate', 0),
                                color_rgb=aa.get('color', BaseAlertAction.DEFAULT_COLOR))

    def value_equals(self, other):
        if isinstance(other, LedAlertAction):
            return (self.led_position == other.led_position and
                    self.flash_rate == other.flash_rate and
                    self.color_rgb == other.color_rgb)
        return False

class ShiftLightAlertAction(ColorAlertAction):
    PREVIEW_IMAGE = 'resource/alerts/shiftlight_alertaction_preview.jpg'
    name = 'shiftlight_alertaction'

    def __init__(self, color_rgb, flash_rate, **kwargs):
        """
        :param integer flash_rate: The Rate of flash in Hz. 0 = solid (no flash)        
        :param array color_rgb: array of R,G,B values
        """
        super(ShiftLightAlertAction, self).__init__(color_rgb, **kwargs)
        self.flash_rate = flash_rate

    @property
    def title(self):
        return 'Set Shift Light'

    def to_dict(self):
        '''
        Get dictionary representation of object
        :return dict
        '''
        return {'shiftlight_alertaction':{'flash_rate': self.flash_rate,
                                          'color':self.color_rgb}}

    @staticmethod
    def from_json(j):
        '''
        Factory method to create an instance from JSON
        :param j JSON string
        :type j string
        :return ShiftLightAlertAction object
        '''
        return ShiftLightAlertAction.from_dict(json.loads(j))

    @staticmethod
    def from_dict(d):
        '''
        Factory method to create an instance from a dict
        :param d dict representing ShiftLightAlertAction object
        :type d dict
        :return ShiftLightAlertAction object
        '''

        aa = d.get('shiftlight_alertaction')
        if aa is None:
            return None

        return ShiftLightAlertAction(flash_rate=aa.get('flash_rate', 0),
                                color_rgb=aa.get('color', BaseAlertAction.DEFAULT_COLOR))

    def value_equals(self, other):
        if isinstance(other, ShiftLightAlertAction):
            return (self.flash_rate == other.flash_rate and
                    self.color_rgb == other.color_rgb)
        return False

def get_alertaction_default_collection(exclude_filter=[]):
    alertaction_prototypes = [
        PopupAlertAction(message='Alert', shape=None, color_rgb=BaseAlertAction.DEFAULT_COLOR),
        ColorAlertAction(color_rgb=BaseAlertAction.DEFAULT_COLOR),
        ShiftLightAlertAction(flash_rate=0, color_rgb=BaseAlertAction.DEFAULT_COLOR),
        LedAlertAction(led_position='left', flash_rate=0, color_rgb=BaseAlertAction.DEFAULT_COLOR)
        ]

    # filter out items from the exclude_filter
    remove = []
    for aa in alertaction_prototypes:
        for f in exclude_filter:
            if aa.__class__.__name__ == f.__class__.__name__:
                remove.append(aa)

    return [a for a in alertaction_prototypes if a not in remove]

class AlertActionFactory(object):
    factory = {
            ColorAlertAction.name:ColorAlertAction.from_dict,
            PopupAlertAction.name:PopupAlertAction.from_dict,
            LedAlertAction.name:LedAlertAction.from_dict,
            ShiftLightAlertAction.name:ShiftLightAlertAction.from_dict
        }

    @staticmethod
    def create_alertaction_from_dict(name, dict):
        return AlertActionFactory.factory[name](dict)

