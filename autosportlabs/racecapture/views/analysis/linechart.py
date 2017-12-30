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

from installfix_garden_graph import Graph, LinePlot, SmoothLinePlot
from kivy.app import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from collections import OrderedDict
from  kivy.metrics import MetricsBase, sp
from kivy.logger import Logger
import bisect
import copy

from autosportlabs.racecapture.views.util.alertview import alertPopup
from autosportlabs.racecapture.views.analysis.analysiswidget import ChannelAnalysisWidget
from autosportlabs.racecapture.views.analysis.markerevent import MarkerEvent
from autosportlabs.racecapture.datastore import Filter
from autosportlabs.racecapture.views.analysis.analysisdata import ChannelData
from autosportlabs.uix.progressspinner import ProgressSpinner
from autosportlabs.uix.options.optionsview import OptionsView, BaseOptionsScreen
from autosportlabs.racecapture.views.analysis.customizechannelsview import CustomizeChannelsView
from autosportlabs.uix.button.widgetbuttons import LabelButton
from autosportlabs.racecapture.theme.color import ColorScheme
from autosportlabs.uix.toast.kivytoast import toast
from fieldlabel import FieldLabel
from iconbutton import IconButton, LabelIconButton
from autosportlabs.racecapture.views.util.viewutils import format_laptime

Builder.load_file('autosportlabs/racecapture/views/analysis/linechart.kv')

class ChannelPlot(object):

    def __init__(self, plot, channel, min_value, max_value, sourceref):
        self.lap = None
        self.chart_x_index = None
        self.plot = plot
        self.channel = channel
        self.min_value = min_value
        self.max_value = max_value
        self.sourceref = sourceref

    def __str__(self):
        return "{}_{}".format(str(self.sourceref), self.channel)

class LineChartMode(object):
    '''
    Describes the supported display modes for the chart
    '''
    TIME = 1
    DISTANCE = 2

    # conversion factor for milliseconds to minutes
    MS_TO_MINUTES = 0.000016666

    @staticmethod
    def format_value(mode, value):
        '''
        Format the value based on the specified mode
        :param mode the LineChartMode value 
        :type enum
        :param value the value to format
        :type float
        '''
        # Label marker that follows marker position
        if mode == LineChartMode.TIME:
            return format_laptime(value * LineChartMode.MS_TO_MINUTES)
        elif mode == LineChartMode.DISTANCE:
            return '{:.2f}'.format(value)
        else:
            return '---'

