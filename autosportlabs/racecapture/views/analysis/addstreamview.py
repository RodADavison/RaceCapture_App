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
from datetime import datetime
from threading import Thread
import kivy
kivy.require('1.10.0')
from kivy.app import Builder
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.screenmanager import Screen
from kivy.base import ExceptionManager
from utils import kvFind
from kivy.adapters.listadapter import ListAdapter
from autosportlabs.uix.button.featurebutton import FeatureButton
from autosportlabs.uix.textwidget import FieldInput
from autosportlabs.racecapture.views.util.alertview import alertPopup, confirmPopup
from autosportlabs.racecapture.views.file.loaddialogview import LoadDialog
from autosportlabs.racecapture.views.file.savedialogview import SaveDialog
from autosportlabs.util.timeutil import friendly_format_time_ago
from iconbutton import IconButton
from fieldlabel import FieldLabel
from iconbutton import LabelIconButton
from autosportlabs.uix.toast.kivytoast import toast

class AddStreamView(BoxLayout):
    Builder.load_string("""
<AddStreamView>:
    orientation: 'vertical'
    ScreenManager:
        id: screens
        AddStreamSelectView:
            id: streamSelectScreen
            name: 'stream_select'
        CloudConnectView:
            id: cloudConnectScreen
            name: 'cloud'
        WirelessConnectView:
            id: wirelessConnectScreen
            name: 'wireless'
        FileConnectView:
            id: fileConnectScreen
            name: 'file'
        SessionImportView:
            id: session_import_screen
            name: 'session'    
    """)
    def __init__(self, settings, datastore, **kwargs):
        super(AddStreamView, self).__init__(**kwargs)
        stream_select_view = self.ids.streamSelectScreen
        stream_select_view.bind(on_select_stream=self.on_select_stream)

        cloud_connect_view = self.ids.cloudConnectScreen
        cloud_connect_view.settings = settings
        cloud_connect_view.datastore = datastore

        wireless_connect_view = self.ids.wirelessConnectScreen
        wireless_connect_view.settings = settings
        wireless_connect_view.datastore = datastore

        file_connect_view = self.ids.fileConnectScreen
        file_connect_view.settings = settings
        file_connect_view.datastore = datastore
        file_connect_view.bind(on_connect_stream_complete=self.connect_stream_complete)
        file_connect_view.bind(on_connect_stream_start=self.connect_stream_start)

        session_import_view = self.ids.session_import_screen
        session_import_view.datastore = datastore
        session_import_view.bind(on_add=self.add_session)
        session_import_view.bind(on_delete=self.delete_session)
        session_import_view.bind(on_close=self.close)
        session_import_view.bind(on_export=self.export_session)

        self.register_event_type('on_connect_stream_start')
        self.register_event_type('on_connect_stream_complete')
        self.register_event_type('on_export_session')
        self.register_event_type('on_add_session')
        self.register_event_type('on_delete_session')
        self.register_event_type('on_close')

    def add_session(self, instance, session):
        self.dispatch('on_add_session', session)

    def delete_session(self, instance, session):
        self.dispatch('on_delete_session', session)

    def export_session(self, instance, session):
        self.dispatch('on_export_session', session)

    def on_delete_session(self, *args):
        pass

    def on_export_session(self, *args):
        pass

    def on_add_session(self, *args):
        pass

    def on_connect_stream_start(self, *args):
        pass

    def on_connect_stream_complete(self, *args):
        pass

    def on_select_stream(self, instance, stream_type):
        self.ids.screens.current = stream_type

    def connect_stream_start(self, *args):
        self.dispatch('on_connect_stream_start')

    def connect_stream_complete(self, instance, session_id):
        self.dispatch('on_connect_stream_complete', session_id)

    def close(self, *args):
        self.dispatch('on_close')

    def on_close(self, *args):
        pass

