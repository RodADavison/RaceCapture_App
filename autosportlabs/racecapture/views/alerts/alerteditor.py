import kivy
kivy.require('1.10.0')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.metrics import dp
from fieldlabel import FieldLabel, ClickFieldLabel
from iconbutton import IconButton
from kivy.app import Builder
from kivy.core.window import Window

from kivy.properties import BooleanProperty, ObjectProperty, StringProperty, NumericProperty
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition, SlideTransition
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.racecapture.views.util.alertview import confirmPopup
from autosportlabs.widgets.scrollcontainer import ScrollContainer
from autosportlabs.racecapture.views.alerts.alertactionviews import AlertActionEditorFactory, AlertActionPreviewFactory
from autosportlabs.racecapture.alerts.alertrules import AlertRule
from autosportlabs.uix.button.betterbutton import BetterButton
from autosportlabs.uix.itemselector.itemselectorview import ItemSelectorView, ItemSelectionRef
from mappedspinner import MappedSpinner
from autosportlabs.racecapture.views.util.alertview import editor_popup, number_editor_popup
from autosportlabs.racecapture.alerts.alertactions import get_alertaction_default_collection
from autosportlabs.uix.layout.sections import ClickAnchorLayout
from autosportlabs.uix.toast.kivytoast import toast
from valuefield import NumericValueField

class AddItemView(BoxLayout):
    title = StringProperty('')
    Builder.load_string("""
<AddItemView>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(80)
    IconButton:
        size_hint_y: None
        height: dp(50)
        text: u'\uf055'
        color: ColorScheme.get_accent()
        on_release: root.dispatch('on_select')
    FieldLabel:
        text: root.title
        halign: 'center'
        size_hint_y: None
        height: dp(30)
    """)

    def __init__(self, **kwargs):
        super(AddItemView, self).__init__(**kwargs)
        self.register_event_type('on_select')

    def on_select(self, *args):
        pass

class AlertRuleSummaryView(BoxLayout):
    is_first = BooleanProperty(False)
    is_last = BooleanProperty(False)
    precision = NumericProperty(0)

    Builder.load_string("""
<AlertRuleSummaryView>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(30)
    ClickFieldLabel:
        id: range
        size_hint_x: 0.29
        on_press: root.dispatch('on_select', root._alertrule)
    ClickAnchorLayout:
        id: type
        size_hint_x: 0.39
        on_press: root.dispatch('on_select', root._alertrule)
    Switch:
        id: enabled
        size_hint_x: 0.2
        on_active: root.on_enable_disable()
    IconButton:
        size_hint_x: 0.07
        text: u'\uf063'
        disabled: root.is_last
        on_release: root.dispatch('on_move_down', root._alertrule)    
    IconButton:
        size_hint_x: 0.07
        text: u'\uf062'
        disabled: root.is_first        
        on_release: root.dispatch('on_move_up', root._alertrule)
    IconButton:
        size_hint_x: 0.07
        text: u'\uf014'
        on_release: root.dispatch('on_delete', root._alertrule)    
""")
    def __init__(self, alertrule, **kwargs):
        super(AlertRuleSummaryView, self).__init__(**kwargs)
        self._alertrule = alertrule
        self.register_event_type('on_select')
        self.register_event_type('on_move_down')
        self.register_event_type('on_move_up')
        self.register_event_type('on_delete')
        self.register_event_type('on_modified')
        self._refresh_view()

    def _refresh_view(self):
        ar = self._alertrule
        range_type = ar.range_type
        self.ids.range.text = '{} {} {}'.format('' if ar.low_threshold is None else self._format_range(ar.low_threshold),
                                                '-' if range_type == AlertRule.RANGE_BETWEEN else '->',
                                                '' if ar.high_threshold is None else self._format_range(ar.high_threshold))
        actions = ar.alert_actions
        actions_len = len(ar.alert_actions)
        if actions_len == 1:
            preview_widget = AlertActionPreviewFactory.create_preview(actions[0])
        else:
            preview_widget = FieldLabel(text='(Multiple Actions)' if actions_len > 1 else '(No Actions)', halign='left')

        self.ids.type.add_widget(preview_widget)

        self.ids.enabled.active = ar.enabled is True

    def _format_range(self, value):
        value_format = '{{:.{}f}}'.format(self.precision)
        return value_format.format(value)

    def on_select(self, rule):
        pass

    def on_enable_disable(self):
        self._alertrule.enabled = self.ids.enabled.active
        self.dispatch('on_modified', self._alertrule)

    def on_modified(self, rule):
        pass

    def on_edit(self, rule):
        pass

    def on_delete(self, rule):
        pass

    def on_move_down(self, rule):
        pass

    def on_move_up(self, rule):
        pass

