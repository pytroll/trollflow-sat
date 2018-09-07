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

"""Unit tests for SatPy resampler plugin"""

import unittest

try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call

from trollflow_sat.satpy_resampler import Resampler
from trollflow_sat.tests.utils import (write_yaml, PRODUCT_LIST, MockScene,
                                       METADATA_FILE, PRODUCT_LIST_SATPROJ,
                                       PRODUCT_LIST_TWO_AREAS)


class TestResampler(unittest.TestCase):

    def setUp(self):
        from threading import Lock
        import six.moves.queue as queue

        self.resampler = Resampler()
        self.lock = Lock()
        self.prev_lock = Lock()
        self.output_queue = queue.Queue()
        self.context = {'lock': self.lock, 'prev_lock': self.prev_lock,
                        'output_queue': self.output_queue}
        self.prodlist = write_yaml(PRODUCT_LIST)
        self.prodlist_satproj = write_yaml(PRODUCT_LIST_SATPROJ)
        self.prodlist_two_areas = write_yaml(PRODUCT_LIST_TWO_AREAS)

    def tearDown(self):
        import os
        os.remove(self.prodlist)
        os.remove(self.prodlist_satproj)
        os.remove(self.prodlist_two_areas)

    def test_init(self):
        self.assertFalse(self.resampler.use_lock)

    def test_pre_invoke(self):
        self.assertIsNone(self.resampler.pre_invoke())

    @patch('trollflow_sat.satpy_resampler.utils.acquire_lock')
    @patch('trollflow_sat.satpy_resampler.utils.release_lock')
    def test_invoke_none(self, release, acquire):
        context = self.context
        context['use_lock'] = True
        context['content'] = None
        self.resampler.invoke(context)
        self.assertEqual(context['output_queue'].qsize(), 1)
        self.assertIsNone(context['output_queue'].get(timeout=1))
        self.assertTrue(acquire.called)
        self.assertTrue(release.called)

    @patch('trollflow_sat.satpy_resampler.utils.covers')
    @patch('trollflow_sat.satpy_resampler.Pass')
    def test_invoke_scene_no_coverage(self, Pass, covers):
        import six.moves.queue as queue
        scene = MockScene(attrs=METADATA_FILE)
        context = self.context
        context['content'] = {'scene': scene,
                              'extra_metadata': {'area_id': 'area1'}}
        context['product_list'] = self.prodlist
        covers.return_value = False

        self.resampler.invoke(context)
        self.assertTrue(Pass.called)
        self.assertTrue(any(covers.mock_calls))
        self.assertRaises(queue.Empty, context['output_queue'].get, timeout=1)

    @patch('trollflow_sat.satpy_resampler.utils.covers')
    @patch('trollflow_sat.satpy_resampler.Pass')
    def test_invoke_scene(self, Pass, covers):
        scene = MockScene(attrs=METADATA_FILE)
        context = self.context
        context['content'] = {'scene': scene,
                              'extra_metadata': {'area_id': 'area1'}}
        context['product_list'] = self.prodlist
        context['process_by_area'] = True
        context['use_lock'] = True

        covers.return_value = True

        self.resampler.invoke(context)
        self.assertTrue(Pass.called)
        self.assertTrue(any(covers.mock_calls))
        self.assertIsNotNone(context['output_queue'].get(timeout=1))

    @patch('trollflow_sat.satpy_resampler.utils.covers')
    @patch('trollflow_sat.satpy_resampler.Pass')
    def test_invoke_scene_satproj(self, Pass, covers):
        scene = MockScene(attrs=METADATA_FILE)
        context = self.context
        context['content'] = {'scene': scene,
                              'extra_metadata': {'area_id': 'satproj'}}
        context['product_list'] = self.prodlist_satproj
        context['process_by_area'] = True
        context['use_lock'] = True
        context['radius'] = None
        context['cache_dir'] = '/path'
        covers.return_value = True

        self.resampler.invoke(context)
        self.assertTrue(Pass.called)
        self.assertTrue(any(covers.mock_calls))
        lcl = context['output_queue'].get(timeout=1)
        self.assertTrue(lcl['scene'] is scene)

    @patch('trollflow_sat.satpy_resampler.utils.covers')
    @patch('trollflow_sat.satpy_resampler.Pass')
    def test_invoke_overpass_is_none(self, Pass, covers):
        scene = MockScene(attrs=METADATA_FILE)
        context = self.context
        context['content'] = {'scene': scene,
                              'extra_metadata': {'area_id': 'area1'}}
        context['product_list'] = self.prodlist
        context['process_by_area'] = True
        Pass.return_value = None

        self.resampler.invoke(context)
        self.assertFalse(any(covers.mock_calls))
        self.assertIsNotNone(context['output_queue'].get(timeout=1))

    def test_post_invoke(self):
        self.assertIsNone(self.resampler.post_invoke())


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestResampler))

    return mysuite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
