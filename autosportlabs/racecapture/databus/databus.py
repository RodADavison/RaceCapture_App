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

from kivy.clock import Clock
from time import sleep
from kivy.logger import Logger
from threading import Thread, Event, Lock
from autosportlabs.racecapture.data.channels import ChannelMeta
from autosportlabs.racecapture.data.sampledata import Sample, SampleMetaException, ChannelMetaCollection
from autosportlabs.racecapture.databus.filter.bestlapfilter import BestLapFilter
from autosportlabs.racecapture.databus.filter.laptimedeltafilter import LaptimeDeltaFilter
from autosportlabs.util.threadutil import safe_thread_exit
from autosportlabs.racecapture.config.rcpconfig import Capabilities
from utils import is_mobile_platform

DEFAULT_DATABUS_UPDATE_INTERVAL = 0.02  # 50Hz UI update rate

class DataBusFactory(object):
    def create_standard_databus(self, system_channels):
        databus = DataBus()
        databus.add_data_filter(BestLapFilter(system_channels))
        databus.add_data_filter(LaptimeDeltaFilter(system_channels))
        return databus

class DataBus(object):
    """Central hub for current sample data. Receives data from DataBusPump
    Also contains the periodic updater for listeners. Updates occur in the UI thread via Clock.schedule_interval
    Architecture:    
    (DATA SOURCE) => DataBus => (LISTENERS)
    
    Typical use:
    (CHANNEL LISTENERS) => DataBus.addChannelListener()  -- listeners receive updates with a particular channel's value
    (META LISTENERS) => DataBus.addMetaListener() -- Listeners receive updates with meta data

    Note: DataBus must be started via start_update before any data flows
    """
    channel_metas = {}
    channel_data = {}
    sample = None
    channel_listeners = {}
    meta_listeners = []
    meta_updated = False
    data_filters = []
    sample_listeners = []
    _polling = False
    rcp_meta_read = False

    def __init__(self, **kwargs):
        super(DataBus, self).__init__(**kwargs)
        self.update_lock = Lock()

    def start_update(self, interval=DEFAULT_DATABUS_UPDATE_INTERVAL):
        if self._polling:
            return

        Clock.schedule_interval(self.notify_listeners, interval)
        self._polling = True

    def stop_update(self):
        Clock.unschedule(self.notify_listeners)
        self._polling = False

    def _update_datafilter_meta(self, datafilter):
        channel_metas = self.channel_metas
        metas = datafilter.get_channel_meta(channel_metas)
        cm = self.channel_metas
        for channel, meta in metas.iteritems():
            cm[channel] = meta

    def update_channel_meta(self, metas):
        """update channel metadata information
        This should be called when the channel information has changed
        """
        try:
            self.update_lock.acquire()
            # update channel metadata
            cd = self.channel_data
            cm = self.channel_metas
            # clear our list of channel data values, in case channels
            # were removed on this metadata update
            cd.clear()

            # clear and reload our channel metas
            cm.clear()
            for meta in metas.channel_metas:
                cm[meta.name] = meta

            # add channel meta for existing filters
            for f in self.data_filters:
                self._update_datafilter_meta(f)

            self.meta_updated = True
            self.rcp_meta_read = True
        finally:
            self.update_lock.release()

    def addSampleListener(self, callback):
        self.sample_listeners.append(callback)

    def update_samples(self, sample):
        """Update channel data with new samples
        """
        try:
            self.update_lock.acquire()
            cd = self.channel_data
            for sample_item in sample.samples:
                channel = sample_item.channelMeta.name
                value = sample_item.value
                cd[channel] = value

            # apply filters to updated data
            for f in self.data_filters:
                f.filter(cd)
        finally:
            self.update_lock.release()

    def notify_listeners(self, dt):

        try:
            self.update_lock.acquire()
            if self.meta_updated:
                cm = self.channel_metas
                self.notify_meta_listeners(cm)
                self.meta_updated = False

            cd = self.channel_data
            for channel, value in cd.iteritems():
                self.notify_channel_listeners(channel, value)

            for listener in self.sample_listeners:
                listener(cd)
        finally:
            self.update_lock.release()

    def notify_channel_listeners(self, channel, value):
        listeners = self.channel_listeners.get(str(channel))
        if listeners:
            for listener in listeners:
                listener(value)

    def notify_meta_listeners(self, channelMeta):
        for listener in self.meta_listeners:
            listener(channelMeta)

    def addChannelListener(self, channel, callback):
        listeners = self.channel_listeners.get(channel)
        if listeners == None:
            listeners = [callback]
            self.channel_listeners[channel] = listeners
        else:
            listeners.append(callback)

    def removeChannelListener(self, channel, callback):
        try:
            listeners = self.channel_listeners.get(channel)
            if listeners:
                listeners.remove(callback)
        except:
            pass

    def remove_sample_listener(self, listener):
        '''
        Remove the specified sample listener
        :param listener
        :type object / callback function
        '''
        try:
            self.sample_listeners.remove(listener)
        except Exception as e:
            Logger.debug('Could not remove sample listener {}: {}'.format(listener, e))

    def remove_meta_listener(self, listener):
        '''
        Remove the specified meta listener
        :param listener
        :type object / callback function
        '''
        try:
            self.meta_listeners.remove(listener)
        except Exception as e:
            Logger.debug('Could not remove meta listener {}: {}'.format(listener, e))

    def add_sample_listener(self, callback):
        self.sample_listeners.append(callback)

    def addMetaListener(self, callback):
        self.meta_listeners.append(callback)

    def add_data_filter(self, datafilter):
        self.data_filters.append(datafilter)
        self._update_datafilter_meta(datafilter)

    def getMeta(self):
        return self.channel_metas

    def getData(self, channel):
        return self.channel_data[channel]


