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
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp
from kivy.app import Builder
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivy.clock import Clock
from kivy.metrics import sp
from iconbutton import IconButton
from autosportlabs.racecapture.theme.color import ColorScheme
from valuefield import FloatValueField
from autosportlabs.racecapture.views.util.viewutils import autoformat_number

__all__ = ('alertPopup, confirmPopup, okPopup, editor_popup, progress_popup, number_editor_popup')

def alertPopup(title, msg):
    popup = Popup(title=title,
                      content=Label(text=msg),
                      size_hint=(None, None), size=(dp(600), dp(200)))
    popup.open()

def choicePopup(title, msg, choice1, choice2, answerCallback):
    content = ChoicePopup(text=msg, choice1=choice1, choice2=choice2)
    content.bind(on_answer=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600), dp(200)),
                    auto_dismiss=False)
    popup.open()
    return popup

class ChoicePopup(GridLayout):
    Builder.load_string("""
<ChoicePopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        Button:
            text: root.choice2
            on_release: root.dispatch('on_answer', False)
        Button:
            text: root.choice1
            on_release: root.dispatch('on_answer', True)    
    """)

    text = StringProperty()
    choice1 = StringProperty('Yes')
    choice2 = StringProperty('No')

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ChoicePopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass

def confirmPopup(title, msg, answerCallback):
    content = ConfirmPopup(text=msg)
    content.bind(on_answer=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600), dp(200)),
                    auto_dismiss=False)
    popup.open()
    return popup

class ConfirmPopup(GridLayout):
    Builder.load_string("""
<ConfirmPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dispatch('on_answer', False)
        IconButton:
            text: u'\uf00c'
            on_press: root.dispatch('on_answer', True)    
    """)
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_answer')
        super(ConfirmPopup, self).__init__(**kwargs)

    def on_answer(self, *args):
        pass

def editor_popup(title, content, answerCallback, size_hint=(None, None), size=(dp(500), dp(220)), hide_ok=False, auto_dismiss_time=None):

    def auto_dismiss(*args):
        popup.dismiss()

    def on_title(instance, title):
        popup.title = title

    content.bind(on_title=on_title)
    content = EditorPopup(content=content, hide_ok=hide_ok)
    content.bind(on_answer=answerCallback)
    popup = Popup(title=title,
                    content=content,
                    size=size, size_hint=size_hint,
                    auto_dismiss=True,
                  title_size=sp(18))
    popup.open()

    if auto_dismiss_time:
        Clock.create_trigger(auto_dismiss, auto_dismiss_time)()

    return popup

class EditorPopup(GridLayout):
    Builder.load_string("""
<EditorPopup>:
    id: editor_popup
    cols:1
    BoxLayout:
        id: content
        size_hint_y: 0.85
    GridLayout:
        id: buttons
        cols: 2
        size_hint_y: 0.15
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dispatch('on_answer', False)
        IconButton:
            id: ok
            text: u'\uf00c'
            on_press: root.dispatch('on_answer', True)    
    """)
    content = ObjectProperty(None)

    def __init__(self, hide_ok=False, **kwargs):
        self.register_event_type('on_answer')
        super(EditorPopup, self).__init__(**kwargs)
        if hide_ok:
            self.ids.buttons.remove_widget(self.ids.ok)

    def on_content(self, instance, value):
        Clock.schedule_once(lambda dt: self.ids.content.add_widget(value))

    def on_answer(self, *args):
        pass

def okPopup(title, msg, answer_callback):
    def ok_cb(*args):
        answer_callback(args)
        popup.dismiss()

    content = OkPopup(text=msg)
    content.bind(on_ok=ok_cb)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600), dp(200)),
                    auto_dismiss=False)
    popup.open()
    return popup