class AddStreamSelectView(Screen):
    Builder.load_string("""
<AnalysisFeatureButton@FeatureButton>
    title_font: 'resource/fonts/ASL_regular.ttf'
    icon_color: [0.0, 0.0, 0.0, 1.0]
    title_color: [0.2, 0.2, 0.2, 1.0]
    disabled_color: [1.0, 1.0, 1.0, 1.0]
    highlight_color: [0.7, 0.7, 0.7, 1.0]

<AddStreamSelectView>:
    BoxLayout:
        orientation: 'vertical'
        GridLayout:
            size_hint_y: 0.8
            padding: [self.height * 0.1, self.height * 0.15]
            spacing: self.height * 0.1
            rows: 1
            cols: 3
            AnalysisFeatureButton:
                icon: u'\uf15b'
                title: 'Import Log File'
                on_press: root.select_stream('file')
            AnalysisFeatureButton:
                icon: u'\uf187'
                title: 'Saved Session'
                on_press: root.select_stream('session')
        FieldLabel:
            size_hint_y: 0.2
            font_size: root.height * 0.1
            font_name: 'resource/fonts/ASL_regular.ttf'
            halign: 'center'
            text: 'Select a session location'    
    """)
    def __init__(self, **kwargs):
        super(AddStreamSelectView, self).__init__(**kwargs)
        self.register_event_type('on_select_stream')

    def select_stream(self, stream):
        self.dispatch('on_select_stream', stream)

    def on_select_stream(self, stream):
        pass

class BaseStreamConnectView(Screen):
    settings = None
    datastore = None
    def __init__(self, **kwargs):
        super(BaseStreamConnectView, self).__init__(**kwargs)
        self.register_event_type('on_connect_stream_complete')
        self.register_event_type('on_connect_stream_start')

    def on_connect_stream_complete(self, *args):
        pass

    def on_connect_stream_start(self, *args):
        pass

class CloudConnectView(BaseStreamConnectView):
    Builder.load_string("""
<CloudConnectView>:
    FieldLabel:
        text: 'Cloud connect view'    
    """)

class WirelessConnectView(BaseStreamConnectView):
    Builder.load_string("""
<WirelessConnectView>:
    FieldLabel:
        text: 'Wireless connect view'    
    """)

class FileConnectView(BaseStreamConnectView):
    Builder.load_string("""
<FileConnectView>:
    BoxLayout:
        orientation: 'vertical'
        LogImportWidget:
            id: log_import    
    """)
    def __init__(self, **kwargs):
        super(FileConnectView, self).__init__(**kwargs)

    def on_enter(self):
        log_import_view = self.ids.log_import
        log_import_view.bind(on_import_complete=self.import_complete)
        log_import_view.bind(on_import_start=self.import_start)
        log_import_view.datastore = self.datastore
        log_import_view.settings = self.settings

    def import_start(self, *args):
        self.dispatch('on_connect_stream_start')

    def import_complete(self, instance, session_id, success, message):
        if success == True:
            self.dispatch('on_connect_stream_complete', session_id)
            return

        alertPopup("Import Failed",
                   "There was a problem importing the datalog. Details:\n\n{}".format(message))
        self.dispatch('on_connect_stream_complete', None)

