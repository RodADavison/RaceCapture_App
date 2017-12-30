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

import uuid
from datetime import datetime
import json
import time
import copy
import errno
import string
from threading import Thread, Lock
import urllib2
import os
import os.path
import traceback
from StringIO import StringIO
import gzip
import zipfile
from autosportlabs.util.timeutil import time_to_epoch, epoch_to_time
from kivy.logger import Logger
from collections import OrderedDict


class Preset(object):
    """Object to represent a preset item
    """
    def __init__(self):
        self.mapping_id = None
        self.uri = None
        self.name = ''
        self.notes = ''
        self.created = None
        self.updated = None
        self.more_info_url = None
        self.image_url = None
        self.local_image_path = None
        self.mapping = None
        self.mapping_type_id = None
        self.mapping_type = None

    def from_dict(self, preset_dict):
        self.mapping_id = int(preset_dict.get('id'))
        self.uri = preset_dict.get('URI')
        self.name = preset_dict.get('name', self.name)
        self.created = preset_dict.get('created')
        self.updated = preset_dict.get('updated')
        self.notes = preset_dict.get('notes')
        self.more_info_url = preset_dict.get('more_info_url')
        self.image_url = preset_dict.get('image_url')
        self.mapping = preset_dict.get('mapping')
        self.mapping_type_id = preset_dict.get('mapping_type_id')
        self.mapping_type = preset_dict.get('mapping_type')


    def to_dict(self):
        return {'id': self.mapping_id,
                'URI': self.uri,
                'name': self.name,
                'notes': self.notes,
                'created': self.created,
                'updated': self.updated,
                'more_info_url': self.more_info_url,
                'image_url': self.image_url,
                'mapping': self.mapping,
                'mapping_type_id': self.mapping_type_id,
                'mapping_type': self.mapping_type}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.mapping_id == other.mapping_id
        return False

