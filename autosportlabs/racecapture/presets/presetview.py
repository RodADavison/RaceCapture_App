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
import os
from kivy.metrics import dp
from kivy.app import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import SpinnerOption
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.logger import Logger
from kivy.uix.anchorlayout import AnchorLayout
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from iconbutton import IconButton
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.theme.color import ColorScheme

class PresetUpdateStatusView(BoxLayout):
    Builder.load_string("""
<PresetUpdateStatusView>:
    orientation: 'vertical'
    ProgressBar:
        value: root.progress_value
    Label:
        text: root.update_msg
    """)
    progress_value = NumericProperty()
    update_msg = StringProperty()
    def __init__(self, **kwargs):
        super(PresetUpdateStatusView, self).__init__(**kwargs)

    def _update_progress(self, percent):
        self.progress_value = percent

    def _update_message(self, message):
        self.update_msg = message

    def on_progress(self, count=None, total=None, message=None):
        if count and total:
            progress_percent = (float(count) / float(total) * 100)
            Clock.schedule_once(lambda dt: self._update_progress(progress_percent))
        if message:
            Clock.schedule_once(lambda dt: self._update_message(message))

    def on_message(self, message):
        self.update_msg = message

class PresetItemView(AnchorLayout):
    Builder.load_string("""
<PresetItemView>:
    canvas.before:
        Color:
            rgba: 0.0, 0.0, 0.0, 1
        Rectangle:
            pos: self.pos
            size: self.size             
    size_hint_y: None
    height: dp(210)
    BoxLayout:
        orientation: 'horizontal'
        AnchorLayout:
            Image:
                source: root.image_path
                allow_stretch: True
                size_hint_y: None
                height: dp(150)

        AnchorLayout:
            anchor_x: 'center'
            anchor_y: 'center'
            size_hint_x: None
            width: dp(190)
            LabelIconButton:
                size_hint: (None, None)
                size: (dp(130), dp(50))
                pos_hint: (0.5,0.5)
                id: load_preset
                title: 'Select'
                icon_size: self.height * 0.7
                title_font_size: self.height * 0.5
                icon: u'\uf046'
                on_press: root.select_preset()
        Widget:
            size_hint_x: None
            width: dp(10)
    AnchorLayout:
        anchor_y: 'top'
        FieldLabel:
            size_hint_y: 0.1
            text: root.name
            font_size: dp(30)

    AnchorLayout:
        anchor_y: 'bottom'
        BoxLayout:
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 0.7
                Rectangle:
                    pos: self.pos
                    size: self.size
            size_hint_y: 0.3
            FieldLabel:
                font_size: dp(20)
                halign: 'left'
                text: '' if root.notes is None else root.notes
""")

    preset_id = NumericProperty()
    name = StringProperty()
    notes = StringProperty(allownone=True)
    image_path = StringProperty()
    def __init__(self, **kwargs):
        super(PresetItemView, self).__init__(**kwargs)
        self.register_event_type('on_preset_selected')

    def select_preset(self):
        self.dispatch('on_preset_selected', self.preset_id)

    def on_preset_selected(self, preset_id):
        pass

class PresetBrowserView(BoxLayout):
    Builder.load_string("""
<PresetBrowserView>:
    orientation: 'vertical'
    spacing: dp(5)
    ScrollContainer:
        size_hint_y: 0.85
        canvas.before:
            Color:
                rgba: 0.05, 0.05, 0.05, 1
            Rectangle:
                pos: self.pos
                size: self.size
        id: scroller
        size_hint_y: 0.95
        do_scroll_x:False
        do_scroll_y:True
        GridLayout:
            id: preset_grid
            spacing: [dp(10), dp(10)]
            size_hint_y: None
            height: max(self.minimum_height, scroller.height)
            cols: 1
    AnchorLayout:
        anchor_x: 'right'
        size_hint_y: None
        height: dp(30)
        LabelIconButton:
            size_hint_x: None
            width: dp(120)
            id: updatecheck
            disabled: True
            title: 'Update'
            icon: '\357\203\255'
            on_press: root._on_update_check()
    IconButton:
        size_hint_y: 0.15
        text: u'\uf00d'
        on_press: root.on_close()
""")

    def __init__(self, preset_manager, preset_type, **kwargs):
        super(PresetBrowserView, self).__init__(**kwargs)
        self.register_event_type('on_preset_close')
        self.register_event_type('on_preset_selected')
        self.preset_manager = preset_manager
        self.preset_type = preset_type
        self.init_view()

    def on_preset_close(self):
        pass

    def on_preset_selected(self, preset_id):
        pass

    def init_view(self):
        self.refresh_view()

    def set_view_disabled(self, disabled):
        self.ids.updatecheck.disabled = disabled

    def _on_update_check(self):

        def on_update_check_success():
            def _success():
                # do this in the UI thread
                popup.content.on_message('Processing...')
                Clock.schedule_once(lambda dt: self.refresh_view())
                popup.dismiss()
            Clock.schedule_once(lambda dt: _success())

        def on_update_check_error(details):
            def _error(details):
                # do this in the UI thread
                popup.dismiss()
                Clock.schedule_once(lambda dt: self.refresh_view())
                Logger.error('PresetBrowserView: Error updating: {}'.format(details))
                alertPopup('Error Updating', 'There was an error updating the presets.\n\nPlease check your network connection and try again')
            Clock.schedule_once(lambda dt: _error(details))

        self.set_view_disabled(True)
        update_view = PresetUpdateStatusView()
        popup = Popup(title='Checking for updates', content=update_view, auto_dismiss=False, size_hint=(None, None), size=(dp(400), dp(200)))
        popup.open()

        self.preset_manager.refresh(update_view.on_progress, on_update_check_success, on_update_check_error)

    def refresh_view(self):
        self.ids.preset_grid.clear_widgets()
        for k, v in self.preset_manager.get_presets_by_type(self.preset_type):
            name = v.name
            notes = v.notes
            self.add_preset(k, name, notes)
        self.set_view_disabled(False)

    def add_preset(self, preset_id, name, notes):
        preset = self.preset_manager.get_preset_by_id(preset_id)
        if preset:
            preset_view = PresetItemView(preset_id=preset_id, name=name, notes=notes, image_path=preset.local_image_path)
            preset_view.bind(on_preset_selected=self.preset_selected)
            self.ids.preset_grid.add_widget(preset_view)

    def preset_selected(self, instance, preset_id):
        self.dispatch('on_preset_selected', preset_id)
        self.dispatch('on_preset_close')

    def on_close(self, *args):
        self.dispatch('on_preset_close')