class SessionImportView(BaseStreamConnectView):
    Builder.load_string("""
<SessionImportView>:
    BoxLayout:
        id: content
        orientation: 'vertical'
        size_hint_y: 1
        BoxLayout:
            ScrollContainer:
                on_scroll_move: root.on_scroll(*args)
                id: session_scroller
                do_scroll_x: False
                do_scroll_y: True
                size_hint_y: 1
                size_hint_x: 1
                GridLayout:
                    id: session_list
                    padding: [0, dp(20)]
                    spacing: [0, dp(10)]
                    row_default_height: dp(30)
                    size_hint_y: None
                    height: self.minimum_height
                    cols: 1
        IconButton:
            size_hint_y: 0.2
            text: "\357\200\214"
            on_press: root.close()    
    """)

    def __init__(self, **kwargs):
        super(SessionImportView, self).__init__(**kwargs)
        self.register_event_type('on_add')
        self.register_event_type('on_delete')
        self.register_event_type('on_close')
        self.register_event_type('on_export')

    def on_enter(self, *args):
        # Find sessions, append to session list
        sessions = self.datastore.get_sessions()

        if len(sessions) == 0:
            self.ids.session_list.add_widget(Label(text="No saved sessions"))

        for session in sessions:
            session_view = SessionListItem(session)
            session_view.ids.name.text = session.name
            session_view.ids.date.text = friendly_format_time_ago(datetime.utcfromtimestamp(session.date))
            session_view.bind(on_delete=self.delete_session)
            session_view.bind(on_add=self.add_session)
            session_view.bind(on_export=self.export_session)

            self.ids.session_list.add_widget(session_view)

    def on_scroll(self, *args):
        pass

    def delete_session(self, list_item):
        self.datastore.delete_session(list_item.session.session_id)
        self.ids.session_list.remove_widget(list_item)
        self.dispatch('on_delete', list_item.session)
        toast("Session deleted", center_on=self)

    def export_session(self, list_item):
        self.dispatch('on_export', list_item.session)

    def add_session(self, list_item):
        self.dispatch('on_add', list_item.session)
        toast("Session loaded", center_on=self)

    def close(self, *args):
        self.dispatch('on_close')

    def on_add(self, *args):
        pass

    def on_export(self, *args):
        pass

    def on_delete(self, *args):
        pass

    def on_close(self, *args):
        pass


class SessionListItem(BoxLayout):
    Builder.load_string("""
<SessionListItem>:
    rows: 1
    spacing: dp(10)
    BoxLayout:
        orientation: 'horizontal'
        FieldLabel:
            text: ''
            id: name
            font_size: self.height * 0.6
        FieldLabel:
            text: ''
            id: date
            font_size: self.height * 0.6
    IconButton:
        on_press: root.add_session()
        text: u'\uf0fe'
        font_size: self.height
        height: root.height
        width: dp(50)
        size_hint_x: None
    IconButton:
        on_press: root.export_session()
        text: u'\uf045'
        font_size: self.height
        height: root.height
        width: dp(50)
        size_hint_x: None
    IconButton:
        on_press: root.delete_session()
        text: u'\uf014'
        font_size: self.height
        height: root.height
        width: dp(50)
        size_hint_x: None    
    """)
    def __init__(self, session, **kwargs):
        super(SessionListItem, self).__init__(**kwargs)
        self.session = session
        self.register_event_type('on_delete')
        self.register_event_type('on_add')
        self.register_event_type('on_export')

    def delete_session(self, *args):
        popup = None

        def confirm_delete(instance, delete):
            if delete:
                self.dispatch('on_delete')
            popup.dismiss()

        popup = confirmPopup("Delete", "Are you sure you sure you want to delete session '{}'?".format(self.session.name),
                             confirm_delete)

    def export_session(self, *args):
        self.dispatch('on_export')

    def add_session(self, *args):
        self.dispatch('on_add')

    def on_delete(self, *args):
        pass

    def on_add(self, *args):
        pass

    def on_export(self, *args):
        pass


