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
from collections import OrderedDict
from copy import deepcopy
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

PRODUCT_LIST = OrderedDict({
    "common": {},
    "product_list": OrderedDict({
        "area1":
        OrderedDict({
            "areaname": "areaname1",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        })
    })
})

PRODUCT_LIST_SATPROJ = OrderedDict({
    "common": {},
    "product_list": OrderedDict({
        "satproj":
        OrderedDict({
            "areaname": "satproj",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        })
    })
})

PRODUCT_LIST_TWO_AREAS = OrderedDict({
    "common": {},
    "product_list": OrderedDict({
        "area1":
        OrderedDict({
            "areaname": "areaname1",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        }),
        "area2":
        OrderedDict({
            "areaname": "areaname2",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        })
    })
})


PRODUCT_LIST_TWO_AREAS_TOGETHER = OrderedDict({
    "common": {"process_by_area": False},
    "product_list": OrderedDict({
        "area1":
        OrderedDict({
            "areaname": "areaname1",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        }),
        "area2":
        OrderedDict({
            "areaname": "areaname2",
            "products":
            OrderedDict({
                "overview":
                OrderedDict({
                    "productname": "overview",
                    "fname_pattern": "pattern",
                    "formats": [{"format": "tif", "writer": None}]
                })
            })
        })
    })
})

FILE1 = "/path/to/data1.file"
FILE2 = "/path/to/data2.file"
METADATA_FILE = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
                 "end_time": dt.datetime(2018, 8, 31, 12, 15),
                 "sensor": "sensor1",
                 "uri": FILE1,
                 "platform_name": "platform1"
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


class MockDset(object):

    def __init__(self, name, attrs=None):
        self.name = name
        self.attrs = attrs or {}

class MockScene(OrderedDict):

    def __init__(self, filenames=None, reader=None, datasets=None, attrs=None):
        self.filenames = filenames or []
        self.reader = reader or []
        self.datasets = datasets or OrderedDict({})
        self.attrs = attrs or {}

    def load(self, names):
        for name in names:
            dset = MockDset(name, attrs=self.attrs)
            self.datasets[dset] = dset

    def unload(self, names):
        datasets = self.datasets.copy()
        for name in names:
            for dset in datasets:
                if dset.name == name:
                    self.datasets.pop(dset, None)

    def resample(self, area_id, **kwargs):
        return deepcopy(self)

    def keys(self):
        return self.datasets.keys()
        # keys = sorted(self.datasets.keys())
        # return (k.name for k in keys)

    def __iter__(self):
        for x in self.datasets.values():
            yield x

    def __getitem__(self, idx):
        for itm in self.datasets:
            if itm.name == idx:
                return itm
        raise IndexError

    def save_datasets(self, datasets=None, **kwargs):
        return MockDset(datasets[0], self.attrs)
