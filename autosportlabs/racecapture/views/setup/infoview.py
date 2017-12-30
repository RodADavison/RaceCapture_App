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

import kivy
kivy.require('1.10.0')
from kivy.clock import Clock
from kivy.app import Builder
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from fieldlabel import FieldLabel
from autosportlabs.racecapture.views.util.alertview import okPopup


INFO_VIEW_KV = """    
<InfoView>:
    AnchorLayout:
        Image:
            allow_stretch: True
            source: root.background_source
        AnchorLayout:
            anchor_y: 'top'
            AnchorLayout:
                size_hint_y: 0.4
                padding: (dp(10), dp(10))
                FieldLabel:
                    on_ref_press: root.on_info_ref(*args)
                    markup: True
                    text_size: self.size
                    font_size: self.height * 0.15
                    text: root.info_text
                    shorten: False
                    valign: 'top'
        AnchorLayout:
            anchor_x: 'right'
            anchor_y: 'bottom'
            padding: (dp(10), dp(10))            
            LabelIconButton:
                id: next
                title: root.next_text
                icon_size: self.height * 0.5
                title_font_size: self.height * 0.6
                icon: root.next_icon
                size_hint_x: None
                width: dp(130)
                size_hint_y: None
                height: dp(50)
                on_release: root.select_next()
                
"""


class InfoView(Screen):
    """
    A base class for setup screens. 
    """
    setup_config = ObjectProperty()
    preset_manager = ObjectProperty()

    next_text = StringProperty('Next')
    next_icon = StringProperty(u'\uf0a9')
    background_source = StringProperty()
    info_text = StringProperty()
    is_last = BooleanProperty(False)
    rc_api = ObjectProperty()
    settings = ObjectProperty()
    rc_config = ObjectProperty()
    track_manager = ObjectProperty()

    Builder.load_string(INFO_VIEW_KV)

    def __init__(self, **kwargs):
        super(InfoView, self).__init__(**kwargs)
        self.register_event_type('on_next')

    def on_info_ref(self, instance, value):
        pass

    def on_pre_enter(self, *args):
        self.ids.next.pulsing = False

    def on_leave(self, *args):
        self.ids.next.pulsing = False

    def on_next(self):
        pass

    def on_is_last(self, instance, value):
        self.next_text = 'Done' if value else 'Next'
        self.next_icon = u'\uf00c' if value else u'\uf0a9'

    def select_next(self):
        self.dispatch('on_next')

    def get_setup_step(self, key):
        if self.setup_config is not None:
            for step in self.setup_config['steps']:
                if step['key'] == key:
                    return step
        return None

    def info_popup(self, msg, callback):
        def done():
            view.dismiss()
            Clock.schedule_once(lambda dt: callback(), 0.25)

        view = ModalView(size_hint=(None, None), size=(dp(600), dp(200)))
        msg = FieldLabel(halign='center', text=msg)
        view.add_widget(msg)
        view.open()
        Clock.schedule_once(lambda dt: done(), 2.0)

    def write_rcp_config(self, info_msg, callback):
        def timeout(dt):
            progress_view.dismiss()
            Clock.schedule_once(lambda dt: callback(), 0.25)

        def write_win(details):
            msg.text += ' Success'
            self.rc_config.stale = False
            Clock.schedule_once(timeout, 1.5)

        def write_fail(details):
            progress_view.dismiss()
            okPopup('Oops!',
                         'We had a problem updating the device. Check the device connection and try again.\n\nError:\n\n{}'.format(details),
                         lambda *args: None)


        progress_view = ModalView(size_hint=(None, None), size=(dp(600), dp(200)))
        msg = FieldLabel(text=info_msg, halign='center')
        progress_view.add_widget(msg)
        progress_view.open()

        self.rc_api.writeRcpCfg(self.rc_config, write_win, write_fail)

