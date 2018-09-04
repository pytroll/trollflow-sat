#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Helper utils for unit tests."""

import datetime as dt
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

PRODUCT_LIST = {
    "product_list": {
        "area1":
        {
            "areaname": "areaname1",
            "products":
            {
                "overview":
                {
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                }
            }
        }
    }
}

FILE1 = "/path/to/data1.file"
FILE2 = "/path/to/data2.file"
METADATA_FILE = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
                 "end_time": dt.datetime(2018, 8, 31, 12, 15),
                 "sensor": "sensor1",
                 "uri": FILE1
                }
METADATA_DATASET = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
                    "end_time": dt.datetime(2018, 8, 31, 12, 15),
                    "sensor": "sensor1",
                    "dataset": [{"uri": FILE1},
                                {"uri": FILE2}]
                   }
METADATA_COLLECTION = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
                       "end_time": dt.datetime(2018, 8, 31, 12, 15),
                       "sensor": "sensor1",
                       "collection": [{"uri": FILE1},
                                      {"uri": FILE2}]
                      }
METADATA_COLLECTION_DATASET = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
                               "end_time": dt.datetime(2018, 8, 31, 12, 15),
                               "sensor": "sensor1",
                               "collection": [{"dataset": [{"uri": FILE1},
                                                           {"uri": FILE2}]}]
                              }


def write_yaml(data):
    import yaml
    import tempfile

    fname = tempfile.mktemp(suffix='.yaml')
    with open(fname, 'w') as fid:
        yaml.dump(data, fid)

    return fname


class MockScene(object):

    def __init__(self, filenames=None, reader=None, datasets=None, attrs=None):
        self.filenames = filenames or []
        self.reader = reader or []
        self.datasets = datasets or {}
        self.attrs = attrs or {}

    def load(self, names):
        for name in names:
            dset = Mock(name=name)
            self.datasets[dset] = None

    def unload(self, names):
        datasets = self.datasets.copy()
        for name in names:
            for dset in datasets:
                if dset.name == name:
                    self.datasets.pop(dset, None)

    def resample(self, area_id, **kwargs):
        return MockScene()