class OkPopup(GridLayout):
    Builder.load_string("""
<OkPopup>:
    cols:1
    Label:
        text: root.text
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            text: u'\uf00c'
            on_press: root.dispatch('on_ok', True)    
    """)
    text = StringProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_ok')
        super(OkPopup, self).__init__(**kwargs)

    def on_ok(self, *args):
        pass

def progress_popup(title, msg, answer_callback):
    content = ProgressPopup(text=msg)
    content.bind(on_ok_cancel=answer_callback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(600), dp(200)),
                    auto_dismiss=False)
    popup.open()
    return popup

class ProgressPopup(GridLayout):
    Builder.load_string("""
<ProgressPopup>:
    cols:1
    padding: (dp(10), dp(10))
    Label:
        text: root.text
        size_hint_y: 0.4
    ProgressBar:
        value: root.progress
        size_hint_y: 0.6
    GridLayout:
        cols: 2
        size_hint_y: None
        height: '44sp'
        spacing: '5sp'
        IconButton:
            id: ok_cancel
            text: u'\uf00d'
            on_press: root.dispatch('on_ok_cancel', True)
            color: ColorScheme.get_primary()                
    """)
    text = StringProperty()
    progress = NumericProperty()

    def __init__(self, **kwargs):
        self.register_event_type('on_ok_cancel')
        super(ProgressPopup, self).__init__(**kwargs)

    def on_ok_cancel(self, *args):
        pass

    def update_progress(self, value):
        self.progress = value

    def on_progress(self, instance, value):
        if value == 100:
            self.ids.ok_cancel.color = ColorScheme.get_light_primary_text()
            self.ids.ok_cancel.text = u'\uf00c'

class NumberEditorPopup(GridLayout):
    Builder.load_string("""
<NumberEditorPopup>:
    cols:1
    padding: (dp(10), dp(10))
    FieldLabel:
        text: root.msg
        size_hint_y: 0.45
        id: msg
    FloatValueField:
        text: root.formatted_value
        on_text: root._on_value_updated()
        size_hint_y: 0.3
        id: value
    GridLayout:
        id: buttons
        cols: 2
        size_hint_y: 0.25
        IconButton:
            text: u'\uf00d'
            color: ColorScheme.get_primary()            
            on_release: root.dispatch('on_ok_cancel', False)
        IconButton:
            id: ok
            text: u'\uf00c'
            on_press: root.dispatch('on_ok_cancel', True)    
    """)
    msg = StringProperty('')
    value = NumericProperty(0)
    formatted_value = StringProperty('0')
    min_value = NumericProperty(None, allownone=True)
    max_value = NumericProperty(None, allownone=True)

    def __init__(self, **kwargs):
        self.register_event_type('on_ok_cancel')
        super(NumberEditorPopup, self).__init__(**kwargs)

    def on_value(self, instance, value):
        self.formatted_value = autoformat_number(value)

    def on_ok_cancel(self, *args):
        pass

    def _on_value_updated(self, *args):
        value_text = self.ids.value.text
        value = 0 if len(value_text) == 0 else float(value_text)
        min_value = self.min_value
        max_value = self.max_value
        is_valid = (min_value is None or value >= min_value) and (max_value is None or value <= max_value)
        self.value = value

        self.ids.value.background_color = ColorScheme.get_normal_background() if is_valid else ColorScheme.get_error_background()
        self.ids.msg.text = self.msg if is_valid else 'Valid range is {} - {}'.format(autoformat_number(self.min_value), autoformat_number(self.max_value))
        self.ids.ok.disabled = not is_valid
        
def number_editor_popup(title, msg, value, min_value, max_value, answer_callback):
    content = NumberEditorPopup(msg=msg,
                                value=value,
                                min_value=min_value,
                                max_value=max_value)
    content.bind(on_ok_cancel=answer_callback)
    popup = Popup(title=title,
                    content=content,
                    size_hint=(None, None),
                    size=(dp(400), dp(300)),
                    auto_dismiss=False)
    popup.open()
    return popup
        