class AlertRuleList(Screen):
    MAX_RULES = 10
    alertrule_collection = ObjectProperty()
    precision = NumericProperty()
    min_value = NumericProperty()
    Builder.load_string("""
<AlertRuleList>:
    ScrollContainer:
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
            id: rules_grid
            padding: [dp(5), dp(5)]                        
            spacing: [dp(0), dp(10)]
            size_hint_y: None
            height: max(self.minimum_height, scroller.height)
            cols: 1
    """)

    def __init__(self, **kwargs):
        super(AlertRuleList, self).__init__(**kwargs)
        self.register_event_type('on_select')

    def on_select(self, value):
        pass

    def on_alertrule_collection(self, instance, value):
        self.refresh_view()

    def _append_alertrule_summary(self, rule):
        view = AlertRuleSummaryView(rule)
        view.precision = self.precision
        view.bind(on_select=self._on_select_rule)
        view.bind(on_move_up=self._on_move_rule_up)
        view.bind(on_move_down=self._on_move_rule_down)
        view.bind(on_delete=self._on_delete_rule)
        view.bind(on_modified=self._on_modified_rule)
        self.ids.rules_grid.add_widget(view)

        return view

    def refresh_view(self):
        grid = self.ids.rules_grid
        rules = self.alertrule_collection.alert_rules

        grid.clear_widgets()
        is_first = True
        view = None
        for rule in rules:
            view = self._append_alertrule_summary(rule)
            view.is_first = is_first
            is_first = False
        if view is not None:
            view.is_last = True

        if len(rules) < AlertRuleList.MAX_RULES:
            add_item = AddItemView(title='' if len(rules) > 0 else 'Add new Rule')
            add_item.bind(on_select=self._add_new_rule)
            grid.add_widget(add_item)

    def _get_next_rule_low_threshold(self):
        # as a convenience, find the highest threshold set
        # so they can easily create congruent ranges
        rules = self.alertrule_collection.alert_rules
        low_threshold = self.min_value
        for rule in rules:
            low_threshold = max(rule.high_threshold, low_threshold)

        return low_threshold

    def _add_new_rule(self, *args):
        alertrule = AlertRule(enabled=True,
                              range_type=AlertRule.RANGE_GREATHER_THAN_EQUAL,
                              low_threshold=self._get_next_rule_low_threshold(),
                              high_threshold=None,
                              alert_actions=[])
        self.alertrule_collection.append(alertrule)
        self.refresh_view()
        self.dispatch('on_select', alertrule)

    def _on_modified_rule(self, instance, value):
        pass

    def _on_select_rule(self, instance, value):
        self.dispatch('on_select', value)

    def _on_move_rule_up(self, instance, value):
        rules = self.alertrule_collection.alert_rules
        current_index = rules.index(value)
        if current_index == 0:
            return

        rules.insert(current_index - 1, rules.pop(current_index))
        self.refresh_view()

    def _on_move_rule_down(self, instance, value):
        rules = self.alertrule_collection.alert_rules
        current_index = rules.index(value)
        if current_index == len(rules) - 1:
            return

        rules.insert(current_index + 1, rules.pop(current_index))
        self.refresh_view()

    def _on_delete_rule(self, instance, value):

        popup = None
        def confirm_delete(instance, delete):
            if delete:
                rules = self.alertrule_collection.alert_rules
                rules.remove(value)
                self.refresh_view()
            popup.dismiss()

        high = value.high_threshold
        low = value.low_threshold
        symbol = '-' if high and low else '->'
        popup = confirmPopup('Delete', 'Delete Group {} {} {}?'.format('' if low is None else low, symbol, '' if high is None else high), confirm_delete)

