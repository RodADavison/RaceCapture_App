import kivy
kivy.require('1.8.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.metrics import dp
from kivy.graphics import Color
from utils import kvFind
from fieldlabel import FieldLabel
from kivy.properties import BoundedNumericProperty, ObjectProperty, BooleanProperty, StringProperty
from autosportlabs.racecapture.views.dashboard.widgets.gauge import Gauge
Builder.load_file('autosportlabs/racecapture/views/dashboard/widgets/timedelta.kv')

MIN_TIME_DELTA  = -99.0
MAX_TIME_DELTA  = 99.0

DEFAULT_AHEAD_COLOR  = [1.0, 0.0 , 1.0, 1.0]
DEFAULT_BEHIND_COLOR = [1.0, 0.65, 0.0 ,1.0]

class TimeDelta(Gauge):
    NULL_TIME_DELTA = '--.-'    
    ahead_color = ObjectProperty(DEFAULT_AHEAD_COLOR)
    behind_color = ObjectProperty(DEFAULT_BEHIND_COLOR)
    halign = StringProperty(None)
    
    def __init__(self, **kwargs):
        super(TimeDelta, self).__init__(**kwargs)
    
    def on_value(self, instance, value):
        view = self.valueView
        if value == None:
            view.text = NULL_TIME_DELTA
        else:
            railedValue = value
            railedValue = MIN_TIME_DELTA if railedValue < MIN_TIME_DELTA else railedValue
            railedvalue = MAX_TIME_DELTA if railedValue > MAX_TIME_DELTA else railedValue
            self.valueView.text = '{0:+1.1f}'.format(float(railedValue))
        self.update_delta_color()

    def update_delta_color(self):
        self.valueView.color = self.ahead_color if self.value <= 0 else self.behind_color
        
    def on_halign(self, instance, value):
        self.valueView.halign = value 
        
    def on_touch_down(self, touch, *args):
        pass

    def on_touch_move(self, touch, *args):
        pass

    def on_touch_up(self, touch, *args):
        pass
        
        