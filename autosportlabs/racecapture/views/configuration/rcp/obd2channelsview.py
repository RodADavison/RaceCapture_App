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
from kivy.uix.boxlayout import BoxLayout
from kivy.app import Builder
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from settingsview import SettingsSwitch
from iconbutton import IconButton
from autosportlabs.help.helpmanager import HelpInfo
from autosportlabs.racecapture.views.configuration.baseconfigview import BaseConfigView
from autosportlabs.racecapture.views.configuration.rcp.canmappingview import CANChannelConfigView, CANChannelMappingTab
from autosportlabs.racecapture.presets.presetview import PresetBrowserView
from autosportlabs.racecapture.data.unitsconversion import UnitsConversionFilters
from autosportlabs.uix.layout.sections import SectionBoxLayout
from autosportlabs.racecapture.views.util.alertview import editor_popup, confirmPopup, choicePopup
from autosportlabs.racecapture.OBD2.obd2settings import OBD2Settings
from autosportlabs.racecapture.views.util.viewutils import clock_sequencer
from utils import *
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.util.alertview import alertPopup
import copy

class PIDConfigTab(CANChannelMappingTab):
    PID_MIN = 0
    PID_MAX = 0xFFFFFFFF
    SUPPORTED_MODES = {1:'01h', 2:'02h', 3:'03h', 4:'04h', 5:'05h', 9:'09h', 34:'22h'}
    DEFAULT_MODE = '01h'

    Builder.load_string("""
<PIDConfigTab>:
    text: 'OBDII PID'
    BoxLayout:
        AnchorLayout:
            size_hint_x: 0.55
            BoxLayout:
                spacing: dp(5)
                orientation: 'vertical'
                SectionBoxLayout:
                    FieldLabel:
                        text: 'OBDII PID'
                        halign: 'right'
                    LargeIntegerValueField:
                        id: pid
                        on_text: root.on_pid(*args)
                SectionBoxLayout:
                    FieldLabel:
                        text: 'Mode'
                        halign: 'right'
                        id: mode
                    LargeMappedSpinner:
                        id: mode
                        on_text: root.on_mode(*args)
        
        BoxLayout:
            size_hint_x: 0.45
            orientation: 'vertical'
            SectionBoxLayout:
                orientation: 'horizontal'
                FieldLabel:
                    size_hint_x: 0.7
                    text: 'Passive Mode'
                    halign: 'right'
                CheckBox:
                    id: passive
                    size_hint_x: 0.3                
                    on_active: root.on_passive(*args)
            SectionBoxLayout:
                orientation: 'horizontal'
                FieldLabel:
                    size_hint_x: 0.7
                    text: '29 bit mode'
                    halign: 'right'
                CheckBox:
                    id: mode29bit
                    size_hint_x: 0.3                
                    on_active: root.on_29bit(*args)

    """)

    def __init__(self, **kwargs):
        super(PIDConfigTab, self).__init__(**kwargs)
        self._loaded = False

    def init_view(self, channel_cfg):
        self._loaded = False
        self.channel_cfg = channel_cfg

        self.ids.mode.setValueMap(PIDConfigTab.SUPPORTED_MODES, PIDConfigTab.DEFAULT_MODE)
        self.ids.mode.setFromValue(channel_cfg.mode)
        self.ids.pid.text = str(channel_cfg.pid)
        self.ids.passive.active = channel_cfg.passive
        self.ids.mode29bit.active = channel_cfg.mapping.can_id == PidConfig.OBDII_MODE_29_BIT_CAN_ID_RESPONSE
        self._loaded = True

    def on_pid(self, instance, value):
        if not self._loaded:
            return
        try:
            value = int(value)
            if value < PIDConfigTab.PID_MIN or value > PIDConfigTab.PID_MAX:
                raise ValueError
            self.channel_cfg.pid = int(value)
        except ValueError:
            instance.text = str(self.channel_cfg.pid)

    def on_mode(self, instance, value):
        if self._loaded:
            self.channel_cfg.mode = instance.getValueFromKey(value)

    def on_passive(self, instance, value):
        if self._loaded:
            self.channel_cfg.passive = instance.active

    def on_29bit(self, instance, value):
        if self._loaded:
            self.channel_cfg.mapping.can_id = PidConfig.OBDII_MODE_29_BIT_CAN_ID_RESPONSE if value == True else PidConfig.OBDII_MODE_11_BIT_CAN_ID_RESPONSE

