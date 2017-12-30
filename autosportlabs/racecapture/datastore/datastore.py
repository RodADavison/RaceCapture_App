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

import sqlite3
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Text
from sqlturk.migration import MigrationTool
import logging
import os
import os.path
import time
import datetime
from kivy.logger import Logger
from collections import OrderedDict


class InvalidChannelException(Exception):
    pass


class DatastoreException(Exception):
    pass


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()


def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def timing(f):
    def wrap(*args):
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()
        Logger.info('Datastore: {} function took {} ms'.format(
            f.func_name, (time2 - time1) * 1000.0))
        return ret
    return wrap


def _get_interp_slope(start, finish, num_samples):
    if start == finish:
        return 0

    return float(start - finish) / float(1 - num_samples)


def _interp_dpoints(start, finish, sample_skip):
    slope = _get_interp_slope(start, finish, sample_skip + 1)

    nlist = [start]
    for i in range(sample_skip - 1):
        nlist.append(float(nlist[-1] + slope))

    nlist.append(finish)

    return nlist


def _smooth_dataset(dset, smoothing_rate):
    # Throw an error if we got a bad smoothing rate
    if not smoothing_rate or smoothing_rate < 2:
        raise DatastoreException("Invalid smoothing rate")

    # This is the dataset that we'll be returning
    new_dset = []

    # Get every nth sample from the dataset where n==smoothing_rate
    dpoints = dset[0::smoothing_rate]

    # Now, loop through the target datapoints, interpolate the values
    # between, and store them to the new dataset that we'll be
    # returning
    for index, val in enumerate(dpoints[:-1]):
        # Get the start and end points of the interpolation
        start = val
        end = dpoints[index + 1]

        # Generate the smoothed dataset
        smoothed_samples = _interp_dpoints(start, end, smoothing_rate)

        # Append everything but the last datapoint in the smoothed
        # samples to the new dataset
        # (This will be the first item in the next dataset)
        new_dset.extend(smoothed_samples[:-1])

        # If the end was the last datapoint in the original set, append
        # it as well
        if index + 1 == len(dpoints) - 1:
            new_dset.append(end)

    # Now we need to smooth out the tail end of the list (if necessary)
    if len(new_dset) < len(dset):
        # calculate the difference in lengths between the original and
        # new datasets
        len_diff = len(dset) - len(new_dset)

        # generate a new smoothed dataset for the missing elements
        tail_dset = _interp_dpoints(new_dset[-1], dset[-1], len_diff)

        # Extend our return list with everything but the tail of the
        # new_dataset (as this would cause a duplicate)
        new_dset.extend(tail_dset[1:])

    return new_dset


def _scrub_sql_value(value):
    """
    Takes a string and makes it safe for a sql parameter, and wraps it in double quotes.
    This makes it safe for use in a SQL query for things like a column name or table name. 
    Not to be confused with traditional SQL escaping with backslashes or
    parameterized queries
    :param value: String
    :return: String
    """
    value = value.strip()
    sql_name = ''.join(
        [char for char in value if char is not '"'])
    return '"{}"'.format(sql_name)


class DataSet(object):

    def __init__(self, cursor, smoothing_map=None):
        self._cur = cursor
        self._smoothing_map = smoothing_map

    @property
    def channels(self):
        return [x[0] for x in self._cur.description]

    def fetch_columns(self, count=None):
        chanmap = {}
        channels = [x[0] for x in self._cur.description]

        if count == None:
            dset = self._cur.fetchall()
        else:
            dset = self._cur.fetchmany(count)
        for c in channels:
            idx = channels.index(c)
            chan_dataset = [x[idx] for x in dset]

            # If we received a smoothing map and the smoothing rate of
            # the selected channel is > 1, smooth it out before
            # returning it to the user
            if self._smoothing_map and self._smoothing_map[c] > 1:
                chan_dataset = _smooth_dataset(
                    chan_dataset, self._smoothing_map[c])
            chanmap[c] = chan_dataset

        return chanmap

    def fetch_records(self, count=None):
        chanmap = self.fetch_columns(count)

        # We have to pull the channel datapoint lists out in the order
        # that you'd expect to find them in the data cursor
        zlist = []
        for ch in self.channels:
            zlist.append(chanmap[ch])

        return zip(*zlist)


class Session(object):

    def __init__(self, session_id, name, notes='', date=None):
        self.session_id = session_id
        self.name = name
        self.notes = notes
        self.date = date


class Lap(object):

    def __init__(self, lap, session_id, lap_time):
        self.lap = lap
        self.session_id = session_id
        self.lap_time = lap_time

# Filter container class


