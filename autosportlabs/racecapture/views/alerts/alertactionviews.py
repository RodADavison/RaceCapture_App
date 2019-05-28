import kivy
from kivy.uix.behaviors.button import ButtonBehavior
kivy.require('1.10.0')
from kivy.app import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from fieldlabel import FieldLabel
from kivy.properties import ObjectProperty
from autosportlabs.racecapture.alerts.alertactions import *
from autosportlabs.racecapture.views.color.colorpickerview import ColorPickerView
from autosportlabs.racecapture.views.color.colorpickerview import ColorBlock
from autosportlabs.uix.textwidget import FieldInput
from mappedspinner import MappedSpinner
import re

class BaseAlertActionEditorView(BoxLayout):
    alertaction = ObjectProperty()

    @classmethod
    def new_instance(cls, action):
        return cls(alertaction=action)

class ColorAlertActionEditorView(BaseAlertActionEditorView):
    Builder.load_string("""
<ColorAlertActionEditorView>:
    BoxLayout:
        size_hint_x: 0.6
    
        AnchorLayout:
            ColorBlock:
                size_hint: (0.5, 0.5)
                id: selected_color
        
    ColorWheel:
        size_hint_x: 0.4
        id: color_wheel
        on_color: root._select_color(*args)
    """)

    def __init__(self, **kwargs):
        super(ColorAlertActionEditorView, self).__init__(**kwargs)
        c = self.alertaction.color_rgb
        self.ids.selected_color.color = [c[0], c[1], c[2], 1.0]

    def _select_color(self, instance, color):
        self.ids.selected_color.color = color
        self.alertaction.color_rgb = [color[0], color[1], color[2], 1.0]

class PopupAlertActionEditorView(BaseAlertActionEditorView):
    Builder.load_string("""
<PopupAlertActionEditorView>:
    BoxLayout:
        size_hint_x: 0.6
        orientation: 'vertical'
        spacing: dp(10)
        Widget:
        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Message'
                halign: 'right'
            FieldInput:
                id: popup_message
                on_text: root._on_popup_message(*args)
                input_filter: lambda text, from_undo: text[:16 - len(self.text)]

        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Shape'
                halign: 'right'
            MappedSpinner:
                value_map: {None:'None', 'triangle':'Triangle', 'octagon':'Octagon'}
                id: popup_shape
                on_text: root._on_popup_shape(*args)
                
        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Color'
                halign: 'right'
            AnchorLayout:
                ColorBlock:
                    id: popup_color
                    on_press: root._on_select_color(*args)
        Widget:
                        
    FieldLabel:
        text: ''
        halign: 'center'
        size_hint_x: 0.4
    """)

    def __init__(self, **kwargs):
        super(PopupAlertActionEditorView, self).__init__(**kwargs)
        self._refresh_view()

    def _refresh_view(self):
        alertaction = self.alertaction
        self.ids.popup_message.text = alertaction.message
        self.ids.popup_shape.setFromValue(alertaction.shape)
        c = alertaction.color_rgb
        self.ids.popup_color.color = [c[0], c[1], c[2], 1.0]

    def _on_popup_message(self, instance, value):
        # filter the message
        value = value.strip()
        self.ids.popup_message.text = value
        self.alertaction.message = value

    def _on_popup_shape(self, instance, value):
        self.alertaction.shape = instance.getValueFromKey(value)

    def _on_select_color(self, instance):
        def color_selected(instance, c):
            self.alertaction.color_rgb = [c[0], c[1], c[2], 1.0]
            self.ids.popup_color.color = [c[0], c[1], c[2], 1.0]
            popup.dismiss()

        c = self.alertaction.color_rgb
        content = ColorPickerView(color=[c[0], c[1], c[2], 1.0])
        content.bind(on_color_selected=color_selected)
        popup = Popup(title="Select Color", content=content, size_hint=(0.4, 0.6))
        popup.open()

class LedAlertActionEditorView(BaseAlertActionEditorView):
    Builder.load_string("""
<LedAlertActionEditorView>:
    BoxLayout:
        size_hint_x: 0.6
        orientation: 'vertical'
        spacing: dp(10)
        Widget:
        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'LED'
                halign: 'right'
            MappedSpinner:
                value_map: {'left':'Left', 'right':'Right'}
                id: led_position
                on_text: root._on_led_position(*args)

        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Flash'
                halign: 'right'
            MappedSpinner:
                value_map: {0:'Solid', 1:'1Hz', 5:'5Hz', 10:'10Hz'}
                id: flash_rate
                on_text: root._on_flash_rate(*args)
                
        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Color'
                halign: 'right'
            AnchorLayout:
                ColorBlock:
                    id: led_color
                    on_press: root._on_select_color(*args)
        Widget:

    FieldLabel:
        size_hint_x: 0.4
        text: ''
        halign: 'center'
    """)

    def __init__(self, **kwargs):
        super(LedAlertActionEditorView, self).__init__(**kwargs)
        self._refresh_view()

    def _refresh_view(self):
        alertaction = self.alertaction
        self.ids.led_position.setFromValue(alertaction.led_position)
        self.ids.flash_rate.setFromValue(alertaction.flash_rate)
        c = alertaction.color_rgb
        self.ids.led_color.color = [c[0], c[1], c[2], 1.0]

    def _on_led_position(self, instance, value):
        try:
            self.alertaction.led_position = instance.getValueFromKey(value)
        except NoneType:
            pass

    def _on_flash_rate(self, instance, value):
        try:
            self.alertaction.flash_rate = instance.getValueFromKey(value)
        except NoneType:
            pass

    def _on_select_color(self, instance):
        def color_selected(instance, c):
            self.alertaction.color_rgb = [c[0], c[1], c[2], 1.0]
            self.ids.led_color.color = [c[0], c[1], c[2], 1.0]
            popup.dismiss()

        c = self.alertaction.color_rgb
        content = ColorPickerView(color=[c[0], c[1], c[2], 1.0])
        content.bind(on_color_selected=color_selected)
        popup = Popup(title="Select Color", content=content, size_hint=(0.4, 0.6))
        popup.open()