class AlertActionSummaryView(BoxLayout):
    Builder.load_string("""

<AlertActionSummaryView>:
    size_hint_y: None
    height: dp(30)
    ClickAnchorLayout:
        id: title
        size_hint_x: 0.9
        on_press: root.dispatch('on_edit', root._alertaction)
 
# TODO re-enable this when we can do drag / drop on alert rules, so 
# we can save space by removing the up/down arrow buttons. 
# and add an edit button to the alert rules list        
#    IconButton:
#        size_hint_x: 0.1        
#        text: u'\uf044'
#        on_release: root.dispatch('on_edit', root._alertaction)

    IconButton:
        size_hint_x: 0.1        
        text: u'\uf014'
        on_release: root.dispatch('on_delete', root._alertaction)    
    """)

    def __init__(self, alertaction, **kwargs):
        super(AlertActionSummaryView, self).__init__(**kwargs)
        self._alertaction = alertaction
        self.register_event_type('on_edit')
        self.register_event_type('on_delete')
        self._refresh_view()

    def _refresh_view(self):
        aa = self._alertaction
        preview = AlertActionPreviewFactory.create_preview(aa)
        self.ids.title.add_widget(preview)

    def on_edit(self, alertaction):
        pass

    def on_delete(self, alertaction):
        pass

class SpinValueField(BoxLayout):
    value = NumericProperty(0.0)
    step_value = NumericProperty(1.0)
    min_value = NumericProperty(0.0)
    max_value = NumericProperty(100.0)
    value_format = StringProperty('{:.0f}')

    Builder.load_string("""
<SpinValueField>:
    BetterButton:
        width: dp(30)
        size_hint_x: None
        text: '-'
        font_size: self.height * 0.7
        on_press: root._increment(-root.step_value)
        disabled: root.value <= root.min_value
        
    ClickFieldLabel:
        text: root.value_format.format(root.value)
        halign: 'center'
        #underline: True
        on_press: root._on_value_edit()
        
    BetterButton:
        width: dp(30)
        size_hint_x: None
        text: '+'
        font_size: self.height * 0.7
        on_press: root._increment(root.step_value)
        disabled: root.value >= root.max_value
    """)

    def _increment(self, step_value):
        self.value = max(self.min_value, min(self.max_value, self.value + step_value))

    def on_step_value(self, instance, value):
        # guess the number of digits of precision
        if self.step_value % 1 == 0:
            self.value_format = '{:.0f}'
        elif self.step_value % 0.1 == 0:
            self.value_format = '{:.1f}'
        else:
            self.value_format = '{:.2f}'

    def _on_value_edit(self, *args):
        def popup_dismissed(instance, result):
            if result:
                self.value = instance.value
            popup.dismiss()

        popup = number_editor_popup('Edit Range', 'Set the value for this range', self.value, self.min_value, self.max_value, popup_dismissed)