class Filter(object):

    def __init__(self):
        self._cmd_seq = ''
        self._comb_op = 'AND '
        self._channels = []
        self.params = []

    @property
    def channels(self):
        return self._channels[:]

    def add_combop(f):
        def wrap(self, *args, **kwargs):
            if len(self._cmd_seq):
                self._cmd_seq += self._comb_op
            ret = f(self, *args, **kwargs)
            return ret
        return wrap

    def chan_adj(f):
        def wrap(self, chan, val):
            self._channels.append(chan)
            prefix = 'datapoint.'
            chan = prefix + str(chan)
            ret = f(self, chan, val)
            return ret
        return wrap

    @add_combop
    @chan_adj
    def neq(self, chan, val):
        self._cmd_seq += '{} != ? '.format(chan, val)
        self.params.append(val)
        return self

    @add_combop
    @chan_adj
    def eq(self, chan, val):
        self._cmd_seq += '{} = ? '.format(chan, val)
        self.params.append(val)
        return self

    @add_combop
    @chan_adj
    def lt(self, chan, val):
        self._cmd_seq += '{} < ? '.format(chan, val)
        self.params.append(val)
        return self

    @add_combop
    @chan_adj
    def gt(self, chan, val):
        self._cmd_seq += '{} > ? '.format(chan, val)
        self.params.append(val)
        return self

    @add_combop
    @chan_adj
    def lteq(self, chan, val):
        self._cmd_seq += '{} <= ? '.format(chan, val)
        self.params.append(val)
        return self

    @add_combop
    @chan_adj
    def gteq(self, chan, val):
        self._cmd_seq += '{} >= ? '.format(chan, val)
        self.params.append(val)
        return self

    def and_(self):
        self._comb_op = 'AND '
        return self

    def or_(self):
        self._comb_op = 'OR '
        return self

    def __str__(self):
        return self._cmd_seq

    @add_combop
    def group(self, filterchain):
        self._cmd_seq += '({})'.format(str(filterchain).strip())
        self.params = self.params + filterchain.params
        return self


class DatalogChannel(object):

    def __init__(self, channel_name='', units='', min=0, max=0, sample_rate=0, smoothing=0):
        self.name = channel_name
        self.units = units
        self.min = min
        self.max = max
        self.sample_rate = sample_rate

    def __str__(self):
        return self.name


