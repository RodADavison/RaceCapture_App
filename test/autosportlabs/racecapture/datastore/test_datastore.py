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

import itertools
import tempfile
import csv
import unittest
import os
import os.path
from collections import namedtuple
from autosportlabs.racecapture.datastore.datastore import DataStore, Filter, \
    DataSet, _interp_dpoints, _smooth_dataset, _scrub_sql_value


fqp = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(fqp, 'rctest.sql3')
log_path = os.path.join(fqp, 'rc_adj.log')
import_export_path = os.path.join(fqp, 'import_export.log')

# NOTE! that


class DataStoreTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.ds = DataStore()

        if os.path.exists(db_path):
            os.remove(db_path)

        self.ds.open_db(db_path)
        self._import_initial_data()

    @classmethod
    def tearDownClass(self):
        self._delete_all_sessions()
        self.ds.close()
        os.remove(db_path)

    @classmethod
    def _import_initial_data(self):
        try:
            self.ds.import_datalog(log_path, 'rc_adj', 'the notes')
        except:
            import sys
            import traceback
            print "Exception importing datalog:"
            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60

    @classmethod
    def _delete_all_sessions(self):
        sessions = self.ds.get_sessions()
        for session in sessions:
            self.ds.delete_session(session.session_id)

    def test_delete_session(self):
        session_id = self.ds.import_datalog(log_path, 'rc_adj', 'the notes')
        self.ds.delete_session(session_id)
        session = self.ds.get_session_by_id(session_id)
        self.assertIsNone(session)

    def test_basic_filter(self):
        f = Filter().lt('LapCount', 1)

        expected_output = 'datapoint.LapCount < ?'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)
        self.assertListEqual(f.params, [1])

    def test_not_equal_filter(self):
        f = Filter().neq('LapCount', 1)

        expected_output = 'datapoint.LapCount != ?'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)
        self.assertListEqual(f.params, [1])

    def test_chained_filter(self):
        f = Filter().lt('LapCount', 1).gt('Coolant', 212).or_().eq('RPM', 9001)

        expected_output = 'datapoint.LapCount < ? AND datapoint.Coolant > ? OR datapoint.RPM = ?'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)
        self.assertListEqual(f.params, [1, 212, 9001])

    def test_grouped_filter(self):
        f = Filter().lt('LapCount', 1).group(
            Filter().gt('Coolant', 212).or_().gt('RPM', 9000))

        expected_output = 'datapoint.LapCount < ? AND (datapoint.Coolant > ? OR datapoint.RPM > ?)'
        filter_text = str(f).strip()

        self.assertSequenceEqual(filter_text, expected_output)
        self.assertListEqual(f.params, [1, 212, 9000])

    def test_dataset_columns(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        expected_channels = ['Coolant', 'RPM', 'MAP', 'session_id']
        dset_channels = dataset.channels

        # Sort both lists to ensure that they'll compare properly
        expected_channels.sort()
        dset_channels.sort()

        self.assertListEqual(expected_channels, dset_channels)

    def test_dataset_val_count(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        samples = dataset.fetch_columns(100)

        for k in samples.keys():
            self.assertEqual(len(samples[k]), 100)

    def test_dataset_record_oriented(self):
        f = Filter().lt('LapCount', 1)
        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'],
                                data_filter=f)

        records = dataset.fetch_records(100)

        self.assertEqual(len(records), 100)

    def test_channel_average(self):
        lat_avg = self.ds.get_channel_average("Latitude")
        lon_avg = self.ds.get_channel_average("Longitude")
        self.assertEqual(round(lat_avg, 6), 47.256164)
        self.assertEqual(round(lon_avg, 6), -123.191297)

    def test_channel_average_by_session(self):
        # session exists
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[1])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[1])
        self.assertEqual(47.256164, round(lat_avg, 6))
        self.assertEqual(-123.191297, round(lon_avg, 6))

        # session does not exist
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[2])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[2])
        self.assertEqual(None, lat_avg)
        self.assertEqual(None, lon_avg)

        # include an existing and not existing session
        lat_avg = self.ds.get_channel_average("Latitude", sessions=[1, 2])
        lon_avg = self.ds.get_channel_average("Longitude", sessions=[1, 2])
        self.assertEqual(47.256164, round(lat_avg, 6))
        self.assertEqual(-123.191297, round(lon_avg, 6))

    def test_channel_min_max(self):
        rpm_min = self.ds.get_channel_min('RPM')
        rpm_max = self.ds.get_channel_max('RPM')

        self.assertEqual(rpm_min, 498.0)
        self.assertEqual(rpm_max, 6246.0)

        # with extra channels
        rpm_min = self.ds.get_channel_min('RPM', extra_channels=['LapCount'])
        rpm_max = self.ds.get_channel_max('RPM', extra_channels=['LapCount'])

        self.assertEqual(rpm_min[0], 498.0)
        self.assertEqual(rpm_max[0], 6246.0)
        self.assertEqual(rpm_min[1], 37)
        self.assertEqual(rpm_max[1], 12)

    def test_interpolation(self):
        dset = [1., 1., 1., 1., 5.]

        smooth_list = _interp_dpoints(1, 5, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5.])

    def test_smoothing_even_bound(self):
        dset = [1., 1., 1., 1., 5.]
        smooth_list = _smooth_dataset(dset, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5.])

    def test_smoothing_offset_bound(self):
        dset = [1., 1., 1., 1., 5., 5., 5., 2]
        smooth_list = _smooth_dataset(dset, 4)

        self.assertListEqual(smooth_list, [1., 2., 3., 4., 5., 4., 3., 2.])

    def test_channel_set_get_smoothing(self):
        success = None
        smoothing_rate = 0
        # positive case, this would appropriately set the smoothing

        self.ds.set_channel_smoothing('RPM', 10)

        smoothing_rate = self.ds.get_channel_smoothing('RPM')

        self.assertEqual(smoothing_rate, 10)

        # reset the smoothing rate so we don't interfere with other tests
        self.ds.set_channel_smoothing('RPM', 1)

        smoothing_rate = self.ds.get_channel_smoothing('RPM')
        self.assertEqual(smoothing_rate, 1)

        # Negative case, this would return an error
        try:
            self.ds.set_channel_smoothing('AverageSpeedOfASwallow', 9001)
            success = True
        except:
            success = False

        self.assertEqual(success, False)

    def test_distinct_queries(self):
        """
        This is a really basic test to ensure that we always obey the distinct keyword

        Distinct should filter out duplicate results, leading to a much smaller dataset
        """

        f = Filter().gt('LapCount', 0)
        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f)

        records = dataset.fetch_records()
        self.assertEqual(len(records), 24667)

        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f,
                                distinct_records=True)

        records = dataset.fetch_records()
        self.assertEqual(len(records), 37)

    def test_no_filter(self):
        """
        This test ensures that we can query the entire datastore without a filter
        """

        dataset = self.ds.query(sessions=[1],
                                channels=['Coolant', 'RPM', 'MAP'])

        records = dataset.fetch_records()
        self.assertEqual(len(records), 25691)

    def test_get_all_laptimes(self):

        f = Filter().gt('LapCount', 0)
        dataset = self.ds.query(sessions=[1],
                                channels=['LapCount', 'LapTime'],
                                data_filter=f,
                                distinct_records=True)

        laptimes = {}
        records = dataset.fetch_records()
        for r in records:
            laptimes[int(r[1])] = r[2]

        self.assertEqual(laptimes[1], 3.437)
        self.assertEqual(laptimes[2], 2.257)
        self.assertEqual(laptimes[3], 2.227)
        self.assertEqual(laptimes[4], 2.313)
        self.assertEqual(laptimes[5], 2.227)
        self.assertEqual(laptimes[6], 2.227)
        self.assertEqual(laptimes[7], 2.423)
        self.assertEqual(laptimes[8], 2.31)
        self.assertEqual(laptimes[9], 2.223)
        self.assertEqual(laptimes[10], 2.233)
        self.assertEqual(laptimes[11], 2.247)
        self.assertEqual(laptimes[12], 2.24)
        self.assertEqual(laptimes[13], 2.25)
        self.assertEqual(laptimes[14], 2.237)
        self.assertEqual(laptimes[15], 2.243)
        self.assertEqual(laptimes[16], 2.29)
        self.assertEqual(laptimes[17], 2.387)
        self.assertEqual(laptimes[18], 2.297)
        self.assertEqual(laptimes[19], 2.383)
        self.assertEqual(laptimes[20], 2.177)
        self.assertEqual(laptimes[21], 2.207)
        self.assertEqual(laptimes[22], 2.18)
        self.assertEqual(laptimes[23], 2.17)
        self.assertEqual(laptimes[24], 2.22)
        self.assertEqual(laptimes[25], 2.217)
        self.assertEqual(laptimes[26], 2.223)
        self.assertEqual(laptimes[27], 2.173)
        self.assertEqual(laptimes[28], 2.19)
        self.assertEqual(laptimes[29], 2.33)
        self.assertEqual(laptimes[30], 2.227)
        self.assertEqual(laptimes[31], 2.257)
        self.assertEqual(laptimes[32], 2.183)
        self.assertEqual(laptimes[33], 2.163)
        self.assertEqual(laptimes[34], 2.23)
        self.assertEqual(laptimes[35], 2.23)
        self.assertEqual(laptimes[36], 2.54)
        self.assertEqual(laptimes[37], 3.383)

    def test_get_sessions(self):
        sessions = self.ds.get_sessions()
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session.name, 'rc_adj')
        self.assertEqual(session.session_id, 1)
        self.assertEqual(session.notes, 'the notes')
        self.assertIsNotNone(session.date)

    def test_location_center(self):
        lat, lon = self.ds.get_location_center([1])
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)

    def test_update_session(self):
        session = self.ds.get_sessions()[0]
        session.name = 'name_updated'
        session.notes = 'notes_updated'
        self.ds.update_session(session)
        session = self.ds.get_sessions()[0]
        self.assertEqual('name_updated', session.name)
        self.assertEqual('notes_updated', session.notes)

    def test_export_datastore(self):
        Meta = namedtuple(
            'Meta', ['name', 'units', 'min', 'max', 'sr', 'index'])

        def parse_header_meta(headers):
            channel_metas = {}
            name_indexes = []
            index = 0
            for header in headers:
                header = header.split('|')
                meta = Meta(name=header[0],
                            units=header[1],
                            min=float(header[2]),
                            max=float(header[3]),
                            sr=int(header[4]),
                            index=index)
                index += 1
                channel_metas[meta.name] = meta
                name_indexes.append(meta.name)

            return channel_metas, name_indexes

        import_export_id = self.ds.import_datalog(
            import_export_path, 'import_export', 'the notes')

        with tempfile.TemporaryFile() as export_file:
            rows = self.ds.export_session(import_export_id, export_file)

            export_file.seek(0)

            line_count = 0
            log_reader = csv.reader(export_file, delimiter=',', quotechar=' ')

            with open(import_export_path, 'rb') as original_log:
                original_reader = csv.reader(
                    original_log, delimiter=',', quotechar=' ')

                original_metas = None
                original_indexes = None
                export_metas = None
                export_indexes = None

                for export, original in itertools.izip(log_reader, original_reader):
                    if not original_metas and not export_metas:
                        original_metas, original_indexes = parse_header_meta(
                            original)
                        export_metas, export_indexes = parse_header_meta(
                            export)
                    else:
                        for om in original_metas.values():
                            # export log can be in random order, so need to
                            # re-align
                            original_index = original_indexes.index(om.name)
                            export_index = export_indexes.index(om.name)
                            export_value = export[export_index]
                            original_value = original[original_index]

                            if len(export_value) > 0 and len(original_value) > 0:
                                export_value = float(export_value)
                                original_value = float(original_value)

                            self.assertEqual(export_value, original_value, 'Line {} : Name {} : {} != {}\noriginal: {}\nexport: {}'.format(
                                line_count, om.name, original_value, export_value, original, export))

                        line_count += 1

                self.assertEqual(
                    len(original_metas.values()), len(export_metas.values()))

                # Test headers
                for o_meta, e_meta in zip(sorted(original_metas.values()), sorted(export_metas.values())):
                    self.assertEqual(o_meta.name, e_meta.name)
                    self.assertEqual(o_meta.units, e_meta.units)
                    self.assertEqual(o_meta.min, e_meta.min)
                    self.assertEqual(o_meta.max, e_meta.max)
                    self.assertEqual(o_meta.sr, e_meta.sr)

            self.ds.delete_session(import_export_id)

    def test_scrub_sql_value(self):
        ds = self.ds
        self.assertEqual(_scrub_sql_value('ABCD1234'), '"ABCD1234"')
        self.assertEqual(_scrub_sql_value('1234ABCD'), '"1234ABCD"')
        self.assertEqual(_scrub_sql_value('ABCD 1234'), '"ABCD 1234"')
        self.assertEqual(_scrub_sql_value(' 1234ABCD'), '"1234ABCD"')
        self.assertEqual(_scrub_sql_value('1234ABCD '), '"1234ABCD"')
        self.assertEqual(
            _scrub_sql_value('!!@@##ABCD%%1234%%**'), '"!!@@##ABCD%%1234%%**"')
        self.assertEqual(_scrub_sql_value('ABCD_1234'), '"ABCD_1234"')
        self.assertEqual(_scrub_sql_value('ABCD 1234'), '"ABCD 1234"')
