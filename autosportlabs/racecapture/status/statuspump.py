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
from kivy.logger import Logger
from kivy.clock import Clock
from time import sleep
from threading import Thread, Event
from autosportlabs.util.threadutil import safe_thread_exit


"""Responsible for querying status from the RaceCapture API
"""
class StatusPump(object):

    # how often we query for status
    STATUS_QUERY_INTERVAL_SEC = 1.0

    # How long we wait for an status message
    READY_WAIT_TIMEOUT_SEC = 5.0

    # Connection to the RC API
    _rc_api = None

    # Things that care about status updates
    _listeners = []

    # Worker Thread
    _status_thread = None

    # signals if thread should continue running
    _running = Event()

    # signals if the thread is ready to send another status request
    _ready = Event()

    def add_listener(self, listener):
        self._listeners.append(listener)

    def start(self, rc_api):
        if self._status_thread is not None and \
           self._status_thread.is_alive():
            Logger.info('StatusPump: Already running')
            return

        self._rc_api = rc_api
        t = Thread(target=self.status_worker)
        self._running.set()
        self._ready.clear()
        t.start()
        self._status_thread = t

    def stop(self):
        self._running.clear()
        self._ready.set()
        try:
            if self._status_thread:
                self._status_thread.join()
        except Exception as e:
            Logger.warn('StatusPump: failed to join status_worker: {}'.format(e))

    def status_worker(self):
        Logger.info('StatusPump: status_worker starting')
        self._rc_api.addListener('status', self._on_status_updated)
        while self._running.is_set():
            self._rc_api.get_status()
            sleep(StatusPump.STATUS_QUERY_INTERVAL_SEC)
            if not self._ready.wait(StatusPump.READY_WAIT_TIMEOUT_SEC):
                Logger.warn('StatusPump: timed out waiting for status response')

        Logger.info('StatusPump: status_worker exited')
        safe_thread_exit()

    def _update_all_listeners(self, status):
        for listener in self._listeners:
            listener(status)

    def _on_status_updated(self, status, source):
        self._ready.set()
        Clock.schedule_once(lambda dt: self._update_all_listeners(status))