class DataBusPump(object):
    """Responsible for dispatching raw JSON API messages into a format the DataBus can consume.
    Attempts to detect asynchronous messaging mode, where messages are streamed to the DataBusPump.
    If Async mode not detected, a polling thread is created to simulate this.
    """
    # Telemetry rate when we're actively needing the stream (logging, dashboard, etc)
    TELEMETRY_RATE_ACTIVE_HZ = 50
    # Telemetry rate when we're idle
    TELEMETRY_RATE_IDLE_HZ = 1

    SAMPLE_POLL_EXCEPTION_RECOVERY = 10.0
    SAMPLES_TO_WAIT_FOR_META = 5

    # Main app views that the DataBusPump should set the active telemetry rate
    TELEMETRY_ACTIVE_VIEWS = ['dash']

    def __init__(self, **kwargs):
        super(DataBusPump, self).__init__(**kwargs)

        self._rc_api = None
        self._data_bus = None
        self.sample = Sample()
        self._sample_event = Event()
        self._poll = Event()
        self._sample_thread = None
        self._meta_is_stale_counter = 0

        self.rc_capabilities = None
        self._should_run = False
        self._running = False
        self._starting = False
        self._auto_streaming_supported = False
        self._current_view = None
        self._is_recording = False

    @property
    def is_telemetry_active(self):
        return self._current_view in DataBusPump.TELEMETRY_ACTIVE_VIEWS or self._is_recording

    @property
    def current_sample_rate(self):
        return DataBusPump.TELEMETRY_RATE_ACTIVE_HZ if self.is_telemetry_active else DataBusPump.TELEMETRY_RATE_IDLE_HZ

    def on_view_change(self, view_name):
        """
        View change listener, if the view being displayed is a view we want to record for, start recording.
        If not and we are currently recording, stop
        :param view_name:
        :return:
        """
        self._current_view = view_name
        self._start_telemetry()

    def _on_session_recording(self, instance, is_recording):
        self._is_recording = is_recording
        self._start_telemetry()

    def _start_telemetry(self):
        capabilities = self.rc_capabilities
        if capabilities is not None and capabilities.has_streaming:
            self._rc_api.start_telemetry(self.current_sample_rate)

    def start(self, data_bus, rc_api, session_recorder, auto_streaming_supported):
        Logger.debug("DataBusPump: start()")

        if self._running or self._starting:
            Logger.debug("DataBusPump: start(), already running, aborting")
            return

        self._should_run = True
        self._auto_streaming_supported = auto_streaming_supported

        if self._poll.is_set():
            # since we're already running, simply
            # request updated metadata
            self.meta_is_stale()
            return

        self._rc_api = rc_api
        self._data_bus = data_bus
        self._session_recorder = session_recorder
        session_recorder.bind(on_recording=self._on_session_recording)
        rc_api.addListener('s', self.on_sample)
        rc_api.addListener('meta', self.on_meta)
        rc_api.add_connect_listener(self.on_connect)
        rc_api.add_disconnect_listener(self.on_disconnect)

        self._start()

    def _start(self):
        if self._running or self._starting:
            Logger.debug("DataBusPump: _start(), already running or starting, aborting")
            return

        self._poll.set()

        # Only BT supports auto-streaming data, the rest we have to stream or poll
        if not self._auto_streaming_supported:
            self._start_sample_streaming()

    def on_connect(self):
        if self._should_run:
            self._start()

    def on_disconnect(self):
        self._stop(True)

    def _start_sample_streaming(self):
        # First need to figure out if the connected RC supports the streaming api
        Logger.info("DataBusPump: Checking for streaming API support")

        def handle_capabilities(capabilities_dict):
            self.rc_capabilities = Capabilities()
            self.rc_capabilities.from_json_dict(capabilities_dict['capabilities'])

            if self.rc_capabilities.has_streaming:
                # Send streaming command
                Logger.info("DataBusPump: device supports streaming")
                self._start_telemetry()
            else:
                Logger.info("DataBusPump: connected device does not support streaming api")
                self._start_polling_telemetry()

            self._running = True

        def handle_capabilities_fail(*args):
            Logger.error("DataBusPump: Failed to get capabilities, can't determine if device supports streaming API. Assuming polling")
            self._start_polling_telemetry()
            self._poll.set()

        self._rc_api.get_capabilities(handle_capabilities, handle_capabilities_fail)
        self._starting = True

    def _start_polling_telemetry(self):
        if self._sample_thread:
            return

        t = Thread(target=self.sample_worker)
        t.start()
        self._sample_thread = t

    def stop(self):
        """ Public method to stop databuspump
        """
        self._should_run = False
        self._stop()

    def _stop(self, disconnected=False):
        """
        Private method to stop databuspump, leaves self._should_run alone so if we're stopping because
        of a disconnect, we will start up again on reconnect
        """
        self._poll.clear()
        self._running = False
        self._starting = False

        if self.rc_capabilities and self.rc_capabilities.has_streaming and not disconnected:
            self._rc_api.stop_telemetry()
            return

        if self._sample_thread is not None:
            try:
                self._sample_thread.join()
            except Exception as e:
                Logger.warning('DataBusPump: Failed to join sample_worker: {}'.format(e))

    def on_meta(self, meta_json, source):
        metas = self.sample.metas
        metas.fromJson(meta_json.get('meta'))
        self._data_bus.update_channel_meta(metas)
        self._meta_is_stale_counter = 0

    def on_sample(self, sample_json, source):
        sample = self.sample
        dataBus = self._data_bus
        try:
            sample.fromJson(sample_json)
            if sample.updated_meta:
                dataBus.update_channel_meta(sample.metas)
            dataBus.update_samples(sample)
            self._sample_event.set()
        except SampleMetaException:
            # this is to prevent repeated sample meta requests
            self._request_meta_handler()

    def _request_meta_handler(self):
            if self._meta_is_stale_counter <= 0:
                Logger.info('DataBusPump: Sample Meta is stale, requesting meta')
                self._meta_is_stale_counter = DataBusPump.SAMPLES_TO_WAIT_FOR_META
                self.request_meta()
            else:
                self._meta_is_stale_counter -= 1

    def stopDataPump(self):
        self._poll.clear()
        self._sample_thread.join()

    def meta_is_stale(self):
        self.request_meta()

    def request_meta(self):
        self._rc_api.get_meta()

    def sample_worker(self):
        rc_api = self._rc_api
        Logger.info('DataBusPump: sample_worker polling starting')
        while self._poll.is_set():
            try:
                rc_api.sample()
                sleep(1.0 / self.current_sample_rate)
            except Exception as e:
                Logger.error('DataBusPump: Exception in sample_worker: ' + str(e))
                sleep(DataBusPump.SAMPLE_POLL_EXCEPTION_RECOVERY)

        Logger.info('DataBusPump: sample_worker exiting')
        safe_thread_exit()

