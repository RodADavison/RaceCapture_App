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
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.app import Builder
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from fieldlabel import FieldLabel
from kivy.uix.screenmanager import Screen
from autosportlabs.racecapture.views.setup.infoview import InfoView
from autosportlabs.uix.button.betterbutton import BetterToggleButton
from kivy.properties import ObjectProperty, StringProperty
from autosportlabs.racecapture.presets.presetview import PresetItemView

class SelectPresetView(InfoView):
    """
    A setup screen that lets users select what device they have.
    """
    Builder.load_string("""
<SelectPresetView>:
    background_source: 'resource/setup/background_blank.png'
    info_text: 'Select a preset'
    BoxLayout:
        orientation: 'vertical'
        padding: (0, dp(20))
        spacing: (0, dp(10))
        BoxLayout:
            size_hint_y: 0.12
        ScrollContainer:
            canvas.before:
                Color:
                    rgba: ColorScheme.get_dark_background()
                Rectangle:
                    pos: self.pos
                    size: self.size        
            do_scroll_x: False
            do_scroll_y: True
            size_hint_y: 1
            size_hint_x: 1
            GridLayout:
                id: presets
                spacing: [0, dp(10)]
                row_default_height: dp(130)
                size_hint_y: None
                height: self.minimum_height
                cols: 1
        BoxLayout:
            size_hint_y: None
            height: dp(50)
    """)

    def __init__(self, **kwargs):
        super(SelectPresetView, self).__init__(**kwargs)
        self.ids.next.disabled = True
        self.ids.next.pulsing = False
        self.preset_selected = False

    def on_setup_config(self, instance, value):
        self._update_ui()

    def _update_ui(self):
        self.ids.presets.clear_widgets()
        device_step = self.get_setup_step('device')
        device = device_step.get('device')
        self.ids.next.disabled = False

        # get the device prefix
        device = device.split('_')[0]
        presets = self.preset_manager.get_presets_by_type(device)

        if presets is None:
            self.select_next()
            return

        for k, v in presets:
            name = v.name
            notes = v.notes
            self.add_preset(k, v)

    def add_preset(self, key, preset):
        view = PresetItemView(preset_id=preset.mapping_id,
                                                   name=preset.name,
                                                   notes=preset.notes,
                                                   image_path=preset.local_image_path)
        view.bind(on_preset_selected=self._preset_selected)
        self.ids.presets.add_widget(view)

    def _preset_selected(self, instance, preset_id):
        def preset_selected():
            self.preset_selected = True
            self.ids.next.pulsing = True
            self.ids.next.disabled = False

        self.ids.next.disabled = True
        preset = self.preset_manager.get_preset_by_id(preset_id)
        self.rc_config.fromJson(preset.mapping)
        self.rc_config.stale = True
        self.write_rcp_config('Applying preset {} ... '.format(preset.name), preset_selected)

    def select_next(self):
        def do_next():
            super(SelectPresetView, self).select_next()

        if not self.preset_selected:
            self.info_popup('You can configure presets later under Setup', do_next)
            return

        do_next()