class PresetManager(object):
    """Manages fetching and updating Presets 
    """
    PRESET_URL = 'https://podium.live/api/v1/mappings'
    READ_RETRIES = 3
    RETRY_DELAY = 1.0
    PRESET_DOWNLOAD_TIMEOUT = 30

    def __init__(self, **kwargs):
        self.on_progress = lambda self, value: value
        self.presets_user_dir = '.'
        self.presets_user_subdir = '/presets'
        self.set_presets_user_dir(kwargs.get('user_dir', self.presets_user_dir) + self.presets_user_subdir)
        self.base_dir = kwargs.get('base_dir')

        self.update_lock = Lock()
        self.presets = OrderedDict()

    def get_preset_by_id(self, id):
        return self.presets.get(id)

    def get_presets_by_type(self, type):
        return OrderedDict ((k, v) for k, v in self.presets.items() if v.mapping_type == type).items()

    def set_presets_user_dir(self, path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        self.presets_user_dir = path

    def init(self, progress_cb, success_cb, fail_cb):
        self._check_load_default_presets()
        self._load_presets(progress_cb, success_cb, fail_cb)

    def load_json(self, uri):
        """Semi-generic method for fetching JSON data
        """
        retries = 0
        while retries < self.READ_RETRIES:
            try:
                opener = urllib2.build_opener()
                opener.addheaders = [('Accept', 'application/json'), ('Accept-encoding', 'gzip')]
                response = opener.open(uri, timeout=PresetManager.PRESET_DOWNLOAD_TIMEOUT)
                data = response.read()
                if response.info().get('Content-Encoding') == 'gzip':
                    string_buffer = StringIO(data)
                    data = gzip.GzipFile(fileobj=string_buffer).read()
                j = json.loads(data)
                return j
            except Exception as detail:
                Logger.warning('PresetManager: Failed to read: from {} : {}'.format(uri, traceback.format_exc()))
                if retries < self.READ_RETRIES:
                    Logger.warning('PresetManager: retrying in ' + str(self.RETRY_DELAY) + ' seconds...')
                    retries += 1
                    time.sleep(self.RETRY_DELAY)
        raise Exception('Error reading json doc from: ' + uri)

    def download_all_presets(self):
        """Downloads all presets, then turns them into Preset objects
        """
        presets = {}
        preset_json = self.fetch_preset_list(True)

        for p in preset_json:
                preset = Preset()
                preset.from_dict(p)
                presets[preset.mapping_id] = preset

        return presets

    def fetch_preset_list(self, full_response=False):
        """Fetches all presets from RCL's API and returns them as an array of dicts. RCL's API normally returns minimal
        object information when listing multiple objects. The 'full_response' arg tells this function to expand
        all objects to contain all their data. This allows us to quickly get basic information about presets or pull
        down everything if we have no presets locally.
        """

        total_mappings = None
        next_uri = self.PRESET_URL + "?start=0&per_page=100"

        if full_response:
            next_uri += '&expand=1'

        mappings_list = []

        while next_uri:
            Logger.info('PresetManager: Fetching preset data: {}'.format(next_uri))
            response = self.load_json(next_uri)
            try:
                if total_mappings is None:
                    total_mappings = int(response.get('total', None))
                    if total_mappings is None:
                        raise MissingKeyException('Mapping list JSON: could not get total preset count')

                mappings = response.get('mappings', None)

                if mappings is None:
                    raise MissingKeyException('Mapping list JSON: could not get preset list')

                mappings_list += mappings
                next_uri = response.get('nextURI')

            except MissingKeyException as detail:
                Logger.error('PresetManager: Malformed venue JSON from url ' + next_uri + '; json =  ' + str(response) +
                             ' ' + str(detail))

        Logger.info('PresetManager: fetched list of ' + str(len(mappings_list)) + ' presets')

        if not total_mappings == len(mappings_list):
            Logger.warning('PresetManager: mappings list count does not reflect downloaded size ' + str(total_mappings) + '/' + str(len(mappings_list)))

        return mappings_list

    def download_preset(self, mapping_id):
        preset_url = '{}/{}'.format(self.PRESET_URL, mapping_id)
        response = self.load_json(preset_url)
        preset = Preset()
        try:
            preset_json = response.get('mapping')
            preset.from_dict(preset_json)
            return copy.deepcopy(preset)
        except Warning:
            return None

    def add_preset(self, preset):
        """ Add the specified preset
        :param preset the preset to add
        :type preset Preset
        """
        self._save_preset(preset)
        self.presets[preset.mapping_id] = preset

    def _save_preset(self, preset):
        path = os.path.join(self.presets_user_dir, str(preset.mapping_id) + '.json')
        preset_json_string = json.dumps(preset.to_dict(), sort_keys=True, indent=2, separators=(',', ': '))
        with open(path, 'w') as text_file:
            text_file.write(preset_json_string)

    def _download_preset_image(self, preset):
        image_url = preset.image_url
        if image_url:
            extension = None
            extension = '.jpg' if '.jpg' in image_url else extension
            extension = '.png' if '.png' in image_url else extension

            request = urllib2.Request(image_url, headers={'User-Agent': 'ASL mapping builder'})
            response = urllib2.urlopen(request, timeout=PresetManager.PRESET_DOWNLOAD_TIMEOUT)
            data = response.read()

            image_file = '{}{}'.format(preset.mapping_id, extension)
            path = os.path.join(self.presets_user_dir, image_file)
            open(path, 'wb').write(data)

    def _load_current_mappings_worker(self, success_cb, fail_cb, progress_cb=None):
        """Method for loading local preset files in a separate thread
        """
        try:
            self.update_lock.acquire()
            self._load_presets(progress_cb)
            success_cb()
        except Exception as detail:
            Logger.exception('')
            fail_cb(detail)
        finally:
            self.update_lock.release()

    def _check_load_default_presets(self):
        preset_file_names = os.listdir(self.presets_user_dir)
        if (len(preset_file_names) == 0):
            Logger.info("PresetManager: No presets found; loading defaults")
            try:
                with zipfile.ZipFile(os.path.join(self.base_dir, 'defaults', 'default_mappings.zip'), 'r') as z:
                    z.extractall(self.presets_user_dir)
            except Exception as e:
                Logger.error("PresetManager: Could not load default presets: {}".format(e))

    def _load_presets(self, progress_cb=None, success_cb=None, fail_cb=None):
        """Loads presets from local files. If called with success and fail callbacks it sets up a separate thread
        """
        if success_cb and fail_cb:
            t = Thread(target=self._load_current_mappings_worker, args=(success_cb, fail_cb, progress_cb))
            t.daemon = True
            t.start()
        else:
            preset_file_names = [f for f in os.listdir(self.presets_user_dir) if f.endswith('.json')]
            self.presets.clear()
            preset_count = len(preset_file_names)
            count = 0

            for preset_path in preset_file_names:
                try:
                    json_data = open(os.path.join(self.presets_user_dir, preset_path))
                    preset_dict = json.load(json_data)

                    if preset_dict is not None:
                        preset = Preset()
                        preset.from_dict(preset_dict)
                        self._set_preset_local_path(preset)

                        self.presets[preset.mapping_id] = preset
                        count += 1
                        if progress_cb:
                            progress_cb(count=preset.count, total=preset_count, message=preset.name)
                except Exception as detail:
                    Logger.warning('PresetManager: failed to read preset file ' + preset_path + ';\n' + str(detail))
                    raise


    def _set_preset_local_path(self, preset):
        local_path = self._image_url_to_local_path(preset.mapping_id, preset.image_url)
        if local_path:
            preset.local_image_path = os.path.join(self.presets_user_dir, local_path)

    def _image_url_to_local_path(self, mapping_id, image_url):
        if image_url is None:
            return None

        extension = None
        extension = '.jpg' if '.jpg' in image_url else extension
        extension = '.png' if '.png' in image_url else extension
        if not extension:
            return None

        return '{}{}'.format(mapping_id, extension)


    def update_all_presets_worker(self, success_cb, fail_cb, progress_cb=None):
        """Method for updating all presets in a separate thread
        """
        try:
            self.update_lock.acquire()
            self.refresh(progress_cb)
            success_cb()
        except Exception as detail:
            Logger.exception('')
            fail_cb(detail)
        finally:
            self.update_lock.release()

    def refresh(self, progress_cb=None, success_cb=None, fail_cb=None):
        """Refreshes all presets. If success and fail callbacks are provided, sets up a new thread.
        If no presets are saved locally, it will fetch all preset data and save it.
        If there are presets saved locally, it will fetch a minimal amount of data and only download
        all data for a preset if the preset has been updated
        """
        if progress_cb:
            progress_cb(message="Fetching list of Presets...")
        if success_cb and fail_cb:
            t = Thread(target=self.update_all_presets_worker, args=(success_cb, fail_cb, progress_cb))
            t.daemon = True
            t.start()
        else:
            if len(self.presets) == 0:
                Logger.info("PresetManager: No presets found locally, fetching all presets")
                preset_list = self.download_all_presets()
                count = 0
                total = len(preset_list)

                for mapping_id, preset in preset_list.iteritems():
                    count += 1
                    if progress_cb:
                        progress_cb(count=count, total=total, message=preset.name)
                    self._save_preset(preset)
                    self._download_preset_image(preset)
                    self._set_preset_local_path(preset)
                    self.presets[mapping_id] = preset
            else:
                Logger.info("PresetManager: refreshing presets")
                venues = self.fetch_preset_list(full_response=False)

                preset_count = len(venues)
                count = 0

                for venue in venues:
                    update = False
                    count += 1
                    preset_id = venue.get('id')

                    if self.presets.get(preset_id) is None:
                        Logger.info('PresetManager: new preset detected: {}'.format(preset_id))
                        update = True
                    elif not self.presets[preset_id].updated == venue['updated']:
                        Logger.info('PresetManager: existing preset changed: {}'.format(preset_id))
                        update = True

                    if update:
                        updated_preset = self.download_preset(preset_id)
                        if updated_preset is not None:
                            self._save_preset(updated_preset)
                            self._download_preset_image(updated_preset)
                            self._set_preset_local_path(updated_preset)
                            self.presets[preset_id] = updated_preset
                            if progress_cb:
                                progress_cb(count=count, total=preset_count, message=updated_preset.name)
                    else:
                        progress_cb(count=count, total=preset_count)


class MissingKeyException(Exception):
    """Exception for if a key is missing from a dict
    """
    pass