class LogImportWidget(BoxLayout):
    Builder.load_string("""
<LogImportWidget>:
    size: root.size
    BoxLayout:
        spacing: dp(10)
        padding: (sp(5), sp(5), sp(5), sp(5))
        orientation: 'vertical'
        BoxLayout:
            orientation: 'vertical'
            spacing: sp(5)            
            size_hint_y: 0.85
            
            BoxLayout:
                size_hint_y: 0.20
                orientation: 'horizontal'
                FieldLabel:
                    text: 'Datalog Location'
                BoxLayout:
                    orientation: 'horizontal'
                    spacing: sp(10)
                    FieldLabel:
                        size_hint_x: 0.5
                        id: log_path
                        multiline: False
                        
                    LabelIconButton:
                        id: browse_button
                        size_hint_x: 0.5
                        title: 'Browse'
                        icon_size: self.height * .9
                        title_font_size: self.height * 0.7
                        icon: '\357\204\225'
                        on_press: root.select_log()
            
            BoxLayout:
                size_hint_y: 0.25
                orientation: 'horizontal'
                FieldLabel: 
                    text: 'Session Name'
                FieldInput:
                    id: session_name
                    
            BoxLayout:
                size_hint_y: 0.55
                orientation: 'vertical'
                spacing: sp(5)
                FieldLabel:
                    size_hint_y: 0.1
                    size_hint_x: 1.0
                    text: 'Log book'
                TextInput:
                    id: session_notes
                    size_hint_y: 0.9


        AnchorLayout:
            anchor_x: 'right'            
            size_hint_y: 0.15
            LabelIconButton:
                id: import_button
                disabled: True
                size_hint_x: 0.2
                title: 'Import'
                icon_size: self.height * .9
                title_font_size: self.height * 0.7
                icon: u'\uf090'
                on_press: root.load_log()
            
                        
        FieldLabel:
            size_hint_y: .05
            halign: 'center'
            id: current_status
            
        ProgressBar:
            id: log_load_progress
            size_hint_y: .05    
    """)
    datastore = ObjectProperty(None)
    settings = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LogImportWidget, self).__init__(**kwargs)
        self.register_event_type('on_import_complete')
        self.register_event_type('on_import_start')
        self._log_path = None

    def on_import_start(self, *args):
        pass

    def on_import_complete(self, session_id, success, message):
        pass

    def close_log_select(self, *args):
        self._log_select.dismiss()
        self._log_select = None

    def set_log_path(self, instance):
        if len(instance.selection):
            path = instance.selection[0]
            self._log_path = path
            base_name = self._extract_base_logfile_name(path)
            self.ids.session_name.text = base_name
            self.ids.log_path.text = base_name
            self.ids.import_button.disabled = False

            self._log_select.dismiss()
            self.set_import_file_path(instance.path)

    def _extract_base_logfile_name(self, path):
        session_name, file_extension = os.path.splitext(os.path.basename(path))
        return session_name

    def set_import_file_path(self, path):
        self.settings.userPrefs.set_pref('preferences', 'import_datalog_dir', path)

    def get_import_file_path(self):
        return self.settings.userPrefs.get_pref('preferences', 'import_datalog_dir')

    def select_log(self):
        ok_cb = self.close_log_select
        content = LoadDialog(ok=self.set_log_path,
                             cancel=self.close_log_select,
                             filters=['*' + '.LOG', '*' + '.log'],
                             user_path=self.get_import_file_path())
        self._log_select = Popup(title="Select Log", content=content, size_hint=(0.9, 0.9))
        self._log_select.open()

    def _loader_thread(self, logpath, session_name, session_notes):
        Clock.schedule_once(lambda dt: self.dispatch('on_import_start'))
        success = True
        message = ''
        session_id = None
        try:
            session_id = self.datastore.import_datalog(logpath, session_name, session_notes, self._update_progress)
        except Exception as e:
            success = False
            message = str(e)
            ExceptionManager.handle_exception(e)
        Clock.schedule_once(lambda dt: self.dispatch('on_import_complete', session_id, success, message))

    def _update_progress(self, percent_complete=0):
        if self.ids.current_status.text != "Loading log records":
            self.ids.current_status.text = "Loading log records"
        self.ids.log_load_progress.value = int(percent_complete)

    def _set_form_disabled(self, disabled):
        self.ids.browse_button.disabled = disabled
        self.ids.session_name.disabled = disabled
        self.ids.import_button.disabled = disabled
        self.ids.session_notes.disabled = disabled

    def load_log(self):
        logpath = self._log_path
        session_name = self.ids.session_name.text.strip()
        session_notes = self.ids.session_notes.text.strip()

        if not os.path.isfile(logpath):
            alertPopup("Invalid log specified",
                      "Unable to find specified log file: {}. \nAre you sure it exists?".format(logpath))
            return

        Logger.info("LogImportWidget: loading log: {}".format(self.ids.log_path.text))

        # choose a default name if the user deletes the suggested name
        if not session_name or len(session_name) == 0:
            session_name = self._extract_base_logfile_name(logpath)
            self.ids.session_name.text = session_name

        self.ids.current_status.text = "Initializing Datastore"

        self._set_form_disabled(True)
        t = Thread(target=self._loader_thread, args=(logpath, session_name, session_notes))
        t.daemon = True
        t.start()