class LineChart(ChannelAnalysisWidget):
    '''
    Displays a line chart capable of showing multiple channels from multiple laps
    '''
    color_sequence = ObjectProperty(None)
    ZOOM_SCALING = 0.01
    TOUCH_ZOOM_SCALING = 0.000001
    MAX_SAMPLES_TO_DISPLAY = 1000

    # The meaningful distance is an approximate distance / time threshold to consider
    # a dataset to have meaningful distance data. The threshold is:
    # 0.000001 miles (or km, close enough) within 1 seconds.
    #
    # This is to provide a smart-ish way to auto-select time vs distance when a lap
    # is loaded loaded.
    MEANINGFUL_DISTANCE_RATIO_THRESHOLD = 0.000001

    def __init__(self, **kwargs):
        super(LineChart, self).__init__(**kwargs)
        self.register_event_type('on_marker')
        Window.bind(mouse_pos=self.on_mouse_pos)
        Window.bind(on_motion=self.on_motion)

        self.metrics_base = MetricsBase()

        self.got_mouse = False
        self._touches = []
        self._initial_touch_distance = 0
        self._touch_offset = 0
        self._touch_distance = 0

        self.zoom_level = 1
        self.max_x = 0
        self.current_x = 0
        self.current_offset = 0
        self.marker_pct = 0
        self.line_chart_mode = LineChartMode.DISTANCE
        self._channel_plots = {}
        self.x_axis_value_label = None

        self._user_refresh_requested = False

    def add_option_buttons(self):
        '''
        Add additional buttons needed by this widget
        '''
        self.chart_mode_toggle_button = IconButton(size_hint_x=0.15, on_press=self.on_toggle_chart_mode)
        self.append_option_button(self.chart_mode_toggle_button)
        self.x_axis_value_label = LabelButton(size_hint_x=0.5, on_press=self.on_toggle_chart_mode)
        self.append_option_button(self.x_axis_value_label)
        self._refresh_chart_mode_toggle()

    def _refresh_chart_mode_toggle(self):
        if self.line_chart_mode == LineChartMode.DISTANCE:
            self.chart_mode_toggle_button.text = u'\uf178'
            toast('Distance')
        else:
            self.chart_mode_toggle_button.text = u'\uf017'
            toast('Time')

    def on_toggle_chart_mode(self, *args):
        if self.line_chart_mode == LineChartMode.DISTANCE:
            self.line_chart_mode = LineChartMode.TIME
        else:
            self.line_chart_mode = LineChartMode.DISTANCE

        self._user_refresh_requested = True
        self._redraw_plots()
        self._refresh_chart_mode_toggle()

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            self.got_mouse = True
            touch.grab(self)
            if len(self._touches) == 1:
                self._initial_touch_distance = self._touches[0].distance(touch)
                self._touch_offset = self.current_offset
                self._touch_distance = self.current_x

            self._touches.append(touch)

            super(LineChart, self).on_touch_down(touch)
            return True
        else:
            super(LineChart, self).on_touch_down(touch)
            return False

    def on_touch_up(self, touch):
        self.got_mouse = False
        x, y = touch.x, touch.y

        # remove it from our saved touches
        if touch in self._touches:  # and touch.grab_state:
            touch.ungrab(self)
            self._touches.remove(touch)

        # stop propagating if its within our bounds
        if self.collide_point(x, y):
            return True

    def on_motion(self, instance, event, motion_event):
        if self.got_mouse and motion_event.x > 0 and motion_event.y > 0 and self.collide_point(motion_event.x, motion_event.y):
            chart = self.ids.chart
            try:
                zoom_scaling = self.max_x * self.ZOOM_SCALING
                button = motion_event.button
                zoom = self.marker_pct
                zoom_right = 1 / zoom
                zoom_left = 1 / (1 - zoom)
                zoom_left = zoom_left * zoom_scaling
                zoom_right = zoom_right * zoom_scaling

                if button == 'scrollup':
                    self.current_x += zoom_right
                    self.current_offset -= zoom_left
                else:
                    if button == 'scrolldown' and self.current_offset < self.current_x:
                        self.current_x -= zoom_right
                        self.current_offset += zoom_left

                self.current_x = self.max_x if self.current_x > self.max_x else self.current_x
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset

                chart.xmax = self.current_x
                chart.xmin = self.current_offset
            except:
                pass  # no scrollwheel support

    def on_marker(self, marker_event):
        pass

    def _get_adjusted_offset(self):
        '''
        Convert the current marker percent (percent across the graph) to 
        the x axis data value
        '''
        return self.current_offset + (self.marker_pct * (self.current_x - self.current_offset))

    def _update_x_marker_value(self):
        '''
        Update the value of the marker distance / time widget based on the current marker percent
        '''
        marker_x = self._get_adjusted_offset()
        label = self.x_axis_value_label
        if label is not None:
            self.x_axis_value_label.text = LineChartMode.format_value(self.line_chart_mode, marker_x)

    def _update_marker_pct(self, x, y):
        '''
        Synchronize the marker percent based on the x / y screen position
        '''
        mouse_x = x - self.pos[0]
        width = self.size[0]
        pct = mouse_x / width
        self.marker_pct = pct

    def _dispatch_marker(self, x, y):
        '''
        Update the marker and notify parent about marker selection
        '''
        data_index = self._get_adjusted_offset()
        self.ids.chart.marker_x = data_index

        self._update_x_marker_value()

        for channel_plot in self._channel_plots.itervalues():
            try:
                value_index = bisect.bisect_right(channel_plot.chart_x_index.keys(), data_index)
                index = channel_plot.chart_x_index.values()[value_index]
                marker = MarkerEvent(int(index), channel_plot.sourceref)
                self.dispatch('on_marker', marker)
            except IndexError:
                pass  # don't update marker for values that don't exist.


    def on_touch_move(self, touch):
        x, y = touch.x, touch.y
        if self.collide_point(x, y):
            touches = len(self._touches)
            if touches == 1:
                # regular dragging / updating marker
                self._update_marker_pct(x, y)
                self._dispatch_marker(x, y)
            elif touches == 2:
                zoom_scaling = self.max_x * self.TOUCH_ZOOM_SCALING
                # handle pinch zoom
                touch1 = self._touches[0]
                touch2 = self._touches[1]
                distance = touch1.distance(touch2)
                delta = distance - self._initial_touch_distance
                delta = delta * (float(self.size[0]) * zoom_scaling)

                # zoom around a dynamic center between two touch points
                touch_center_x = touch1.x + ((touch2.x - touch1.x) / 2)
                width = self.size[0]
                pct = touch_center_x / width
                zoom_right = 1 / pct
                zoom_left = 1 / (1 - pct)
                zoom_left = zoom_left * delta
                zoom_right = zoom_right * delta

                self.current_x = self._touch_distance - zoom_right
                self.current_offset = self._touch_offset + zoom_left

                # Rail the zooming
                self.current_x = self.max_x if self.current_x > self.max_x else self.current_x
                self.current_x = self.current_offset + zoom_scaling if self.current_x < self.current_offset else self.current_x
                self.current_offset = 0 if self.current_offset < 0 else self.current_offset
                self.current_offset = self.current_x + zoom_scaling if self.current_offset > self.current_x else self.current_offset

                chart = self.ids.chart
                chart.xmax = self.current_x
                chart.xmin = self.current_offset
            return True

    def on_mouse_pos(self, x, pos):
        if len(self._touches) > 1:
            return False
        if not self.collide_point(pos[0], pos[1]):
            return False

        self._update_marker_pct(pos[0], pos[1])
        self._dispatch_marker(pos[0] * self.metrics_base.density, pos[1] * self.metrics_base.density)

    def remove_channel(self, channel, source_ref):
        remove = []
        for channel_plot in self._channel_plots.itervalues():
            if channel_plot.channel == channel and str(source_ref) == str(channel_plot.sourceref):
                remove.append(channel_plot)

        for channel_plot in remove:
            self.ids.chart.remove_plot(channel_plot.plot)
            del(self._channel_plots[str(channel_plot)])

        self._update_max_chart_x()

    def _update_max_chart_x(self):
        '''
        Reset max chart X dimension for the currently selected plots
        '''
        max_chart_x = 0
        for plot in self._channel_plots.itervalues():
            # Find the largest chart_x for all of the active plots
            chart_x_index = plot.chart_x_index
            try:
                last = next(reversed(chart_x_index))
                chart_x = last
                if chart_x and chart_x > max_chart_x:
                    max_chart_x = chart_x
            except StopIteration:  # iterator is empty so just continue
                pass

        # update chart zoom range
        self.current_offset = 0
        self.current_x = max_chart_x
        self.max_x = max_chart_x

        self.ids.chart.xmin = self.current_offset
        self.ids.chart.xmax = self.current_x


    def _add_channels_results_time(self, channels, query_data):
        try:
            time_data_values = query_data['Interval']
            for channel in channels:
                chart = self.ids.chart
                channel_data_values = query_data[channel]
                channel_data = channel_data_values.values
                # If we queried a channel that has no sample results, skip adding the plot
                if len(channel_data) == 0 or channel_data[0] is None:
                    continue

                key = channel_data_values.channel + str(channel_data_values.source)
                plot = SmoothLinePlot(color=self.color_sequence.get_color(key))
                channel_plot = ChannelPlot(plot,
                                           channel_data_values.channel,
                                           channel_data_values.min,
                                           channel_data_values.max,
                                           channel_data_values.source)

                chart.add_plot(plot)
                points = []
                time_index = OrderedDict()
                sample_index = 0
                time_data = time_data_values.values
                sample_count = len(time_data)
                interval = max(1, int(sample_count / self.MAX_SAMPLES_TO_DISPLAY))
                Logger.info('LineChart: plot interval {}'.format(interval))
                last_time = None
                time = 0
                last_time = time_data[0]
                while sample_index < sample_count:
                    current_time = time_data[sample_index]
                    if last_time > current_time:
                        Logger.warn('LineChart: interruption in interval channel, possible reset in data stream ({}->{})'.format(last_time, current_time))
                        last_time = current_time
                    sample = channel_data[sample_index]
                    time += current_time - last_time
                    last_time = current_time
                    points.append((time, sample))
                    time_index[time] = sample_index
                    sample_index += interval

                channel_plot.chart_x_index = time_index
                plot.ymin = channel_data_values.min
                plot.ymax = channel_data_values.max
                plot.points = points
                self._channel_plots[str(channel_plot)] = channel_plot

                # sync max chart x dimension
                self._update_max_chart_x()
                self._update_x_marker_value()
        finally:
            ProgressSpinner.decrement_refcount()


    def _add_channels_results_distance(self, channels, query_data):
        try:
            distance_data_values = query_data['Distance']
            for channel in channels:
                chart = self.ids.chart
                channel_data_values = query_data[channel]

                key = channel_data_values.channel + str(channel_data_values.source)
                plot = SmoothLinePlot(color=self.color_sequence.get_color(key))
                channel_plot = ChannelPlot(plot,
                                           channel_data_values.channel,
                                           channel_data_values.min,
                                           channel_data_values.max,
                                           channel_data_values.source)

                chart.add_plot(plot)
                points = []
                distance_index = OrderedDict()
                sample_index = 0
                distance_data = distance_data_values.values
                channel_data = channel_data_values.values
                sample_count = len(distance_data)
                interval = max(1, int(sample_count / self.MAX_SAMPLES_TO_DISPLAY))
                Logger.info('LineChart: plot interval {}'.format(interval))
                while sample_index < sample_count:
                    sample = channel_data[sample_index]
                    distance = distance_data[sample_index]
                    points.append((distance, sample))
                    distance_index[distance] = sample_index
                    sample_index += interval

                channel_plot.chart_x_index = distance_index
                plot.ymin = channel_data_values.min
                plot.ymax = channel_data_values.max
                plot.points = points
                self._channel_plots[str(channel_plot)] = channel_plot

                # sync max chart distances
                self._update_max_chart_x()
                self._update_x_marker_value()

        finally:
            ProgressSpinner.decrement_refcount()

    def _results_has_distance(self, results):
        distance_values = results.get('Distance')
        interval_values = results.get('Interval')
        # Some sanity checking
        if not (distance_values and interval_values):
            return False

        distance_values = distance_values.values
        interval_values = interval_values.values
        if not (len(distance_values) > 0 and len(interval_values) > 0):
            return False

        # calculate the ratio of total distance / time
        total_time_ms = interval_values[-1] - interval_values[0]
        total_distance = distance_values[-1]
        distance_ratio = total_distance / total_time_ms if total_time_ms > 0 else 0

        Logger.debug('Checking distance threshold. Time: {} Distance: {} Ratio: {}'.format(total_time_ms, total_distance, distance_ratio))
        return distance_ratio > LineChart.MEANINGFUL_DISTANCE_RATIO_THRESHOLD

    def _add_unselected_channels(self, channels, source_ref):
        ProgressSpinner.increment_refcount()
        def get_results(results):
            # Auto-switch to time mode in charts only if the user
            # did not request it.
            if (
                    self.line_chart_mode == LineChartMode.DISTANCE and
                    not self._results_has_distance(results)
                ):
                    if self._user_refresh_requested == True:
                        toast("Warning: one or more selected laps have missing distance data", length_long=True)
                        self._user_refresh_requested = False
                    else:
                        self.line_chart_mode = LineChartMode.TIME
                        self._refresh_chart_mode_toggle()

            # clone the incoming list of channels and pass it to the handler
            if self.line_chart_mode == LineChartMode.TIME:
                Clock.schedule_once(lambda dt: self._add_channels_results_time(channels[:], results))
            elif self.line_chart_mode == LineChartMode.DISTANCE:
                Clock.schedule_once(lambda dt: self._add_channels_results_distance(channels[:], results))
            else:
                Logger.error('LineChart: Unknown line chart mode ' + str(self.line_chart_mode))
        try:
            self.datastore.get_channel_data(source_ref, ['Interval', 'Distance'] + channels, get_results)
        except Exception as e:
            Logger.warn('Non existant channel selected, not loading channels {}; {}'.format(channels, e))
        finally:
            ProgressSpinner.decrement_refcount()

    def _redraw_plots(self):
        selected_channels = self.selected_channels
        for channel in selected_channels:
            self._remove_channel_all_laps(channel)
        self._add_channels_all_laps(selected_channels)

    def _customized(self, instance, values):
        # Update selected channels
        updated_channels = values.current_channels
        if self.selected_channels != updated_channels:
            self.select_channels(updated_channels)
            self.dispatch('on_channel_selected', updated_channels)

        # update plot mode
        if self.line_chart_mode != values.line_chart_mode:
            self.line_chart_mode = values.line_chart_mode
            self._refresh_chart_mode_toggle()
            self._redraw_plots()

    def on_options(self, *args):
        params = CustomizeParams(settings=self.settings, datastore=self.datastore)
        values = CustomizeValues(list(self.selected_channels), self.line_chart_mode)

        content = OptionsView(values)
        content.add_options_screen(CustomizeChannelsScreen(name='Channels', params=params, values=values), ChannelsOptionsButton())
        content.add_options_screen(CustomizeChartScreen(name='Chart', params=params, values=values), ChartOptionsButton())

        popup = Popup(title="Customize Chart", content=content, size_hint=(0.7, 0.7))
        content.bind(on_customized=self._customized)
        content.bind(on_close=lambda *args:popup.dismiss())
        popup.open()


