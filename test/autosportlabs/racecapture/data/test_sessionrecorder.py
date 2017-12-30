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

import unittest
from mock import Mock, patch
from autosportlabs.racecapture.data.sessionrecorder import SessionRecorder
import Queue

class TestSessionRecorder(unittest.TestCase):

    def setUp(self):
        self.mock_rcp_api = Mock()
        self.mock_databus = Mock()
        self.mock_datastore = Mock()
        self.mock_track_manager = Mock()
        self.mock_trigger = Mock()
        self.mock_status_pump = Mock()
        self.mock_settings = Mock()

        self.mock_track_manager.find_nearby_tracks = Mock(return_value=[])
        self.mock_databus.getMeta = Mock(return_value=None)
        self.mock_rcp_api.add_connect_listener = Mock()
        self.mock_rcp_api.add_disconnect_listener = Mock()
        self.mock_databus.addMetaListener = Mock()
        self.mock_databus.addSampleListener = Mock()
        self.mock_datastore.create_session = Mock(return_value=1)
        self.mock_datastore.init_session = Mock(return_value=1)
        self.mock_datastore.get_sessions = Mock(return_value=[])
        self.mock_status_pump.add_listener = Mock()

    def test_starts(self):

        session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                           self.mock_settings, self.mock_track_manager, self.mock_status_pump)

        # Should not be recording yet, not connected to RCP and not on dash screen
        self.assertFalse(session_recorder.recording, "Does not record if not connected to RCP, view is not 'dash'\
         and no meta")

        session_recorder.on_view_change('dash')
        self.assertFalse(session_recorder.recording, "Does not record if not connected to RCP and no meta")

        # Get subscription to connect event and call it
        connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
        connect_listener()
        self.assertFalse(session_recorder.recording, "Does not record if connected to RCP and no meta")

        # Get meta subscription and call it
        meta_listener = self.mock_databus.addMetaListener.call_args[0][0]
        meta_listener({"foo": "bar"})
        self.assertTrue(session_recorder.recording, "Records when all conditions met")

    def test_creates_session(self):
        self.mock_databus.getMeta = Mock(return_value={"foo": "bar"})

        session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                           self.mock_settings, self.mock_track_manager, self.mock_status_pump)

        session_recorder.on_view_change('dash')
        # Get subscription to connect event and call it
        connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
        connect_listener()

        self.assertEqual(len(self.mock_datastore.init_session.mock_calls), 1, "Creates a new session")

    def test_creates_stop_timer_on_view_change(self):
        self.mock_databus.getMeta = Mock(return_value={"foo": "bar"})

        with patch('autosportlabs.racecapture.data.sessionrecorder.Clock.create_trigger') as mock_create_trigger:
            mock_create_trigger.return_value = self.mock_trigger
            session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                               self.mock_settings, self.mock_track_manager, self.mock_status_pump)

            session_recorder.on_view_change('dash')
            mock_create_trigger.assert_called_with(session_recorder._actual_stop, 120)
            self.mock_trigger.is_triggered = False

            # Get subscription to connect event and call it
            connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
            connect_listener()

            self.assertTrue(session_recorder.recording, "Session recorder is recording")

            session_recorder.on_view_change('analysis')
            self.mock_trigger.assert_called_with()

    def test_cancels_stop_timer_on_view_change(self):
        self.mock_databus.getMeta = Mock(return_value={"foo": "bar"})

        with patch('autosportlabs.racecapture.data.sessionrecorder.Clock.create_trigger') as mock_create_trigger:
            mock_create_trigger.return_value = self.mock_trigger
            session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                               self.mock_settings, self.mock_track_manager, self.mock_status_pump)

            session_recorder.on_view_change('dash')
            mock_create_trigger.assert_called_with(session_recorder._actual_stop, 120)
            self.mock_trigger.is_triggered = True

            # Get subscription to connect event and call it
            connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
            connect_listener()

            self.assertTrue(session_recorder.recording, "Session recorder is recording")

            session_recorder.on_view_change('analysis')

            session_recorder.on_view_change('dash')
            self.mock_trigger.cancel.assert_called_with()

    def test_stop_timer_on_view_change_with_zero_delay(self):
        self.mock_databus.getMeta = Mock(return_value={"foo": "bar"})

        session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                           self.mock_settings, self.mock_track_manager, self.mock_status_pump, stop_delay=0)

        session_recorder.on_view_change('dash')
        # Get subscription to connect event and call it
        connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
        connect_listener()

        self.assertTrue(session_recorder.recording, "Session recorder is recording")

        session_recorder.on_view_change('analysis')
        self.assertFalse(session_recorder.recording, "Session recorder stops recording when view changes to\
         non-recording view")

    def test_should_stay_running_on_disconnect(self):
        self.mock_databus.getMeta = Mock(return_value={"foo": "bar"})

        session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                           self.mock_settings, self.mock_track_manager, self.mock_status_pump)

        session_recorder.on_view_change('dash')
        # Get subscription to connect event and call it
        connect_listener = self.mock_rcp_api.add_connect_listener.call_args[0][0]
        connect_listener()

        self.assertTrue(session_recorder.recording, "Session recorder is recording")

        disconnect_listener = self.mock_rcp_api.add_disconnect_listener.call_args[0][0]
        disconnect_listener()
        self.assertTrue(session_recorder.recording, "Session recorder stops recording on disconnect")

    def test_on_sample(self):
        # warning: this is test is  necessarily slow, as it involves timing the queue performance.
        session_recorder = SessionRecorder(self.mock_datastore, self.mock_databus, self.mock_rcp_api,
                                           self.mock_settings, self.mock_track_manager, self.mock_status_pump)
        
	q = session_recorder._sample_queue
        session_recorder.recording = True

	sampleIn = { 'v': 0 }
	session_recorder._on_sample( sampleIn )
	sampleOut = q.get( True, 0 )
        self.assertTrue(sampleIn == sampleOut, "Session recorder basic queue test")

	i = 0
        while not session_recorder._sample_queue_full:
            session_recorder._on_sample( { 'v': i } )
            i += 1

        self.assertTrue( session_recorder._sample_send_delay
            == SessionRecorder.SAMPLE_QUEUE_MAX_SEND_DELAY_MS,
                "Session recorder is slowing sample rate" )
        
        for i in range( 0, SessionRecorder.SAMPLE_QUEUE_MAX_SIZE * 2 ):
            session_recorder._on_sample( { 'v': i } )
            try:
                sampleOut = q.get( True, 0 )
                sampleOut = q.get( True, 0 )
            except Queue.Empty:
                pass

        self.assertTrue( session_recorder._sample_send_delay
            == SessionRecorder.SAMPLE_QUEUE_MIN_SEND_DELAY_MS,
                "Session recorder is restoring max sample rate" )
        

def main():
    unittest.main()

if __name__ == "__main__":
    main()