class OBD2ChannelConfigView(CANChannelConfigView):
    def __init__(self, obd2_preset_settings, is_new, mapping_capable, **kwargs):
        self._current_channel_config = None
        self._is_new = is_new
        self._mapping_capable = mapping_capable
        self.obd2_preset_settings = obd2_preset_settings
        self.pid_config_tab = PIDConfigTab()
        super(OBD2ChannelConfigView, self).__init__(**kwargs)
        self.can_channel_customization_tab.set_channel_filter_list(obd2_preset_settings.getChannelNames())

    def on_channel_selected(self, instance, channel_cfg):
        name = channel_cfg.name
        obd2_preset = self.obd2_preset_settings.obd2channelInfo.get(name)
        if obd2_preset is None:
            return

        # was the existing channel ever customized? this test will determine if the original channel
        # still matches the original preset
        matching_existing_preset = self.obd2_preset_settings.obd2channelInfo.get(self._current_channel_config.name)
        channel_was_customized = not self._current_channel_config.equals(matching_existing_preset)
        popup = None

        def _apply_preset():
            channel_cfg.__dict__.update(obd2_preset.__dict__)
            Clock.schedule_once(lambda dt: HelpInfo.help_popup('obdii_preset_help', self, arrow_pos='left_mid'), 1.0)
            self.load_tabs()

        def _on_answer(instance, answer):
            if answer:
                _apply_preset()
            popup.dismiss()

        if not self._is_new and channel_was_customized:
            popup = confirmPopup('Confirm', 'Apply pre-set values for {}?\n\nAny customizations made to this channel will be over-written.'.format(name), _on_answer)
        else:
            _apply_preset()


    def init_tabs(self):
        self.ids.tabs.add_widget(self.can_channel_customization_tab)
        if self._mapping_capable:
            self.ids.tabs.add_widget(self.pid_config_tab)
            self.ids.tabs.add_widget(self.can_id_tab)
            self.ids.tabs.add_widget(self.can_value_map_tab)
            self.ids.tabs.add_widget(self.can_formula_tab)
            self.ids.tabs.add_widget(self.can_units_conversion_tab)

    def load_tabs(self):
        self._current_channel_config = copy.deepcopy(self.channel_cfg)
        tabs = [lambda dt: self.can_channel_customization_tab.init_view(self.channel_cfg, self.channels, self.max_sample_rate)]
        if self._mapping_capable:
            tabs += [lambda dt: self.can_channel_customization_tab.init_view(self.channel_cfg, self.channels, self.max_sample_rate),
                     lambda dt: self.pid_config_tab.init_view(self.channel_cfg),
                     lambda dt: self.can_id_tab.init_view(self.channel_cfg),
                     lambda dt: self.can_value_map_tab.init_view(self.channel_cfg),
                     lambda dt: self.can_formula_tab.init_view(self.channel_cfg),
                     lambda dt: self.can_units_conversion_tab.init_view(self.channel_cfg, self.can_filters)
                     ]
        clock_sequencer(tabs)

class OBD2Channel(BoxLayout):
    channel = None
    obd2_preset_settings = None
    channel_index = 0
    Builder.load_string("""
<OBD2Channel>:
    size_hint_y: None
    height: dp(30)
    orientation: 'horizontal'
    FieldLabel:
        size_hint_x: 0.5
        id: name
    FieldLabel:
        size_hint_x: 0.3
        id: sample_rate
    IconButton:
        size_hint_x: 0.1    
        text: u'\uf044'
        on_release: root.on_edit()        
    IconButton:
        size_hint_x: 0.1
        text: '\357\200\224'
        on_release: root.on_delete()
""")

    def __init__(self, obd2_preset_settings, can_filters, channels, **kwargs):
        super(OBD2Channel, self).__init__(**kwargs)
        self.obd2_preset_settings = obd2_preset_settings
        self.can_filters = can_filters
        self.channels = channels
        self.register_event_type('on_delete_obd2_channel')
        self.register_event_type('on_modified')
        self.register_event_type('on_edit_channel')

    def on_delete_obd2_channel(self, pid):
        pass

    def on_modified(self):
        pass

    def on_delete(self):
        self.dispatch('on_delete_obd2_channel', self.channel_index)

    def on_edit_channel(self, channel_index):
        pass

    def on_edit(self):
        self.dispatch('on_edit_channel', self.channel_index)

    def set_channel(self, channel_index, channel):
        self.channel_index = channel_index
        self.channel = channel
        self.refresh()

    def refresh(self):
        self.ids.name.text = self.channel.name
        self.ids.sample_rate.text = '{}Hz'.format(self.channel.sampleRate)