class AlertActionList(Screen):
    MAX_ALERTACTIONS = 10
    alertrule = ObjectProperty()
    min_value = NumericProperty()
    max_value = NumericProperty()
    precision = NumericProperty()
    Builder.load_string("""
#:import AlertRule autosportlabs.racecapture.alerts.alertrules.AlertRule
<AlertActionList>:
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            padding: (0, dp(2))
            FieldLabel:
                text: 'Active Range'
                halign: 'right'
                padding: (dp(5), 0)
                size_hint_x: 0.4
            BoxLayout:
                ScreenManager:
                    id: low_threshold_screen
                    Screen:
                        name: 'show'
                        SpinValueField:
                            id: low_threshold
                            on_value: root._on_low_threshold(*args)
                            min_value: root.min_value
                            max_value: root.max_value
                    Screen:
                        name: 'hide'
                AnchorLayout:
                    MappedSpinner:
                        id: range_type
                        size_hint_x: 0.9
                        value_map: {AlertRule.RANGE_BETWEEN:'to',AlertRule.RANGE_LESS_THAN_EQUAL:'up to',AlertRule.RANGE_GREATHER_THAN_EQUAL:'and up'}
                        font_size: self.height * .7
                        font_name: "resource/fonts/ASL_light.ttf"
                        on_text: root._on_range_type_selected(*args)
                ScreenManager:
                    id: high_threshold_screen
                    Screen:
                        name: 'show'
                        SpinValueField:
                            id: high_threshold
                            on_value: root._on_high_threshold(*args)
                            min_value: root.min_value
                            max_value: root.max_value
                    Screen:
                        name: 'hide'
                    
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: dp(80)
            BoxLayout:
                size_hint_y: None
                height: dp(40)
                padding: (0, dp(2))
                FieldLabel:
                    text: 'Active After'
                    size_hint_x: 0.4
                    halign: 'right'
                    padding: (dp(5), 0)
                BoxLayout:
                    SpinValueField:
                        size_hint_x: 0.33
                        id: activate_sec
                        on_value: root._on_activate_sec(*args)
                    FieldLabel:
                        padding: (dp(5), 0)
                        size_hint_x: 0.33
                        text: 'sec.'
                        halign: 'left'
                    Widget:
                        size_hint_x: 0.33

            BoxLayout:
                size_hint_y: None
                height: dp(40)
                padding: (0, dp(2))
                FieldLabel:
                    text: 'Deactive After'
                    size_hint_x: 0.4                    
                    halign: 'right'
                    padding: (dp(5), 0)
                BoxLayout:
                    SpinValueField:
                        size_hint_x: 0.33
                        id: deactivate_sec
                        on_value: root._on_deactivate_sec(*args)
                    FieldLabel:
                        padding: (dp(5), 0)
                        size_hint_x: 0.33
                        text: 'sec.'
                        halign: 'left'
                    Widget:
                        size_hint_x: 0.33

        ScrollContainer:
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
                id: grid
                padding: [dp(5), dp(5)]                        
                spacing: [dp(0), dp(10)]
                size_hint_y: None
                height: max(self.minimum_height, scroller.height)
                cols: 1
    
        AnchorLayout:
            size_hint_y: None
            height: dp(60)
            anchor_x: 'right'
            IconButton:
                text: "\357\200\214"
                #size_hint_x: None
                #width: dp(60)
                on_press: root.dispatch('on_close')
    """)

    def __init__(self, **kwargs):
        super(AlertActionList, self).__init__(**kwargs)
        self.register_event_type('on_close')
        self.register_event_type('on_edit_action')

    def on_max_value(self, instance, value):
        self._update_range_step()

    def on_min_value(self, instance, value):
        self._update_range_step()

    def _update_range_step(self):
        step = (self.max_value - self.min_value) / 100.0
        self.ids.high_threshold.step_value = self.ids.low_threshold.step_value = step

    def _on_range_type_selected(self, instance, value):
        value = instance.getValueFromKey(value)
        self.alertrule.range_type = value
        show_low_threshold = value == AlertRule.RANGE_BETWEEN or value == AlertRule.RANGE_GREATHER_THAN_EQUAL
        show_high_threshold = value == AlertRule.RANGE_BETWEEN or value == AlertRule.RANGE_LESS_THAN_EQUAL
        low_threshold = self.ids.low_threshold
        high_threshold = self.ids.high_threshold

        low_screen = self.ids.low_threshold_screen
        high_screen = self.ids.high_threshold_screen

        low_screen.transition.direction = 'up' if show_low_threshold else 'down'
        high_screen.transition.direction = 'up' if show_high_threshold else 'down'

        low_screen.current = 'show' if show_low_threshold else 'hide'
        high_screen.current = 'show' if show_high_threshold else 'hide'

        self.alertrule.low_threshold = None if not show_low_threshold else low_threshold.value
        self.alertrule.high_threshold = None if not show_high_threshold else high_threshold.value

    def _on_activate_sec(self, instance, value):
        try:
            self.alertrule.activate_sec = value
        except NoneType:
            pass

    def _on_deactivate_sec(self, instance, value):
        self.alertrule.deactivate_sec = value

    def _on_high_threshold(self, instance, value):
        self.alertrule.high_threshold = value
        self._auto_adjust_range()

    def _on_low_threshold(self, instance, value):
        self.alertrule.low_threshold = value
        self._auto_adjust_range()

    def _auto_adjust_range(self):
        low = self.alertrule.low_threshold
        high = self.alertrule.high_threshold
        range_type = self.alertrule.range_type
        if range_type == AlertRule.RANGE_BETWEEN:
            if low >= high:
                high = low

        if low is not None:
            self.ids.low_threshold.value = low
        if high is not None:
            self.ids.high_threshold.value = high

    def on_alertrule(self, instance, value):
        self.refresh_view()

    def _append_alertaction_view(self, alertaction):
        view = AlertActionSummaryView(alertaction)
        view.bind(on_edit=self._on_edit_action)
        view.bind(on_delete=self._on_delete_action)
        self.ids.grid.add_widget(view)

    def refresh_view(self):
        self.ids.low_threshold_screen.transition = SlideTransition(direction='up')
        self.ids.high_threshold_screen.transition = SlideTransition(direction='up')
        grid = self.ids.grid
        alertrule = self.alertrule
        alertactions = alertrule.alert_actions

        grid.clear_widgets()
        for alertaction in alertactions:
            self._append_alertaction_view(alertaction)

        if len(alertactions) < AlertActionList.MAX_ALERTACTIONS:
            add_item = AddItemView(title='' if len(alertactions) > 0 else 'Add new Action')
            add_item.bind(on_select=self._add_new_action)
            grid.add_widget(add_item)

        self.ids.low_threshold.value = self.min_value if alertrule.low_threshold is None else alertrule.low_threshold
        self.ids.high_threshold.value = self.max_value if alertrule.high_threshold is None else alertrule.high_threshold
        self.ids.activate_sec.value = alertrule.activate_sec
        self.ids.deactivate_sec.value = alertrule.deactivate_sec
        self.ids.range_type.setFromValue(alertrule.range_type)

    def _add_new_action(self, *args):
        def popup_dismissed(instance, result):
            if result:
                selected = instance.content.selected_item
                if selected is not None:
                    alertaction = selected.key
                    self.alertrule.alert_actions.append(alertaction)
                    self.dispatch('on_edit_action', alertaction)
                    self.refresh_view()
            popup.dismiss()

        alertaction_prototypes = get_alertaction_default_collection(exclude_filter=self.alertrule.alert_actions)

        items = [ItemSelectionRef(title=alertaction.title, image_source=alertaction.PREVIEW_IMAGE, key=alertaction) for alertaction in alertaction_prototypes]

        if len(items) == 0:
            toast('No more actions available')
        else:
            view = ItemSelectorView(item_references=items)
            popup = editor_popup('Select Action', view,
                                 popup_dismissed,
                                 size_hint=(None, None),
                                 size=(min(Window.width, dp(700)), min(Window.height,dp(400))),
                                 auto_dismiss_time=10)

    def on_close(self):
        pass

    def on_edit_action(self, action):
        pass

    def on_enter(self, *args):
        pass

    def _on_edit_action(self, instance, action):
        self.dispatch('on_edit_action', action)

    def _on_delete_action(self, instance, action):
        popup = None
        def confirm_delete(instance, delete):
            if delete:
                actions = self.alertrule.alert_actions
                actions.remove(action)
                self.refresh_view()
            popup.dismiss()

        popup = confirmPopup('Delete', 'Delete Action {}?'.format(action.title), confirm_delete)

