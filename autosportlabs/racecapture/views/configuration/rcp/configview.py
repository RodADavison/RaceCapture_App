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

import os

import kivy

kivy.require('1.10.0')
from kivy.app import Builder
from kivy.uix.treeview import TreeViewLabel
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy import platform
from kivy.logger import Logger
from autosportlabs.help.helpmanager import HelpInfo

from autosportlabs.racecapture.views.configuration.rcp.analogchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.imuchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.gpschannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.lapstatsview import *
from autosportlabs.racecapture.views.configuration.rcp.timerchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.gpiochannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.pwmchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.trackconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.canchannelsview import *
from autosportlabs.racecapture.views.configuration.rcp.obd2channelsview import *
from autosportlabs.racecapture.views.configuration.rcp.canconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.telemetry.telemetryconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.wirelessconfigview import *
from autosportlabs.racecapture.views.configuration.rcp.scriptview import *
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.racecapture.config.rcpconfig import *
from autosportlabs.racecapture.theme.color import ColorScheme


RCP_CONFIG_FILE_EXTENSION = '.rcp'

CONFIG_VIEW_KV = 'autosportlabs/racecapture/views/configuration/rcp/configview.kv'

class LinkedTreeViewLabel(TreeViewLabel):
    view = None
    view_builder = None