class OBD2ChannelsView(BaseConfigView):
    DEFAULT_OBD2_SAMPLE_RATE = 1
    obd2_cfg = None
    max_sample_rate = 0
    obd2_grid = None
    obd2_preset_settings = None
    Builder.load_string("""
<OBD2ChannelsView>:
    spacing: dp(20)
    orientation: 'vertical'
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 0.20
        SettingsView:
            id: obd2enable
            size_hint_y: 0.6
            label_text: 'OBDII channels'
            help_text: ''
        BoxLayout:
            padding: (dp(10), dp(0))
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(40)        
            BoxLayout:
            LabelIconButton:
                size_hint_x: None
                width: dp(120)
                id: load_preset
                title: 'Presets'
                icon_size: self.height * 0.7
                title_font_size: self.height * 0.5
                icon: u'\uf150'
                on_press: root.load_preset_view()
    BoxLayout:
        size_hint_y: 0.85
        orientation: 'vertical'        
        HSeparator:
            text: 'OBDII Channels'
        BoxLayout:
            orientation: 'horizontal'
            padding: [dp(5), dp(0)]
            size_hint_y: 0.1
            FieldLabel:
                text: 'Channel'
                size_hint_x: 0.5                
            FieldLabel:
                text: 'Rate'
                size_hint_x: 0.3
            BoxLayout:
                size_hint_x: 0.2
        AnchorLayout:                
            AnchorLayout:
                ScrollContainer:
                    canvas.before:
                        Color:
                            rgba: 0.05, 0.05, 0.05, 1
                        Rectangle:
                            pos: self.pos
                            size: self.size                
                    id: scrlobd2
                    size_hint_y: 0.95
                    do_scroll_x:False
                    do_scroll_y:True
                    GridLayout:
                        id: obd2grid
                        padding: [dp(5), dp(5)]
                        spacing: [dp(0), dp(10)]
                        size_hint_y: None
                        height: max(self.minimum_height, scrlobd2.height)
                        cols: 1
                FieldLabel:
                    halign: 'center'
                    id: list_msg
                    text: ''                                    
            AnchorLayout:
                anchor_y: 'bottom'
                IconButton:
                    size_hint: (None, None)
                    height: root.height * .12
                    text: u'\uf055'
                    color: ColorScheme.get_accent()
                    on_release: root.on_add_obd2_channel()
                    disabled: True
                    id: addpid
""")
    preset_manager = ObjectProperty()

    def __init__(self, **kwargs):
        super(OBD2ChannelsView, self).__init__(**kwargs)
        self.register_event_type('on_config_updated')
        self.obd2_grid = self.ids.obd2grid
        obd2_enable = self.ids.obd2enable
        obd2_enable.bind(on_setting=self.on_obd2_enabled)
        obd2_enable.setControl(SettingsSwitch())
        base_dir = kwargs.get('base_dir')

        self.obd2_preset_settings = OBD2Settings(base_dir=base_dir)
        self.can_filters = UnitsConversionFilters(base_dir)

        self.update_view_enabled()

    def on_modified(self, *args):
        if self.obd2_cfg:
            self.obd2_cfg.stale = True
            self.dispatch('on_config_modified', *args)

    def on_obd2_enabled(self, instance, value):
        if self.obd2_cfg:
            self.obd2_cfg.enabled = value
            self.dispatch('on_modified')

    def on_config_updated(self, rc_cfg):
        obd2_cfg = rc_cfg.obd2Config
        max_sample_rate = rc_cfg.capabilities.sample_rates.sensor
        self.ids.obd2enable.setValue(obd2_cfg.enabled)

        self.obd2_grid.clear_widgets()
        self.reload_obd2_channel_grid(obd2_cfg)
        self.max_sample_rate = max_sample_rate
        self.obd2_cfg = obd2_cfg
        self.mapping_capable = rc_cfg.capabilities.has_can_channel
        self.update_view_enabled()


    def update_view_enabled(self):
        add_disabled = True
        if self.obd2_cfg:
            if len(self.obd2_cfg.pids) < OBD2_CONFIG_MAX_PIDS:
                add_disabled = False

        self.ids.addpid.disabled = add_disabled

    def reload_obd2_channel_grid(self, obd2_cfg):
        self.obd2_grid.clear_widgets()

        for i in range(len(obd2_cfg.pids)):
            pid_config = obd2_cfg.pids[i]
            self.add_obd2_channel(i, pid_config)

        self.update_view_enabled()
        self._refresh_channel_list_notice(obd2_cfg)

    def _delete_obdii_channel(self, channel_index):
        del self.obd2_cfg.pids[channel_index]
        self.reload_obd2_channel_grid(self.obd2_cfg)
        self.dispatch('on_modified')

    def on_delete_obd2_channel(self, instance, channel_index):
        popup = None
        def _on_answer(instance, answer):
            if answer:
                self._delete_obdii_channel(channel_index)
            popup.dismiss()
        popup = confirmPopup('Confirm', 'Delete OBDII Channel?', _on_answer)


    def _replace_config(self, to_cfg, from_cfg):
        to_cfg.__dict__.update(from_cfg.__dict__)

    def _on_edit_channel(self, instance, channel_index):
        self._edit_channel(channel_index, False)

    def _edit_channel(self, channel_index, is_new):
        channel = self.obd2_cfg.pids[channel_index]
        working_channel_cfg = copy.deepcopy(channel)
        content = OBD2ChannelConfigView(self.obd2_preset_settings, is_new, self.mapping_capable)
        content.init_config(working_channel_cfg, self.can_filters, self.max_sample_rate, self.channels)

        def _on_answer(instance, answer):
            if answer:
                self._replace_config(channel, working_channel_cfg)
                self.dispatch('on_modified')
                self.reload_obd2_channel_grid(self.obd2_cfg)
            popup.dismiss()

        popup = editor_popup('Edit OBDII channel', content, _on_answer, size=(dp(500), dp(300)))

    def add_obd2_channel(self, index, pid_config):
        channel = OBD2Channel(obd2_preset_settings=self.obd2_preset_settings, can_filters=self.can_filters, channels=self.channels)
        channel.bind(on_delete_obd2_channel=self.on_delete_obd2_channel)
        channel.bind(on_edit_channel=self._on_edit_channel)
        channel.set_channel(index, pid_config)
        channel.bind(on_modified=self.on_modified)
        self.obd2_grid.add_widget(channel)

    def on_add_obd2_channel(self):
        if not self.obd2_cfg:
            return

        pid_config = PidConfig()
        pid_config.sampleRate = self.DEFAULT_OBD2_SAMPLE_RATE

        def _on_answer(instance, answer):
            if answer:
                self.obd2_cfg.pids.append(pid_config)
                channel_index = len(self.obd2_cfg.pids) - 1
                self.add_obd2_channel(channel_index, pid_config)
                self.dispatch('on_modified')
                self.reload_obd2_channel_grid(self.obd2_cfg)
            popup.dismiss()

        content = OBD2ChannelConfigView(self.obd2_preset_settings, True, self.mapping_capable)
        content.init_config(pid_config, self.can_filters, self.max_sample_rate, self.channels)
        popup = editor_popup('Add OBDII channel', content, _on_answer, size=(dp(500), dp(300)))


    def _refresh_channel_list_notice(self, obd2_cfg):
        channel_count = len(obd2_cfg.pids)
        self.ids.list_msg.text = 'Press (+) to add an OBDII channel' if channel_count == 0 else ''


    def _delete_all_channels(self):
        del self.obd2_cfg.pids[:]
        self.reload_obd2_channel_grid(self.obd2_cfg)
        self.dispatch('on_modified')

    def _on_preset_selected(self, instance, preset_id):
        popup = None
        def _on_answer(instance, answer):
            if answer == True:
                self._delete_all_channels()
            self._import_preset(preset_id)
            popup.dismiss()

        if len(self.obd2_cfg.pids) > 0:
            popup = choicePopup('Confirm', 'Overwrite or append existing channels?', 'Overwrite', 'Append', _on_answer)
        else:
            self._import_preset(preset_id)

    def _import_preset(self, id):
        try:
            preset = self.preset_manager.get_preset_by_id(id)
            if preset:
                mapping = preset.mapping
                for channel_json in mapping['pids']:
                    new_channel = PidConfig()
                    new_channel.fromJson(channel_json)
                    self.obd2_cfg.pids.append(new_channel)
                self.reload_obd2_channel_grid(self.obd2_cfg)
                self.obd2_cfg.stale = True
                self.dispatch('on_modified')
            self._refresh_channel_list_notice(self.obd2_cfg)
        except Exception as e:
            alertPopup('Error', 'There was an error loading the preset:\n\n{}'.format(e))
            raise

    def load_preset_view(self):
        def popup_dismissed(*args):
            pass

        content = PresetBrowserView(self.preset_manager, 'obd2')
        content.bind(on_preset_selected=self._on_preset_selected)
        content.bind(on_preset_close=lambda *args:popup.dismiss())
        popup = Popup(title='Import a preset configuration', content=content, size_hint=(0.7, 0.8))
        popup.bind(on_dismiss=popup_dismissed)
        popup.open()
