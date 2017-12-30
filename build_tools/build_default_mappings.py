#!/usr/bin/python
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

from autosportlabs.racecapture.presets.presetmanager import PresetManager
import json
import zipfile
import StringIO
import os
import urllib2
from autosportlabs.racecapture.presets.presetmanager import PresetManager

headers = {'User-Agent': 'ASL mapping builder'}

tm = PresetManager()

presets = tm.download_all_presets()

mf = StringIO.StringIO()
with zipfile.ZipFile(mf, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
    for preset_id, preset in presets.iteritems():
        preset_json_string = json.dumps(preset.to_dict(), sort_keys=True, indent=2, separators=(',', ': '))
        zf.writestr('{}.json'.format(preset_id), preset_json_string)
        image_url = preset.image_url
        if image_url:

            extension = None
            extension = '.jpg' if '.jpg' in image_url else extension
            extension = '.png' if '.png' in image_url else extension

            request = urllib2.Request(image_url, headers={'User-Agent': 'ASL mapping builder'})
            response = urllib2.urlopen(request, timeout=PresetManager.PRESET_DOWNLOAD_TIMEOUT)
            data = response.read()

            image_file = '{}{}'.format(preset.mapping_id, extension)
            open(image_file, 'wb').write(data)
            zf.write(image_file)
            os.remove(image_file)



archive_path = os.path.join('defaults', 'default_mappings.zip')

with open(archive_path, 'wb') as f:
    f.write(mf.getvalue())

