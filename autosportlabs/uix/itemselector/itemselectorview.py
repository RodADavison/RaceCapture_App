import kivy
kivy.require('1.10.0')
from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButtonBehavior
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.app import Builder

from autosportlabs.racecapture.theme.color import ColorScheme
class ItemSelectionRef(EventDispatcher):
    title = StringProperty()
    image_source = StringProperty(allownone=True)
    key = ObjectProperty()

    def __init__(self, **kwargs):
        super(ItemSelectionRef, self).__init__(**kwargs)

class ItemSelectionView(ToggleButtonBehavior, BoxLayout):
    Builder.load_string("""
<ItemSelectionView>:
    canvas.before:
        Color:
            rgba: root.selected_color
        Rectangle:
            pos: self.pos
            size: self.size
    group: 'item'
    padding: (dp(5), dp(5))
    FieldLabel:
        text: root.title
        halign: 'center'
    Image:
        source: root.image_source
    """)

    title = StringProperty()
    image_source = StringProperty(allownone=True)
    item_reference = ObjectProperty()
    selected_color = ListProperty(ColorScheme.get_dark_background())

    def on_state(self, instance, value):
        selected = value == 'down'
        self.selected_color = ColorScheme.get_medium_background() if selected else ColorScheme.get_dark_background()
        self.dispatch('on_selected', selected)

    def __init__(self, **kwargs):
        super(ItemSelectionView, self).__init__(**kwargs)
        self.register_event_type('on_selected')
        self.state = 'down' if kwargs.get('selected') == True else 'normal'

    def on_selected(self, state):
        pass

class ItemSelectorView(BoxLayout):
    Builder.load_string("""
<ItemSelectorView>:
    orientation: 'vertical'
    spacing: dp(5)
    padding: (dp(10), dp(10))
    ScrollContainer:
        id: scroll
        size_hint_y: 0.6
        do_scroll_x:False
        do_scroll_y:True
        GridLayout:
            id: grid
            padding: (dp(10), dp(10))
            spacing: dp(10)
            row_default_height: root.height * 0.3
            size_hint_y: None
            height: self.minimum_height
            cols: 1
    """)

    selected_item = ObjectProperty()
    item_references = ListProperty()

    def __init__(self, **kwargs):
        super(ItemSelectorView, self).__init__(**kwargs)
        self.init_view()

    def init_view(self):
        item_references = self.item_references

        for item in item_references:
            view = ItemSelectionView(title=item.title, image_source=item.image_source, item_reference=item, selected_item=item)
            view.bind(on_selected=self._on_item_state)
            self.ids.grid.add_widget(view)

    def _on_item_state(self, instance, value):
        if value:
            self.selected_item = instance.item_reference