class AlertActionEditor(Screen):
    alertaction = ObjectProperty()
    Builder.load_string("""
<AlertActionEditor>:
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            id: editor_container
            
        AnchorLayout:
            size_hint_y: None
            height: dp(60)
            anchor_x: 'right'
            IconButton:
                text: "\357\200\214"
                #size_hint_x: None
                #width: dp(60)
                on_press: root.dispatch('on_close')
""")
    alertaction = ObjectProperty()

    def __init__(self, **kwargs):
        super(AlertActionEditor, self).__init__(**kwargs)
        self.register_event_type('on_close')

    def on_alertaction(self, instance, action):
        ec = self.ids.editor_container
        ec.clear_widgets()
        ec.add_widget(AlertActionEditorFactory.create_editor(action))

    def on_close(self):
        pass

class AlertRulesView(BoxLayout):
    title = StringProperty()
    channel = StringProperty()
    min_value = NumericProperty()
    max_value = NumericProperty()
    precision = NumericProperty()
    current_alertrule = ObjectProperty(allownone=True)
    current_action = ObjectProperty(allownone=True)

    Builder.load_string("""
<AlertRulesView>:
    ScreenManager:
        id: screen_manager
        AlertRuleList:
            name: "rule_list"
            id: rule_list
            precision: root.precision
            min_value: root.min_value
        AlertActionList:
            name: 'group_list'
            id: group_list
            min_value: root.min_value
            max_value: root.max_value
            precision: root.precision
        AlertActionEditor:
            name: 'action_editor'
            id: action_editor
    """)

    def __init__(self, alertrule_collection, **kwargs):
        super(AlertRulesView, self).__init__(**kwargs)
        self.ids.screen_manager.transition = SlideTransition()
        self._alertrule_collection = alertrule_collection

        self.ids.rule_list.bind(on_select=self._on_rule_select)
        self.ids.rule_list.alertrule_collection = alertrule_collection

        self.ids.group_list.bind(on_edit_action=self._on_edit_action)
        self.ids.group_list.bind(on_close=self._on_close_group)

        self.ids.action_editor.bind(on_close=self._on_close_action_editor)

    def _refresh_title(self):
        ar = self.current_alertrule
        value_range = '' if ar is None else ': {} - {}'.format(ar.low_threshold, ar.high_threshold)

        a = self.current_action
        action = '' if a is None else ': {}'.format(a.title)
        self.title = 'Customize {} {} {}'.format(self.channel, value_range, action)

    def on_current_alertrule(self, instance, value):
        self._refresh_title()

    def on_current_action(self, instance, value):
        self._refresh_title()

    def _on_rule_select(self, instance, alertrule):
        sm = self.ids.screen_manager
        sm.transition.direction = 'up'
        self.ids.group_list.alertrule = alertrule
        sm.current = 'group_list'
        self.current_alertrule = alertrule

    def _on_close_group(self, instance):
        sm = self.ids.screen_manager
        sm.transition.direction = 'down'
        sm.current = 'rule_list'
        self.current_alertrule = None
        self.ids.rule_list.refresh_view()

    def _on_close_action_editor(self, instance):
        sm = self.ids.screen_manager
        sm.transition.direction = 'down'
        sm.current = 'group_list'
        self.current_action = None
        self.ids.group_list.refresh_view()

    def _on_edit_action(self, instance, alertaction):
        sm = self.ids.screen_manager
        sm.transition.direction = 'up'
        self.ids.action_editor.alertaction = alertaction
        sm.current = 'action_editor'
        self.current_action = alertaction