class ConfigView(Screen):
    Builder.load_file(CONFIG_VIEW_KV)
    # file save/load
    loaded = BooleanProperty(False)
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)
    writeStale = BooleanProperty(False)
    track_manager = ObjectProperty(None)

    # List of config views
    configViews = []
    menu = None
    rc_config = None
    script_view = None
    _settings = None
    base_dir = None
    _databus = None

    def __init__(self, **kwargs):
        super(ConfigView, self).__init__(**kwargs)

        self._status_pump = kwargs.get('status_pump')
        self._databus = kwargs.get('databus')
        self.rc_config = kwargs.get('rcpConfig', None)
        self.rc_api = kwargs.get('rc_api', None)
        self._settings = kwargs.get('settings')
        self.base_dir = kwargs.get('base_dir')

        self.register_event_type('on_config_updated')
        self.register_event_type('on_channels_updated')
        self.register_event_type('on_config_written')
        self.register_event_type('on_tracks_updated')
        self.register_event_type('on_config_modified')
        self.register_event_type('on_read_config')
        self.register_event_type('on_write_config')

        self._sn = ''

        if self.rc_config:
            self._sn = self.rc_config.versionConfig.serial

        self.ids.menu.bind(selected_node=self.on_select_node)

    def on_config_written(self, *args):
        self.writeStale = False

    def on_config_modified(self, *args):
        self.writeStale = True

    def update_runtime_channels(self, system_channels):
        for view in self.configViews:
            channelWidgets = list(kvquery(view, __class__=ChannelNameSpinner))
            for channelWidget in channelWidgets:
                channelWidget.dispatch('on_channels_updated', system_channels)

    def on_channels_updated(self, runtime_channels):
        self.update_runtime_channels(runtime_channels)

    def on_config_updated(self, config, force_reload=False):
        if config.versionConfig.serial != self._sn or force_reload:
            # New device or we need to redraw, reload everything
            # Our config object is the same object with new values, so we need to copy our value
            self._sn = copy(config.versionConfig.serial)
            self._clear()
            self.init_screen()
        else:
            self.rc_config = config
            self.update_config_views()

    def _clear(self):
        nodes = []

        # Building an array because if we remove while iterating we end up skipping things
        for node in self.ids.menu.iterate_all_nodes():
            nodes.append(node)

        for node in nodes:
            self.ids.menu.remove_node(node)

        self.ids.menu.clear_widgets()
        del(self.configViews[:])
        self.ids.content.clear_widgets()

    def on_track_manager(self, instance, value):
        self.update_tracks()

    def on_loaded(self, instance, value):
        self.update_config_views()
        self.update_tracks()

    def on_writeStale(self, instance, value):
        self.updateControls()

    def _reset_stale(self):
        self.writeStale = False

    def update_config_views(self):
        config = self.rc_config
        if config and self.loaded:
            for view in self.configViews:
                view.dispatch('on_config_updated', config)
        self._reset_stale()

    def init_screen(self):
        self.createConfigViews()

    def on_enter(self):
        if not self.loaded:
            Clock.schedule_once(lambda dt: self.init_screen())

    def createConfigViews(self):

        def attach_node(text, n, view_builder):
            tree = self.ids.menu
            label = LinkedTreeViewLabel(text=text)
            label.view_builder = view_builder
            label.color_selected = ColorScheme.get_dark_primary()
            return tree.add_node(label, n)

        def create_scripting_view(capabilities):
            script_view = LuaScriptingView(capabilities, rc_api=self.rc_api)
            self.script_view = script_view
            return script_view

        runtime_channels = self._settings.runtimeChannels

        default_node = attach_node('Race Tracks', None, lambda: TrackConfigView(status_pump=self._status_pump,
                                                                                    databus=self._databus,
                                                                                    rc_api=self.rc_api,
                                                                                    settings=self._settings,
                                                                                    track_manager=self.track_manager))

        if self.rc_config.capabilities.has_gps:
            attach_node('GPS', None, lambda: GPSChannelsView())
            
        attach_node('Race Timing', None, lambda: LapStatsView())

        if self.rc_config.capabilities.has_analog:
            attach_node('Analog Sensors', None, lambda: AnalogChannelsView(channels=runtime_channels))

        if self.rc_config.capabilities.has_timer:
            attach_node('Pulse/RPM Sensors', None, lambda: PulseChannelsView(channels=runtime_channels))

        if self.rc_config.capabilities.has_gpio:
            attach_node('Digital In/Out', None, lambda: GPIOChannelsView(channels=runtime_channels))

        if self.rc_config.capabilities.has_imu:
            attach_node('Accel/Gyro', None, lambda: ImuChannelsView(rc_api=self.rc_api))

        if self.rc_config.capabilities.has_pwm:
            attach_node('Pulse/Analog Out', None, lambda: AnalogPulseOutputChannelsView(channels=runtime_channels))

        attach_node('CAN Bus', None, lambda: CANConfigView())

        if self.rc_config.capabilities.has_can_channel:
            attach_node('CAN Mapping', None, lambda: CANChannelsView(settings=self._settings, channels=runtime_channels, base_dir=self.base_dir))

        attach_node('OBDII', None, lambda: OBD2ChannelsView(channels=runtime_channels, base_dir=self.base_dir))

        attach_node('Wireless', None, lambda: WirelessConfigView(self.base_dir, self.rc_config, self.rc_config.capabilities))

        attach_node('Telemetry', None, lambda: TelemetryConfigView(self.rc_config.capabilities))

        if self.rc_config.capabilities.has_script:
            node_name = 'Scripting'
        else:
            node_name = 'Logs'
        attach_node(node_name, None, lambda: create_scripting_view(self.rc_config.capabilities))

        if self.rc_api.is_firmware_update_supported():
            from autosportlabs.racecapture.views.configuration.rcp.firmwareupdateview import FirmwareUpdateView
            attach_node('Firmware', None, lambda: FirmwareUpdateView(rc_api=self.rc_api, settings=self._settings))

        self.ids.menu.select_node(default_node)

        self.update_runtime_channels(runtime_channels)
        self.update_tracks()
        self.loaded = True

    def show_node(self, node):
        view = node.view
        if not view:
            view = node.view_builder()
            self.configViews.append(view)
            view.bind(on_config_modified=self.on_config_modified)
            node.view = view
            if self.loaded:
                if self.rc_config:
                    view.dispatch('on_config_updated', self.rc_config)
                if self.track_manager:
                    view.dispatch('on_tracks_updated', self.track_manager)

        if view.get_parent_window() is None:
            Clock.schedule_once(lambda dt: self.ids.content.add_widget(view))

    def on_select_node(self, instance, value):
        if not value:
            return
        # ensure that any keyboard is released
        try:
            self.ids.content.get_parent_window().release_keyboard()
        except:
            pass
        self.ids.content.clear_widgets()
        Clock.schedule_once(lambda dt: self.show_node(value))

    def updateControls(self):
        Logger.debug("ConfigView: data is stale: " + str(self.writeStale))
        write_button = self.ids.write
        write_button.disabled = not self.writeStale
        write_button.pulsing = self.writeStale
        Clock.schedule_once(lambda dt: HelpInfo.help_popup('rc_write_config', self, arrow_pos='left_mid'), 1.0)

    def update_tracks(self):
        track_manager = self.track_manager
        if track_manager and self.loaded:
            for view in self.configViews:
                view.dispatch('on_tracks_updated', track_manager)

    def on_tracks_updated(self, track_manager):
        self.track_manager = track_manager

    def on_read_config(self, instance, *args):
        pass

    def on_write_config(self, instance, *args):
        pass

    def readConfig(self):
        if self.writeStale == True:
            popup = None
            def _on_answer(instance, answer):
                if answer:
                    self.dispatch('on_read_config', None)
                popup.dismiss()
            popup = confirmPopup('Confirm', 'Configuration Modified  - Continue Loading?', _on_answer)
        else:
            self.dispatch('on_read_config', None)

    def writeConfig(self):
        if self.rc_config.loaded:
            self.dispatch('on_write_config', None)
        else:
            alertPopup('Warning', 'Please load or read a configuration before writing')

    def openConfig(self):
        if self.writeStale:
            popup = None
            def _on_answer(instance, answer):
                if answer:
                    self.doOpenConfig()
                popup.dismiss()
            popup = confirmPopup('Confirm', 'Configuration Modified  - Open Configuration?', _on_answer)
        else:
            self.doOpenConfig()

    def set_config_file_path(self, path):
        self._settings.userPrefs.set_pref('preferences', 'config_file_dir', path)

    def get_config_file_path(self):
        return self._settings.userPrefs.get_pref('preferences', 'config_file_dir')

    def doOpenConfig(self):
        content = LoadDialog(ok=self.load, cancel=self.dismiss_popup, filters=['*' + RCP_CONFIG_FILE_EXTENSION], user_path=self.get_config_file_path())
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def saveConfig(self):
        if self.rc_config.loaded:
            content = SaveDialog(ok=self.save, cancel=self.dismiss_popup, filters=['*' + RCP_CONFIG_FILE_EXTENSION], user_path=self.get_config_file_path())
            self._popup = Popup(title="Save file", content=content, size_hint=(0.9, 0.9))
            self._popup.open()
        else:
            alertPopup('Warning', 'Please load or read a configuration before saving')

    def load(self, instance):
        self.set_config_file_path(instance.path)
        self.dismiss_popup()
        try:
            selection = instance.selection
            filename = selection[0] if len(selection) else None
            if filename:
                with open(filename) as stream:
                    rcpConfigJsonString = stream.read()
                    self.rc_config.fromJsonString(rcpConfigJsonString)
                    self.rc_config.stale = True
                    self.on_config_updated(self.rc_config, force_reload=True)
                    self.on_config_modified()
            else:
                alertPopup('Error Loading', 'No config file selected')
        except Exception as detail:
            alertPopup('Error Loading', 'Failed to Load Configuration:\n\n' + str(detail))
            Logger.exception('ConfigView: Error loading config: ' + str(detail))

    def save(self, instance):
        def _do_save_config(filename):
            if not filename.endswith(RCP_CONFIG_FILE_EXTENSION): filename += RCP_CONFIG_FILE_EXTENSION
            with open(filename, 'w') as stream:
                configJson = self.rc_config.toJsonString()
                stream.write(configJson)

        self.set_config_file_path(instance.path)
        self.dismiss_popup()
        config_filename = instance.filename
        if len(config_filename):
            try:
                config_filename = os.path.join(instance.path, config_filename)
                if os.path.isfile(config_filename):
                    def _on_answer(instance, answer):
                        if answer:
                            _do_save_config(config_filename)
                        popup.dismiss()
                    popup = confirmPopup('Confirm', 'File Exists - overwrite?', _on_answer)
                else:
                    _do_save_config(config_filename)
            except Exception as detail:
                alertPopup('Error Saving', 'Failed to save:\n\n' + str(detail))
                Logger.exception('ConfigView: Error Saving config: ' + str(detail))

    def dismiss_popup(self, *args):
        self._popup.dismiss()

