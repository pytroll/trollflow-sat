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

"""Unit tests for utils"""

import unittest
from io import StringIO
import datetime as dt

from collections import OrderedDict
try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call

from trollflow_sat import utils
from trollflow.utils import ordered_load
from posttroll.message import Message

CONFIG_MINIMAL = u"""common:
  use_extern_calib: false

groups:
  all:
    - EPSG4326

product_list:
  EPSG4326:
    areaname: EPSG4326
    products:
      image_compositor_name:
        productname: dummy
"""


class TestUtils(unittest.TestCase):

    config = ordered_load(StringIO(CONFIG_MINIMAL))
    info = {'time': dt.datetime(2016, 11, 7, 12, 0),
            'platform_name': 'Meteosat-10',
            'area_id': 'EPSG4326',
            'productname': 'dummy',
            'sensor': ['seviri']}

    def test_create_fnames(self):
        # Absolute minimum config
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "20161107_1200_Meteosat-10_EPSG4326_dummy.png")
        self.assertEqual(prod_name, 'dummy')

        # Add output_dir
        self.config["common"]["output_dir"] = "/tmp/{time:%Y/%m/%d}"
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "20161107_1200_Meteosat-10_EPSG4326_dummy.png")

        # Add filename pattern
        self.config["common"]["fname_pattern"] = \
            "{time:%Y_%m_%d_%H_%M}_asd.{format}"
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.tif")

        # Add file formats
        self.config["common"]["formats"] = [OrderedDict([('format', 'png'), ]),
                                            OrderedDict([('format', 'tif'), ])]
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.png")
        self.assertEqual(fnames[1],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.tif")

        # Change filename pattern to one where "time" is changed to
        # "satellite_time"
        self.config["common"][
            "fname_pattern"] = "{satellite_time:%Y_%m_%d_%H_%M}_asd.{format}"
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.png")

        # Change metadata so that the time name doesn't match pattern
        self.info['start_time'] = self.info['time']
        del self.info['time']
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.png")

    def test_get_data_time_from_message_data(self):
        msg = {'time': 'foo'}
        res = utils._get_data_time_from_message_data(msg)
        self.assertEqual(res, 'foo')
        msg = {'nominal_time': 'foo'}
        res = utils._get_data_time_from_message_data(msg)
        self.assertEqual(res, 'foo')
        msg = {'start_time': 'foo'}
        res = utils._get_data_time_from_message_data(msg)
        self.assertEqual(res, 'foo')
        msg = {}
        res = utils._get_data_time_from_message_data(msg)
        self.assertIsNone(res)

    def test_get_orbit_number_from_message_data(self):
        msg = {"orbit_number": 42}
        res = utils._get_orbit_number_from_message_data(msg)
        self.assertEqual(res, 42)
        msg = {}
        res = utils._get_orbit_number_from_message_data(msg)
        self.assertIsNone(res)

    def test_get_monitor_metadata(self):
        msg = Message('/topic', 'monitor', self.info)
        res = utils.get_monitor_metadata(msg, status='foo')
        self.assertEqual(res['message_time'], msg.time)
        self.assertEqual(res['data_time'], self.info["start_time"])
        self.assertEqual(res['platform_name'], self.info["platform_name"])
        self.assertEqual(res['sensor'], self.info["sensor"])
        self.assertIsNone(res['orbit_number'])
        self.assertEqual(res['status'], 'foo')

    def test_select_dict_items(self):
        info = {"a": "a_value", "b": "b_value", "c":
                [{"c_a": "c1_a_value", "c_b": "c1_b_value"},
                 {"c_a": "c2_a_value", "c_b": "c2_b_value"}]}

        selection = {'b_new': 'b'}
        res = utils.select_dict_items(info, selection)
        self.assertEqual(res, {'b_new': 'b_value'})

        selection = {'b_new': 'b', 'b2': 'a'}
        res = utils.select_dict_items(info, selection)
        self.assertEqual(res, {'b_new': 'b_value', 'b2': 'a_value'})

        selection = {'cXa': '/c/*/c_a', 'a': 'a'}
        res = utils.select_dict_items(info, selection)
        self.assertEqual(res, {'cXa': ['c1_a_value', 'c2_a_value'],
                               'a': 'a_value'})
        selection = [1, 2, 3]
        res = utils.select_dict_items(info, selection)
        self.assertEqual(res, {1: 1, 2: 2, 3: 3})
        selection = {'a': '/a'}
        res = utils.select_dict_items(info, selection)
        self.assertEqual(res, {'a': 'a_value'})

    def test_get_format_settings(self):
        from trollflow_sat.tests.utils import PRODUCT_LIST_TWO_AREAS
        res = utils.get_format_settings(PRODUCT_LIST_TWO_AREAS, 'overview',
                                        'area2')
        self.assertTrue('writer' in res[0])
        self.assertTrue('format' in res[0])
        self.assertTrue('fill_value' in res[0])

    @patch('trollflow_sat.utils.astronomy.sun_zenith_angle')
    def test_bad_sunzen_range(self, sun_zenith_angle):
        from trollflow_sat.tests.utils import PRODUCT_LIST_TWO_AREAS
        prod_conf = PRODUCT_LIST_TWO_AREAS.copy()
        # No sunzen limits configured
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertFalse(res)
        # Limit given for night product
        prod_conf = PRODUCT_LIST_TWO_AREAS.copy()
        prod = prod_conf['product_list']['area2']['products']['overview']
        prod['sunzen_night_minimum'] = 90.
        prod['sunzen_lon'] = 0.
        prod['sunzen_lat'] = 0.
        sun_zenith_angle.return_value = 85.
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertTrue(sun_zenith_angle.called)
        self.assertTrue(res)
        sun_zenith_angle.return_value = 95.
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertFalse(res)
        # Limit given for day product
        del prod['sunzen_night_minimum']
        prod['sunzen_day_maximum'] = 90.
        sun_zenith_angle.return_value = 95.
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertTrue(res)
        sun_zenith_angle.return_value = 85.
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertFalse(res)
        # No limits given
        del prod['sunzen_day_maximum']
        res = utils.bad_sunzen_range(prod_conf, 'area2',
                                     'overview', 'start_time')
        self.assertFalse(res)

    @patch('trollflow_sat.utils.Publish')
    def test_send_message(self, Publish):
        pub = Mock()
        Publish.return_value.__enter__.return_value = pub
        utils.send_message('topic', 'file', {}, nameservers=None)
        self.assertTrue(pub.send.called)
        pub = Mock()
        Publish.return_value.__enter__.return_value = pub
        utils.send_message('topic', 'file', {}, nameservers='foo')
        self.assertTrue(pub.send.called)

    @patch('trollflow_sat.utils.release_lock')
    def test_release_locks(self, release_lock):
        release_lock.return_value = 1
        log = Mock()
        lock = None
        res = utils.release_locks(lock, log=None, log_msg=None)
        self.assertTrue(release_lock.called)
        res = utils.release_locks(lock, log=log, log_msg=None)
        self.assertFalse(log.called)
        res = utils.release_locks(lock, log=log, log_msg='message')
        self.assertTrue(log.called)

    @patch('trollflow_sat.utils.trollflow_acquire_lock')
    def test_acquire_lock(self, trollflow_acquire_lock):
        trollflow_acquire_lock.return_value = 'foo'
        res = utils.acquire_lock(None)
        self.assertEqual(res, 'foo')
        self.assertTrue(trollflow_acquire_lock.called)

    @patch('trollflow_sat.utils.get_area_def')
    def test_covers(self, get_area_def):
        overpass = Mock()
        logger = Mock()
        res = utils.covers(overpass, 'area1', 0, logger)
        self.assertTrue(res)
        self.assertFalse(logger.info.called)
        overpass.area_coverage.return_value = 0
        res = utils.covers(overpass, 'area1', 10, logger)
        self.assertFalse(res)
        self.assertTrue(logger.info.called)
        overpass.area_coverage.return_value = 100
        res = utils.covers(overpass, 'area1', 10, logger)
        self.assertTrue(res)
        self.assertTrue(logger.info.called)
        overpass.area_coverage.side_effect = AttributeError
        res = utils.covers(overpass, 'area1', 10, logger)
        self.assertTrue(logger.warning.called)

    def test_add_overviews(self):
        r_open = Mock()
        rasterio = Mock(RasterioIOError=BaseException, open=r_open)
        import sys
        sys.modules['rasterio'] = rasterio
        from trollflow_sat.utils import add_overviews
        logger = Mock()
        fnames = ['a', 'b', 'c']
        overviews = None
        add_overviews(fnames, overviews, logger=logger)
        r_open.has_calls([call('a', 'r+'),
                          call('b', 'r+'),
                          call('c', 'r+')])


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestUtils))

    return mysuite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