class CustomizeParams(object):
    '''
    A container class for holding multiple parameter for customization dialog
    '''
    def __init__(self, settings, datastore, **kwargs):
        self.settings = settings
        self.datastore = datastore

class CustomizeValues(object):
    '''
    A container class for holding customization values
    '''
    def __init__(self, current_channels, line_chart_mode, **kwargs):
        self.current_channels = current_channels
        self.line_chart_mode = line_chart_mode

class ChannelsOptionsButton(LabelIconButton):
    '''
    Button for Configuring channels
    '''
    Builder.load_string('''
<ChannelsOptionsButton>:
    title: 'Channels'
    icon_size: self.height * .9
    title_font_size: self.height * 0.6
    icon: u'\uf03a'    
    ''')

class ChartOptionsButton(LabelIconButton):
    '''
    Button for configuring chart options
    '''
    Builder.load_string('''
<ChartOptionsButton>:
    title: 'Chart'
    icon_size: self.height * .9
    title_font_size: self.height * 0.6
    icon: u'\uf080'    
    ''')

class CustomizeChartScreen(BaseOptionsScreen):
    '''
    The customization view for customizing the various chart options
    '''
    Builder.load_string('''
<CustomizeChartScreen>:
    BoxLayout:
        orientation: 'vertical'
        HSeparator:
            text: 'Plot Type'
            size_hint_y: 0.2
        BoxLayout:
            size_hint_y: 0.2
            orientation: 'horizontal'
            CheckBox:
                size_hint_x: 0.2
                group: 'x_plot_type'
                id: plot_time
                on_active: root.on_plot_type_time()
            LabelButton:
                size_hint_x: 0.4
                text: 'Time'
                font_size: self.height * 0.4
                on_press: root.on_label_plot_time()
            CheckBox:
                size_hint_x: 0.2
                group: 'x_plot_type'
                id: plot_distance
                on_active: root.on_plot_type_distance()
            LabelButton:
                size_hint_x: 0.4
                text: 'Distance'
                font_size: self.height * 0.4
                on_press: root.on_label_plot_distance()
        BoxLayout:
            size_hint_y: 0.6
    ''')

    def __init__(self, params, values, **kwargs):
        super(CustomizeChartScreen, self).__init__(params, values, **kwargs)

    def on_enter(self):
        if self.initialized == False:
            self._update_plot_type_view(self.values.line_chart_mode)
            self.initialized = True

    def _update_plot_type(self, plot_type):
        if self.initialized:
            self.values.line_chart_mode = plot_type
            self.dispatch('on_screen_modified', self.values)

    def _update_plot_type_view(self, plot_type):
        if plot_type == LineChartMode.DISTANCE:
            self.ids.plot_time.active = False
            self.ids.plot_distance.active = True
        elif plot_type == LineChartMode.TIME:
            self.ids.plot_distance.active = False
            self.ids.plot_time.active = True
        else:
            Logger.error("CustomizeChartScreen: Unknown plot plot_type: {}".format(plot_type))

    def on_label_plot_distance(self):
        self._update_plot_type_view(LineChartMode.DISTANCE)

    def on_label_plot_time(self):
        self._update_plot_type_view(LineChartMode.TIME)

    def on_plot_type_time(self):
        if self.ids.plot_time.active:
            self._update_plot_type(LineChartMode.TIME)

    def on_plot_type_distance(self):
        if self.ids.plot_distance.active:
            self._update_plot_type(LineChartMode.DISTANCE)

class CustomizeChannelsScreen(BaseOptionsScreen):
    '''
    The customization view for customizing the selected channels
    '''
    Builder.load_string('''
<CustomizeChannelsScreen>:
    ''')

    def __init__(self, params, values, **kwargs):
        super(CustomizeChannelsScreen, self).__init__(params, values, **kwargs)
        self.params = params
        self.values = values


    def on_modified(self, *args):
        self.values.current_channels = args[1]
        super(CustomizeChannelsScreen, self).on_modified(*args)

    def on_enter(self):
        if self.initialized == False:
            content = CustomizeChannelsView(datastore=self.params.datastore, current_channels=self.values.current_channels)
            content.bind(on_channels_customized=self.on_modified)
            self.add_widget(content)
            self.initialized = True