class DataStore(object):
    # Maximum supported sample rate
    MAX_SAMPLE_RATE = 1000

    # System channels that should show up in the first columns of a log file.
    # Ordering is important, as it indicates which order it should show up in
    # the log
    SYSTEM_CHANNELS = ['Interval', 'Utc']

    # Channels to index on, WARNING: only [A-z] channel names with no spaces
    # will work currently
    EXTRA_INDEX_CHANNELS = ["CurrentLap"]
    val_filters = ['lt', 'gt', 'eq', 'lt_eq', 'gt_eq']

    def __init__(self, databus=None):
        self._channels = []
        self._isopen = False
        self.datalogchanneltypes = {}
        self._ending_datalog_id = 0
        self._conn = None
        self._databus = databus

    def close(self):
        self._conn.close()
        self._isopen = False

    def open_db(self, db_path):
        if self._isopen:
            self.close()

        db_uri = 'sqlite:///{}'.format(db_path)

        # Perform any pending database migrations
        # Will create the database if necessary
        self._perform_migration(db_uri, 'resource/datastore/migrations')

        self._engine = create_engine(
            db_uri, connect_args={'check_same_thread': False})
        sqlite_conn = self._engine.connect()
        self._conn = sqlite_conn.connection
        sqlite_conn.detach()

        self._populate_channel_list()

        self._isopen = True

    @property
    def connection(self):
        return self._conn

    def _populate_channel_list(self):
        del self._channels[:]
        channels = self.get_channel_list()
        # remove duplicates and rail the min, max and sample rates to the
        # extents

        filtered_channels = [
            DatalogChannel(channel_name=c) for c in set([c.name for c in channels])]
        for c in filtered_channels:
            c_dup = [cd for cd in channels if c.name in cd.name]
            for d in c_dup:
                # The channel variation that has the largest
                # swing in min/max values "wins"
                if d.max - d.min > c.max - c.min:
                    c.min = d.min
                    c.max = d.max
                    c.sample_rate = d.sample_rate
                    c.units = d.units

        self._channels += filtered_channels

    @property
    def is_open(self):
        return self._isopen

    def channel_exists(self, channel):
        return channel in [x.name for x in self._channels]

    @property
    def channel_list(self):
        return self._channels[:]

    def get_channel_list(self, session_id=None):
        def move_to_front(channels, channel):
            current_index = [
                index for index, value in enumerate(channels) if value.name == channel]
            if len(current_index):
                channels.insert(0, channels.pop(current_index[0]))

        c = self._conn.cursor()

        channels = []
        where = '' if session_id is None else ' WHERE session_id = ? '
        sql = """SELECT DISTINCT name, units, min_value, max_value, sample_rate, smoothing
        from channel {} ORDER BY name ASC, min_value ASC, max_value DESC, sample_rate DESC""".format(where)

        if session_id is None:
            c.execute(sql)
        else:
            c.execute(sql, [session_id])

        for ch in c.fetchall():
            channels.append(DatalogChannel(channel_name=ch[0],
                                           units=ch[1],
                                           min=ch[2],
                                           max=ch[3],
                                           sample_rate=ch[4],
                                           smoothing=ch[5]))

        # special columns are Interval and UTC; place these at the beginning,
        # if present
        for channel in DataStore.SYSTEM_CHANNELS[::-1]:
            move_to_front(channels, channel)

        return channels

    def get_channel(self, name):
        '''
        Retreives information for a channel
        :param name the channel name
        :type name string
        :returns DatalogChannel object for the channel. Raises DatastoreException if channel is unknown
        '''
        channel = [c for c in self._channels if name in c.name]
        if not len(channel):
            raise DatastoreException("Unknown channel: {}".format(name))
        return channel[0]

    def _perform_migration(self, db_uri, migration_dir):
        tool = MigrationTool(db_uri, migration_dir=migration_dir)
        tool.install()  # create a database table to track schema changes
        Logger.info(
            'DataStore: Applying db migrations: {}'.format(tool.find_migrations()))
        tool.run_migrations()
        Logger.info('DataStore: db migrations complete')
        tool.engine.dispose()

    def _add_extra_indexes(self, channels):
        existing_indexes = []
        c = self._conn.cursor()
        for row in c.execute('PRAGMA index_list(datapoint)'):
            existing_indexes.append(row[1])

        extra_indexes = []
        for c in channels:
            name = c.name
            if name in self.EXTRA_INDEX_CHANNELS:
                extra_indexes.append(name)

        for index_channel in extra_indexes:
            index_name = '{}_index_id'.format(index_channel)
            if index_name in existing_indexes:
                continue
            self._conn.execute(
                """CREATE INDEX {} on datapoint({})""".format(_scrub_sql_value(index_name), _scrub_sql_value(index_channel)))

    def _extend_datalog_channels(self, channels):
        """
        Add new columns as needed
        """
        existing_columns = []
        c = self._conn.cursor()
        for row in c.execute('PRAGMA table_info(datapoint)'):
            existing_columns.append(_scrub_sql_value(row[1]))

        for channel in channels:
            name = _scrub_sql_value(channel.name)
            # SQLite column names are case-insensitive
            if name.upper() in (col.upper() for col in existing_columns):
                continue
            # Extend the datapoint table to include the channel as a
            # new field
            self._conn.execute("""ALTER TABLE datapoint
            ADD {} REAL""".format(name))
        self._add_extra_indexes(channels)
        self._conn.commit()

    def _parse_datalog_headers(self, header):
        raw_channels = header.split(',')
        channels = []

        try:
            for i in range(1, len(raw_channels) + 1):
                name, units, min, max, samplerate = raw_channels[
                    i - 1].replace('"', '').split('|')
                channel = DatalogChannel(
                    name, units, float(min), float(max), int(samplerate), 0)
                channels.append(channel)
        except:
            import sys
            import traceback
            print "Exception in user code:"
            print '-' * 60
            traceback.print_exc(file=sys.stdout)
            print '-' * 60
            raise DatastoreException("Unable to import datalog, bad metadata")

        return channels

    def _add_session_channels(self, session_id, channels):
            # Add the channel to the 'channel' table
        for channel in channels:
            self._conn.execute("""INSERT INTO channel (session_id, name, units, min_value, max_value, sample_rate, smoothing)
                VALUES (?,?,?,?,?,?,?)""", (session_id, channel.name, channel.units, channel.min, channel.max, channel.sample_rate, 1))

    def _get_last_table_id(self, table_name):
        """
        Returns the last used ID number (as an int) from the specified table name

        This is useful when inserting new data as we use this number to join on the datalog table
        """

        c = self._conn.cursor()
        base_sql = "SELECT * FROM SQLITE_SEQUENCE WHERE name='{}';".format(
            table_name)
        c.execute(base_sql)
        res = c.fetchone()

        if res == None:
            dl_id = 0
        else:
            dl_id = res[1]  # comes back as sample|<last id>
        return dl_id

    def insert_record(self, record, channels, session_id):
        """
        Takes a record of interpolated+extrapolated channels and their header metadata
        and inserts it into the database
        """

        cursor = self._conn.cursor()
        try:
            # First, insert into the datalog table to give us a reference
            # point for the datapoint insertions
            cursor.execute(
                """INSERT INTO sample (session_id) VALUES (?)""", [session_id])
            datalog_id = cursor.lastrowid

            # Insert the datapoints into their tables
            extrap_vals = [datalog_id] + record

            # Now, insert the record into the datalog table using the ID
            # list we built up in the previous iteration

            # Put together an insert statement containing the column names
            base_sql = "INSERT INTO datapoint ({}) VALUES({});".format(','.join(['sample_id'] + [_scrub_sql_value(x.name) for x in channels]),
                                                                       ','.join(['?'] * (len(extrap_vals) + 1)))
            cursor.execute(base_sql, extrap_vals)
            self._conn.commit()
        except:  # rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

    def commit(self):
        """
        Commit any pending changes to the database.
        """
        try:
            self._conn.commit()
        except:  # rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

    def insert_sample_nocommit(self, sample, session_id):
        """
        Insert samples which are queued to be added to the DB. 
        A subsequent commit is required before the sample will appear in the DB.
        """
        cursor = self._conn.cursor()
        try:
            # First, insert into the datalog table to give us a reference
            # point for the datapoint insertions
            cursor.execute(
                """INSERT INTO sample (session_id) VALUES (?)""", [session_id])
            sample_id = cursor.lastrowid

            values = [sample_id]
            names = []

            for channel_name, value in sample.iteritems():
                values.append(value)
                names.append(channel_name)

            # Put together an insert statement containing the column names
            base_sql = "INSERT INTO datapoint ({}) VALUES({});".format(','.join(['sample_id'] + [_scrub_sql_value(x) for x in names]),
                                                                       ','.join(['?'] * (len(values))))

            cursor.execute(base_sql, values)

        except:  # rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

    def _extrap_datapoints(self, datapoints):
        """
        Takes a list of datapoints, and returns a new list of extrapolated datapoints

        i.e: '3, nil, nil, nil, 7' (as a column) will become:
        [3, 3, 3, 3, 7]

         In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [5, 5, 5, 5]

        """

        ret_list = []

        # first we need to handle the 'start of dataset, begin on a
        # miss' case
        if datapoints[0] == None:
            ret_list = [datapoints[-1] for x in datapoints]
            return ret_list

        # Next, we need to handle the case where there are only two
        # entries and both are hits, if this is the case, we just
        # duplicate the values in the tuple for each entry and return
        # that
        if len(datapoints) == 2:
            ret_list = [x for x in datapoints]
            return ret_list

        # If we're here, it means we actually have a start and end
        # point to this data sample, have blanks in between and need
        # to interpolate+extrapolate the bits in between

        extrap_list = []
        for e in range(len(datapoints) - 1):
            extrap_list.append(datapoints[0])
        extrap_list.append(datapoints[-1])

        return extrap_list

    def _desparsified_data_generator(self, data_file, warnings=None, progress_cb=None):
        """
        Takes a racecapture pro CSV file and removes sparsity from the dataset.
        This function yields samples that have been extrapolated from the
        parent dataset.

        'extrapolated' means that we'll just carry all values forward: [3, nil, nil, nil, 7] -> [3, 3, 3, 3, 7, 7, 7...]

        So to summarize: '3, nil, nil, nil, 7' (as a column) will become:
        [3, 3, 3, 3, 7]

        In the event of the 'start' of the dataset, we may have something like:
        [nil, nil, nil, 5], in this case, we will just back extrapolate, so:
        [nil, nil, nil, 5] becomes [5, 5, 5, 5]
        """

        # Notes on this algorithm: The basic idea is that we're going
        # 100% bob barker on this data...Think Plinko.
        # We maintain 2 lists of n lists where n = the number
        # of columns we're playing with.
        # Container list 1 holds our work space, we file records into
        # it one by one into their respective columnar lists.
        # A data point containing a NIL is a 'miss', a data point
        # containing some value is a 'hit'.  We continue to file until
        # we get a 'hit'.  When that happens, we take the slice of the
        # columnar list [0:hit], extrapolate the
        # values in between, then take the slice [0:hit-1] and insert
        # it into the second container list (in the same respective
        # column).  We shift container list 1's respective columnar
        # list by [hit:], then continue on.  We do this for EACH
        # columnar list in container list 1. (In the event that we're
        # just starting out and have misses at the head of the column,
        # instead of interpolating/extrapolating between hits, we just
        # back-extrapolate and shift as expected)
        # After this operation, we shift our attention to container
        # list 2.  If there is data in each column (i.e. len(col) > 0
        # for each column), we yield a new list containing:
        # [col0[0], col1[0], col2[0],...,coln[0]] and shift each
        # column down by 1 (i.e.: [1, 2, 3] becomes [2, 3])
        # That's right, this is a generator.  Booya.

        work_list = []
        yield_list = []

        # In order to facilitate a progress callback, we need to know
        # the number of lines in the file

        # Get the current file cursor position
        start_pos = data_file.tell()

        # Count the remaining lines in the file
        line_count = sum(1 for line in data_file)
        current_line = 0

        # Reset the file cursor
        data_file.seek(start_pos)

        for line in data_file:

            try:
                # Strip the line and break it down into it's component
                # channels, replace all blank entries with None
                channels = [
                    None if x == '' else float(x) for x in line.strip().split(',')]

                # Now, if this is the first entry (characterized by
                # work_list being an empty list), we need to create all of
                # our 'plinko slots' for each channel in both the work and
                # yield lists
                work_list_len = len(work_list)
                channels_len = len(channels)
                if work_list_len == 0:
                    work_list = [[] for x in channels]
                    yield_list = [[] for x in channels]

                if channels_len > work_list_len and current_line > 0:
                    warn_msg = 'Unexpected channel count in line {}. Expected {}, got {}'.format(
                        current_line, work_list_len, channels_len)
                    if warnings:
                        warnings.append((line, warn_msg))
                    Logger.warn("DataStore: {}".format(warn_msg))
                    continue

                # Down to business, first, we stuff each channel's sample
                # into the work list
                Logger.debug('DataStore: work_list.len={}, channels.len={}, current_line={}'.format(
                    work_list_len, channels_len, current_line))
                for c in range(channels_len):
                    work_list[c].append(channels[c])

                # At this point, we need to walk through each channel
                # column in the work list.  If the length of the column is
                # 1, we simply move onto the next column.  If the length
                # is > 1, we check if column[-1] is a miss (None) or a
                # hit(anything else).  If it is a hit, we
                # interpolate/extrapolate the column, then move everything
                # EXCEPT the last item into the yield list

                for c in range(len(work_list)):
                    if len(work_list[c]) == 1:
                        continue

                    # If we have a hit at the end of the list, get the
                    # extraploated/interpolated list of datapoints
                    if not work_list[c][-1] == None:
                        mod_list = self._extrap_datapoints(work_list[c])

                        # Now copy everything but the last point in the
                        # modified list into the yield_list
                        yield_list[c].extend(mod_list[:-1])

                        # And remove everything BUT the last datapoint from
                        # the current list in work_list
                        work_list[c] = work_list[c][-1:]

                # Ok, we now have THINGS in our yield list, if we have
                # something in EVERY column of the yield list, create a
                # new list containing the first item in every column,
                # shift all columns down one, and yield the new list
                if not 0 in [len(x) for x in yield_list]:
                    ds_to_yield = [x[0] for x in yield_list]
                    map(lambda x: x.pop(0), yield_list)
                    if progress_cb:
                        percent_complete = float(current_line) / line_count * 100
                        progress_cb(percent_complete)
                    yield ds_to_yield

                # Increment line number
            except Exception as e:
                Logger.warn('Datastore: could not parse logfile data at line {}'.format(current_line))

            current_line += 1

        # now, finish off and extrapolate the remaining items in the
        # work list and extend the yield list with the resultant values
        for idx in range(len(work_list)):
            set_len = len(work_list[idx])
            work_list[idx] = [work_list[idx][0] for x in range(set_len)]
            yield_list[idx].extend(work_list[idx])

        # Yield off the remaining items in the yield list
        while not 0 in [len(x) for x in yield_list]:
            current_line += 1
            ds_to_yield = [x[0] for x in yield_list]
            map(lambda x: x.pop(0), yield_list)
            if progress_cb:
                percent_complete = float(current_line) / line_count * 100
                progress_cb(percent_complete)
            yield ds_to_yield

    def delete_session(self, session_id):
        self._conn.execute(
            """DELETE FROM datapoint WHERE sample_id in (select id from sample where session_id = ?)""", (session_id,))
        self._conn.execute(
            """DELETE FROM sample WHERE session_id=?""", (session_id,))
        self._conn.execute("""DELETE FROM session where id=?""", (session_id,))
        self._conn.execute(
            """DELETE FROM channel where session_id=?""", (session_id,))
        self._conn.commit()

    def init_session(self, name, channel_metas=None, notes=''):
        session_id = self.create_session(name, notes)

        if channel_metas:
            session_channels = []
            new_channels = []
            for name, meta in channel_metas.iteritems():
                channel = DatalogChannel(
                    name, meta.units, meta.min, meta.max, meta.sampleRate, 0)
                if channel.name not in [x.name for x in self._channels]:
                    new_channels.append(channel)
                session_channels.append(channel)
            self._extend_datalog_channels(new_channels)

            self._add_session_channels(session_id, session_channels)
            self._populate_channel_list()

        return session_id

    def create_session(self, name, notes=''):
        """
        Creates a new session entry in the sessions table and returns it's ID
        """

        current_time = unix_time(datetime.datetime.now())
        self._conn.execute("""INSERT INTO session
        (name, notes, date)
        VALUES (?, ?, ?)""", (name, notes, current_time))

        self._conn.commit()
        session_id = self._get_last_table_id('session')

        Logger.info(
            'DataStore: Created session with ID: {}'.format(session_id))
        return session_id

    # class member variable to track ending datalog id when importing
    def _handle_data(self, data_file, headers, session_id, warnings=None, progress_cb=None):
        """
        takes a raw dataset in the form of a CSV file and inserts the data
        into the sqlite database.

        This function is not thread-safe.
        """

        starting_datalog_id = self._get_last_table_id('sample') + 1
        self._ending_datalog_id = starting_datalog_id

        def sample_iter(count, sample_id):
            for x in range(count):
                yield [sample_id]

        def datapoint_iter(data, datalog_id):
            for record in data:
                record = [datalog_id] + record
                datalog_id += 1
                yield record
            self._ending_datalog_id = datalog_id

        # Create the generator for the desparsified data
        newdata_gen = self._desparsified_data_generator(
            data_file, warnings=warnings, progress_cb=progress_cb)

        # Put together an insert statement containing the column names
        datapoint_sql = "INSERT INTO datapoint ({}) VALUES ({});".format(','.join(['sample_id'] + [_scrub_sql_value(x.name) for x in headers]),
                                                                         ','.join(['?'] * (len(headers) + 1)))

        # Relatively static insert statement for sample table
        sample_sql = "INSERT INTO sample (session_id) VALUES (?)"

        # Use a generator to efficiently insert data into table, within a
        # transaction
        cur = self._conn.cursor()
        try:
            cur.executemany(
                datapoint_sql, datapoint_iter(newdata_gen, starting_datalog_id))
            cur.executemany(sample_sql, sample_iter(
                self._ending_datalog_id - starting_datalog_id, session_id))
            self._conn.commit()
        except:  # rollback under any exception, then re-raise exception
            self._conn.rollback()
            raise

    def get_location_center(self, sessions=None):

        if not (self.channel_exists('Latitude') and self.channel_exists('Longitude')):
            return (0, 0)

        c = self._conn.cursor()

        base_sql = 'SELECT AVG(Latitude), AVG(Longitude) from datapoint'
        params = ','.join(['?'] * (len(sessions)))

        if type(sessions) == list and len(sessions) > 0:
            base_sql += """ JOIN sample ON datapoint.sample_id=sample.id WHERE sample.session_id IN({}) AND
            datapoint.Latitude != 0 AND datapoint.Longitude != 0""".format(params)

        c.execute(base_sql, sessions)
        res = c.fetchone()

        lat_average = None
        lon_average = None
        if res:
            lat_average = res[0]
            lon_average = res[1]
        return (lat_average, lon_average)

    def _session_select_clause(self, sessions=None):
        sql = ''
        if type(sessions) == list and len(sessions) > 0:
            subs = ','.join(['?'] * len(sessions))

            sql += ' JOIN sample ON datapoint.sample_id=sample.id WHERE sample.session_id IN({})'.format(
                subs)
        return sql

    def get_channel_average(self, channel, sessions=None):
        c = self._conn.cursor()
        params = []

        if sessions is not None:
            params = params + sessions

        base_sql = "SELECT AVG({}) from datapoint ".format(
            _scrub_sql_value(channel)) + self._session_select_clause(sessions)
        c.execute(base_sql, params)
        res = c.fetchone()
        average = None if res == None else res[0]
        return average

    def _extra_channels(self, extra_channels=None):
        sql = ''
        if type(extra_channels) == list:
            for channel in extra_channels:
                sql += ',{}'.format(_scrub_sql_value(channel))
        return sql

    def _get_channel_aggregate(self, aggregate, channel, sessions=None, extra_channels=None, exclude_zero=True):
        c = self._conn.cursor()
        params = []

        if sessions is not None:
            params = params + sessions

        if not self.channel_exists(channel):
            raise InvalidChannelException()

        base_sql = "SELECT {}({}) {} from datapoint {} {};".format(aggregate, _scrub_sql_value(channel),
                                                                   self._extra_channels(
                                                                       extra_channels),
                                                                   self._session_select_clause(
                                                                       sessions),
                                                                   '{} {} > 0'.format('AND' if sessions else 'WHERE',
                                                                                      _scrub_sql_value(channel))
                                                                   if exclude_zero else '')

        c.execute(base_sql, params)
        res = c.fetchone()
        return None if res == None else res if extra_channels else res[0]

    def get_channel_max(self, channel, sessions=None, extra_channels=None):
        return self._get_channel_aggregate('MAX', channel, sessions=sessions, extra_channels=extra_channels)

    def get_channel_min(self, channel, sessions=None, extra_channels=None, exclude_zero=True):
        return self._get_channel_aggregate('MIN', channel, sessions=sessions, extra_channels=extra_channels)

    def set_channel_smoothing(self, channel, smoothing):
        """
        Sets the smoothing rate on a per channel basis, this will be reflected in the returned dataset

        The 'smoothing' rate details how many samples we should skip and smooth out in the middle of a dataset, i.e:
        [1, 1, 1, 1, 5] with a smoothing rate of '4', would mean we evaluate this list as:
         0* 1  2  3  4*
        [1, x, x, x, 5], which would then be interpolated as:
        [1, 2, 3, 4, 5]
        """
        if smoothing < 1:
            smoothing = 1

        if not channel in [x.name for x in self._channels]:
            raise DatastoreException("Unknown channel: {}".format(channel))

        params = [smoothing, channel]

        self._conn.execute(
            'UPDATE channel SET smoothing = ? WHERE name = ?', params)

    def get_channel_smoothing(self, channel):
        if not channel in [x.name for x in self._channels]:
            raise DatastoreException("Unknown channel: {}".format(channel))

        c = self._conn.cursor()

        base_sql = "SELECT smoothing from channel WHERE channel.name=?;"
        c.execute(base_sql, [channel])

        res = c.fetchone()

        if res == None:
            raise DatastoreException(
                "Unable to retrieve smoothing for channel: {}".format(channel))
        else:
            return res[0]

    @timing
    def import_datalog(self, path, name, notes='', progress_cb=None):
        warnings = []
        if not self._isopen:
            raise DatastoreException("Datastore is not open")
        try:
            dl = open(path, 'rb')
        except:
            raise DatastoreException("Unable to open file")

        header = dl.readline()
        channels = self._parse_datalog_headers(header)
        self._extend_datalog_channels(channels)

        # Create an event to be tagged to these records
        session_id = self.create_session(name, notes)
        self._add_session_channels(session_id, channels)
        self._handle_data(dl, channels, session_id, warnings, progress_cb)

        self._populate_channel_list()
        return session_id

    def query(self, sessions=[], channels=[], data_filter=None, distinct_records=False):
        # Build our select statement
        sel_st = 'SELECT '

        if distinct_records:
            sel_st += 'DISTINCT '

        columns = []
        joins = []
        params = []

        # make sure that the sessions list exists
        if type(sessions) != list or len(sessions) == 0:
            raise DatastoreException(
                "Must provide a list of sessions to query!")

        # If there are no channels, or if a '*' is passed, select all
        # of the channels
        if len(channels) == 0 or '*' in channels:
            channels = [_scrub_sql_value(x.name) for x in self._channels]

        for ch in channels:
            chanst = str(_scrub_sql_value(ch))
            tbl_prefix = 'datapoint.'
            alias = ' as {}'.format(chanst)
            columns.append(tbl_prefix + chanst + alias)
            joins.append(tbl_prefix + chanst)

        # Make the session ID the first column
        ses_sel = "sample.session_id as session_id"
        columns.insert(0, ses_sel)

        # Add the columns to the select statement
        sel_st += ','.join(columns)

        # Point out where we're pulling this from
        sel_st += '\nFROM sample\n'

        # Add our joins
        sel_st += 'JOIN datapoint ON datapoint.sample_id=sample.id\n'

        if data_filter is not None:
            # Add our filter
            sel_st += 'WHERE '
            if not 'Filter' in type(data_filter).__name__:
                raise TypeError("data_filter must be of class Filter")

            sel_st += str(data_filter)
            params = params + data_filter.params

        # create the session filter
        if data_filter == None:
            ses_st = "WHERE "
        else:
            ses_st = "AND "

        ses_filters = []
        for s in sessions:
            ses_filters.append('sample.session_id = ?')
            params.append(s)

        ses_st += 'OR '.join(ses_filters)

        # Now add the session filter to the select statement
        sel_st += ses_st

        Logger.debug('[datastore] Query execute: {}'.format(sel_st))
        c = self._conn.cursor()
        c.execute(sel_st, params)

        smoothing_map = {}
        # Put together the smoothing map
        for ch in channels:
            sr = self.get_channel_smoothing(ch)
            smoothing_map[ch] = sr

        # add the session_id to the smoothing map with a smoothing rate
        # of 0
        smoothing_map['session_id'] = 0

        return DataSet(c, smoothing_map)

    def get_session_by_id(self, session_id, sessions=None):
        sessions = self.get_sessions() if not sessions else sessions
        session = next(
            (x for x in sessions if x.session_id == session_id), None)
        return session

    def get_sessions(self):
        sessions = []
        for row in self._conn.execute('SELECT id, name, notes, date FROM session ORDER BY date DESC;'):
            sessions.append(
                Session(session_id=row[0], name=row[1], notes=row[2], date=row[3]))

        return sessions

    def session_has_laps(self, session_id):
        '''
        Indicates if the specified session includes any lap data. 
        :param session_id the session id
        :type session_id int
        :returns True if the session has lap information
        :type Boolean
        '''
        if not (self.channel_exists('CurrentLap') and self.channel_exists('LapCount')):
            return False

        c = self._conn.cursor()
        for row in c.execute('''SELECT s.session_id, d.LapCount, d.CurrentLap FROM sample s, 
                             datapoint d WHERE s.session_id = ? AND d.sample_id = s.id ORDER BY d.LapCount DESC LIMIT 1;''',
                             (session_id,)):
            return row[1] is not None and row[2] is not None
        return False

    def get_laps(self, session_id):
        '''
        Fetches a list of lap information for the specified session id
        :param session_id the session id
        :type session_id int
        :returns list of Lap objects
        :type list 
        '''

        # if there is no lap information then just return a default single lap.
        if not self.session_has_laps(session_id):
            laps_dict = OrderedDict()
            laps_dict[1] = Lap(session_id=session_id, lap=1, lap_time=None)
            return laps_dict

        laps = []
        c = self._conn.cursor()
        for row in c.execute('''SELECT DISTINCT sample.session_id AS session_id, 
                                datapoint.CurrentLap AS CurrentLap,
                                LapTime
                                FROM sample
                                JOIN datapoint ON datapoint.sample_id=sample.id
                                AND sample.session_id = ?
                                GROUP BY LapCount, session_id
                                ORDER BY datapoint.LapCount ASC;''',
                             (session_id,)):
            lap = row[1]
            lap = 1 if lap is None else lap
            laps.append(Lap(session_id=row[0], lap=lap - 1, lap_time=row[2]))

        # Figure out if there are samples beyond the last lap
        extra_lap_query = '''SELECT COUNT(*) FROM sample JOIN datapoint ON datapoint.sample_id=sample.id
                             AND sample.session_id = ? WHERE datapoint.CurrentLap > ? LIMIT 1'''

        # If there are samples beyond the last actual timed lap (crossed start/finish), add that lap to the end
        # so users can view that data if needed
        if len(laps) > 0:
            c = self._conn.cursor()

            for row in c.execute(extra_lap_query, [session_id, laps[-1].lap]):
                laps.append(
                    Lap(session_id=session_id, lap=(laps[-1].lap + 1), lap_time=None))
                break

        # Filter so we only include valid laps
        laps = [lap for lap in laps if lap.lap >= 0]

        # Transform into an ordered dict so lap IDs are preserved as keys.
        laps_dict = OrderedDict()
        for lap in laps:
            laps_dict[lap.lap] = lap

        return laps_dict

    def update_session(self, session):
        self._conn.execute("""UPDATE session SET name=?, notes=?, date=? WHERE id=?;""", (
            session.name, session.notes, unix_time(datetime.datetime.now()), session.session_id,))
        self._conn.commit()

    def _get_session_record_count(self, session_id):
        c = self._conn.cursor()
        c.execute(
            'SELECT count(session_id) from sample where session_id =?', (session_id,))
        res = c.fetchone()
        return None if res is None else res[0]

    @timing
    def export_session(self, session_id, export_file, progress_callback=None):
        """
        Exports the specified session to a CSV file
        :param session_id the session to export
        :type session_id int
        :param export_file_name the file name to export
        :type export_file_name string
        :param progress_callback callback function for progress. Return true from this function to cancel export
        :type progress_callback function
        :return the number of rows exported
        """

        def _do_progress_cb(progress):
            if progress_callback is not None:
                return progress_callback(progress)
            return False

        # channel_list
        channels = self.get_channel_list(session_id)

        header = ''
        for channel in channels:
            header += '"{}"|"{}"|{}|{}|{},'.format(channel.name,
                                                   channel.units,
                                                   channel.min,
                                                   channel.max,
                                                   channel.sample_rate)
        export_file.write(header[:-1] + '\n')

        channel_names = []
        channel_intervals = []
        system_channel_indexes = []

        for c in channels:
            name = c.name
            channel_names.append(name)
            interval = DataStore.MAX_SAMPLE_RATE / c.sample_rate
            channel_intervals.append(interval)
            system_channel_indexes.append(
                True if name in DataStore.SYSTEM_CHANNELS else False)

        export_count = self._get_session_record_count(session_id)

        dataset = self.query([session_id], channel_names)
        # dataset = self.query(sessions=[session_id], channels=channel_names)
        records = dataset.fetch_records()
        sync_point = None

        try:
            datalog_interval_index = channel_names.index('Interval')
        except ValueError:
            raise DatastoreException(
                'DataStore: Cannot export: Interval channel missing from data')

        # check if there are no samples to output!
        if set(channel_names).issubset(DataStore.SYSTEM_CHANNELS):
            raise DatastoreException(
                'DataStore: Cannot export: No channels to output')

        row_index = 0
        channel_count = len(channels)

        for record in records:
            # Note 1 + offset; record contains session_id as first column,
            # the rest are individual channels
            sampled = False
            while not sampled:
                if sync_point is None:
                    # the first interval is our synchronization point
                    # for determining when to output samples
                    # The first sample outputs all values by default
                    interval_record = record[1 + datalog_interval_index]
                    if interval_record is None:
                        Logger.warning('DataStore: Export: invalid row detected, skipping: {}'.format(record))
                        break
                    sync_point = long(interval_record)

                row = ''
                current_interval = long(record[1 + datalog_interval_index])

                for index in range(channel_count):
                    # first column is session id, so skip it
                    if system_channel_indexes[index] == True:
                        # our system channels are in long integer format
                        value = long(record[1 + index])
                    else:
                        channel_interval = channel_intervals[index]
                        if (current_interval - sync_point) % channel_interval == 0:
                            value = record[1 + index]
                            if value is None:
                                value = ''
                            sampled = True
                        else:
                            value = ''
                    row += str(value) + ','
                if sampled:
                    export_file.write(row[:-1] + '\n')
                if not sampled:
                    # The data log may have inconsistent data; if so
                    # the interval will change. If we detect this then we need
                    # to re-synchronize
                    Logger.warning(
                        'DataStore: Export: Inconsistent interval detected at interval {}; re-syncing'.format(current_interval))
                    sync_point = None
            row_index += 1
            progress = row_index * 100 / export_count
            if progress % 5 == 0:
                cancel = _do_progress_cb(progress)
                if cancel == True:
                    break
        _do_progress_cb(100)
        return row_index