class ShiftLightAlertActionEditorView(BaseAlertActionEditorView):
    Builder.load_string("""
<ShiftLightAlertActionEditorView>:
    BoxLayout:
        size_hint_x: 0.6
        orientation: 'vertical'
        spacing: dp(10)
        Widget:

        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Flash'
                halign: 'right'
            MappedSpinner:
                value_map: {0:'Solid', 1:'1Hz', 5:'5Hz', 10:'10Hz'}
                id: flash_rate
                on_text: root._on_flash_rate(*args)
                
        BoxLayout:
            spacing: dp(10)
            size_hint_y: None
            height: dp(40)
            FieldLabel:
                text: 'Color'
                halign: 'right'
            AnchorLayout:
                ColorBlock:
                    id: led_color
                    on_press: root._on_select_color(*args)
        Widget:
                        
    FieldLabel:
        size_hint_x: 0.4
        text: ''
        halign: 'center'
    """)

    def __init__(self, **kwargs):
        super(ShiftLightAlertActionEditorView, self).__init__(**kwargs)
        self._refresh_view()

    def _refresh_view(self):
        alertaction = self.alertaction
        self.ids.flash_rate.setFromValue(alertaction.flash_rate)
        c = alertaction.color_rgb
        self.ids.led_color.color = [c[0], c[1], c[2], 1.0]

    def _on_flash_rate(self, instance, value):
        try:
            self.alertaction.flash_rate = instance.getValueFromKey(value)
        except NoneType:
            pass

    def _on_select_color(self, instance):
        def color_selected(instance, c):
            self.alertaction.color_rgb = [c[0], c[1], c[2], 1.0]
            self.ids.led_color.color = [c[0], c[1], c[2], 1.0]
            popup.dismiss()

        c = self.alertaction.color_rgb
        content = ColorPickerView(color=[c[0], c[1], c[2], 1.0])
        content.bind(on_color_selected=color_selected)
        popup = Popup(title="Select Color", content=content, size_hint=(0.4, 0.6))
        popup.open()

class AlertActionEditorFactory(object):

    factory = {
                ColorAlertAction.__name__:ColorAlertActionEditorView.new_instance,
                PopupAlertAction.__name__:PopupAlertActionEditorView.new_instance,
                LedAlertAction.__name__:LedAlertActionEditorView.new_instance,
                ShiftLightAlertAction.__name__:ShiftLightAlertActionEditorView.new_instance
              }

    @staticmethod
    def create_editor(alertaction):
        return AlertActionEditorFactory.factory[alertaction.__class__.__name__](alertaction)

class BaseAlertActionPreviewView(BoxLayout):
    alertaction = ObjectProperty()

    @classmethod
    def new_instance(cls, action):
        return cls(alertaction=action)

class TitleAlertActionPreviewView(BaseAlertActionEditorView):
    Builder.load_string("""
<TitleAlertActionPreviewView>:
    FieldLabel:
        text: root.alertaction.title
    """)

class ColorAlertActionPreviewView(BaseAlertActionEditorView):
    Builder.load_string("""
<ColorAlertActionPreviewView>:
    FieldLabel:
        text: root.alertaction.title
        size_hint_x: None
        width: dp(200)
    Widget:
        canvas.before:
            Color:
                rgba: [root.alertaction.color_rgb[0], root.alertaction.color_rgb[1], root.alertaction.color_rgb[2], 1.0]
            Rectangle:
                pos: self.pos
                size: self.size
        size_hint_x: None
        width: dp(20)
    """)

class AlertActionPreviewFactory(object):
    factory = {
            ColorAlertAction.__name__:ColorAlertActionPreviewView.new_instance,
            PopupAlertAction.__name__:ColorAlertActionPreviewView.new_instance,
            LedAlertAction.__name__:ColorAlertActionPreviewView.new_instance,
            ShiftLightAlertAction.__name__:ColorAlertActionPreviewView.new_instance
        }

    @staticmethod
    def create_preview(alertaction):
        return AlertActionPreviewFactory.factory[alertaction.__class__.__name__](alertaction)
