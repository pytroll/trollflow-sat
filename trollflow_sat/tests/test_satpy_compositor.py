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
from unittest.mock import patch, Mock, call
import datetime as dt

from trollflow_sat.satpy_compositor import SceneLoader

PRODUCT_LIST = {
    "product_list": {
        "area1":
        {
            "areaname": "areaname1",
            "products":
            {
                "productname": "overview",
                "fname_pattern": "pattern",
                "formats": [{"format": "tif", "writer": None}]
            }
        }
    }
}

METADATA = {"start_time": dt.datetime(2018, 8, 31, 12, 0),
            "end_time": dt.datetime(2018, 8, 31, 12, 15)
}


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
        self.msg = Message('/topic', 'file', METADATA)
        self.dset1 = Mock(name='dset1')
        self.dset2 = Mock(name='dset2')
        self.scene = Mock(attrs=METADATA, datasets=[self.dset1, self.dset2])

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
    def test_invoke_scene_is_none(self, foo):
        context = self.context
        context['instruments'] = ['spam']
        context['product_list'] = write_yaml(PRODUCT_LIST)
        context['collection_area_id'] = 'not_in_message'
        context['ignore_foo'] = True
        context['content'] = self.msg
        foo.return_value = None
        res = self.loader.invoke(context)
        self.assertIsNone(res)
        self.assertFalse(self.context['prev_lock'].locked())
        foo.assert_called_once()

    @patch('trollflow_sat.satpy_compositor.utils.send_message')
    @patch('trollflow_sat.satpy_compositor.utils.get_monitor_metadata')
    @patch('trollflow_sat.satpy_compositor.SceneLoader.create_scene_from_message')
    def test_invoke_scene_monitor_msg(self, foo, bar, baz):
        context = self.context
        context['instruments'] = ['spam']
        context['product_list'] = write_yaml(PRODUCT_LIST)
        context['collection_area_id'] = 'not_in_message'
        context['ignore_foo'] = True
        context['content'] = self.msg
        context['monitor_topic'] = '/topic'
        # Set non-existent collection area ID
        context['content'].data['collection_area_id'] = 'asd'
        foo.return_value = self.scene
        bar.return_value = {}

        res = self.loader.invoke(context)
        self.assertIsNone(res)
        self.assertFalse(self.context['prev_lock'].locked())
        foo.assert_called_once()
        bar.assert_called_once()
        baz.assert_any_call('/topic', 'monitor', {'status': 'completed'},
                            nameservers=None, port=0)
        #baz.assert_has_calls([call('/topic', 'monitor', {}, nameservers=None,
        #                           port=0), 
        #                      call('/topic', 'monitor', {'status': 'completed'},
        #                           nameservers=None, port=0)])

    def test_post_invoke(self):
        self.assertIsNone(self.loader.post_invoke())


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
