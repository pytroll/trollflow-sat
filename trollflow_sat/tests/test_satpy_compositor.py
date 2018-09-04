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

"""Unit tests for SatPy compositor plugin"""

import unittest
try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call
import datetime as dt

from trollflow_sat.satpy_compositor import SceneLoader

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


class TestSceneLoader(unittest.TestCase):

    def setUp(self):
        from threading import Lock
        import six.moves.queue as queue
        from posttroll.message import Message

        self.loader = SceneLoader()
        self.prodlist = write_yaml(PRODUCT_LIST)
        self.lock = Lock()
        self.prev_lock = Lock()
        self.output_queue = queue.Queue()
        self.context = {'lock': self.lock, 'prev_lock': self.prev_lock,
                        'output_queue': self.output_queue}
        self.topic = '/topic'
        self.file_msg = Message(self.topic, 'file', METADATA_FILE)
        self.dataset_msg = Message(self.topic, 'dataset', METADATA_DATASET)
        self.collection_msg = Message(self.topic, 'collection',
                                      METADATA_COLLECTION)
        self.collection_dataset_msg = Message(self.topic, 'collection',
                                              METADATA_COLLECTION_DATASET)
        self.dset1 = Mock(name='dset1')
        self.dset2 = Mock(name='dset2')
        self.scene = Mock(attrs=METADATA_FILE, datasets=[self.dset1, self.dset2])

    def tearDown(self):
        import os
        os.remove(self.prodlist)

    def test_init(self):
        self.assertFalse(self.loader.use_lock)
        self.assertFalse(self.loader.slots)

    def test_pre_invoke(self):
        self.assertIsNone(self.loader.pre_invoke())

    def test_invoke_no_instrument(self):
        self.assertIsNone(self.loader.invoke(self.context))
        self.assertFalse(self.context['prev_lock'].locked())

    @patch('trollflow_sat.satpy_compositor.SceneLoader.create_scene_from_message')
    def test_invoke_scene_is_none(self, scene_from_msg):
        context = self.context
        context['instruments'] = ['spam']
        context['product_list'] = self.prodlist
        context['collection_area_id'] = 'not_in_message'
        context['ignore_foo'] = True
        context['content'] = self.file_msg
        scene_from_msg.return_value = None
        res = self.loader.invoke(context)
        self.assertIsNone(res)
        self.assertFalse(self.context['prev_lock'].locked())
        self.assertFalse(self.context['lock'].locked())
        self.assertTrue(scene_from_msg.called)

    @patch('trollflow_sat.satpy_compositor.utils.send_message')
    @patch('trollflow_sat.satpy_compositor.utils.get_monitor_metadata')
    @patch('trollflow_sat.satpy_compositor.SceneLoader.create_scene_from_message')
    def test_invoke_scene_monitor_msg(self, scene_from_msg,
                                      get_monitor_metadata, send_message):
        context = self.context
        context['instruments'] = ['spam']
        context['product_list'] = self.prodlist
        context['collection_area_id'] = 'not_in_message'
        context['ignore_foo'] = True
        context['content'] = self.file_msg
        context['monitor_topic'] = self.topic
        # Set non-existent collection area ID
        context['content'].data['collection_area_id'] = 'asd'
        scene_from_msg.return_value = self.scene
        get_monitor_metadata.return_value = {}

        res = self.loader.invoke(context)
        self.assertIsNone(res)
        self.assertFalse(self.context['prev_lock'].locked())
        self.assertFalse(self.context['lock'].locked())
        self.assertTrue(scene_from_msg.called)
        metadata = METADATA_FILE.copy()
        metadata['collection_area_id'] = 'asd'
        get_monitor_metadata.assert_has_calls([call(metadata,
                                                    status='start',
                                                    service=None),
                                               call(metadata,
                                                    status='completed',
                                                    service=None)])
        send_message.assert_has_calls([call(self.topic, 'monitor', {},
                                            nameservers=None, port=0),
                                       call(self.topic, 'monitor', {},
                                            nameservers=None, port=0)])
        self.assertIsNone(self.output_queue.get(timeout=1))

    @patch('trollflow_sat.satpy_compositor.SceneLoader.load_composites')
    @patch('trollflow_sat.satpy_compositor.SceneLoader.create_scene_from_message')
    def test_invoke_scene(self, scene_from_msg, load_composites):
        context = self.context
        context['instruments'] = ['spam']
        context['product_list'] = self.prodlist
        context['content'] = self.file_msg
        context['use_lock'] = True
        scene_from_msg.return_value = self.scene
        load_composites.return_value = {}

        res = self.loader.invoke(context)
        self.assertIsNone(res)
        self.assertFalse(self.context['prev_lock'].locked())
        self.assertFalse(self.context['lock'].locked())
        self.assertTrue(scene_from_msg.called)
        self.assertTrue(load_composites.called)
        self.assertIsNotNone(self.output_queue.get(timeout=1))

    def test_post_invoke(self):
        self.assertIsNone(self.loader.post_invoke())

    @patch('trollflow_sat.satpy_compositor.Scene')
    def test_create_scene_from_message(self, scene):
        from copy import deepcopy
        scene.return_value = Mock(attrs={})
        # Incorrect message type
        msg = deepcopy(self.file_msg)
        msg.type = 'spam'
        self.assertIsNone(self.loader.create_scene_from_message(msg, None, None))

        # Unconfigured instrument
        msg = deepcopy(self.file_msg)
        res = self.loader.create_scene_from_message(msg, ['eggs'], None)
        self.assertIsNone(res)

        # Proper file message
        msg = deepcopy(self.file_msg)
        res = self.loader.create_scene_from_message(msg, ['sensor1'], None)
        self.assertEqual(res.attrs, METADATA_FILE)

    @patch('trollflow_sat.satpy_compositor.Scene')
    def test_create_scene_from_mda(self, scene):
        from copy import deepcopy

        # Message type is dataset
        scene.return_value = Mock(attrs={})
        msg = deepcopy(self.dataset_msg)
        msg.data['sensor'] = [msg.data['sensor']]
        res = self.loader.create_scene_from_mda(msg.data, "dataset",
                                                ['sensor1'], None)
        meta = METADATA_DATASET.copy()
        meta['sensor'] = [meta['sensor']]
        self.assertEqual(res.attrs, meta)

        # No readers found
        scene.return_value = Mock(attrs={})
        scene.side_effect = ValueError
        msg = deepcopy(self.dataset_msg)
        msg.data['sensor'] = [msg.data['sensor']]
        res = self.loader.create_scene_from_mda(msg.data, "dataset",
                                                ['sensor1'], None)

        # Collection
        msg = deepcopy(self.collection_msg)
        # Reset the return value attrs dictionary
        scene.return_value = Mock(attrs={})
        scene.side_effect = None
        res = self.loader.create_scene_from_mda(msg.data, "collection",
                                                ['sensor1'], None)
        self.assertEqual(res.attrs, METADATA_COLLECTION)

        # Collection of datasets
        msg = deepcopy(self.collection_dataset_msg)
        scene.return_value = Mock(attrs={})
        res = self.loader.create_scene_from_mda(msg.data, "collection",
                                                ['sensor1'], None)
        self.assertEqual(res.attrs, METADATA_COLLECTION_DATASET)

    @patch('trollflow_sat.satpy_compositor.utils.bad_sunzen_range_satpy')
    def test_load_composites(self, bad_sunzen_range_satpy):
        # Check for unload
        glbl_data = MockScene(attrs=METADATA_FILE)
        bad_sunzen_range_satpy.return_value = True
        dset = Mock(name='overview')
        glbl_data.datasets[dset] = None
        self.loader.load_composites(glbl_data, PRODUCT_LIST, 'area1')
        self.assertEqual(len(glbl_data.datasets), 0)

        # Check for load
        glbl_data = MockScene(attrs=METADATA_FILE)
        bad_sunzen_range_satpy.return_value = False
        self.loader.load_composites(glbl_data, PRODUCT_LIST, 'area1')
        self.assertEqual(len(glbl_data.datasets), 1)


def write_yaml(data):
    import yaml
    import tempfile

    fname = tempfile.mktemp(suffix='.yaml')
    with open(fname, 'w') as fid:
        yaml.dump(data, fid)

    return fname


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestSceneLoader))

    return mysuite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
