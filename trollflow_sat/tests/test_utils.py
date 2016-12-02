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
from StringIO import StringIO
import datetime as dt
from collections import OrderedDict

from trollflow_sat import utils
from trollflow.utils import ordered_load

CONFIG_MINIMAL = """common:
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
            'areaname': 'EPSG4326',
            'productname': 'dummy'}

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
                         "2016_11_07_12_00_asd.png")

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
        self.info['foo_time'] = dt.datetime(2016, 11, 7, 12, 0)
        del self.info['time']
        fnames, prod_name = utils.create_fnames(self.info,
                                                self.config,
                                                "image_compositor_name")
        self.assertEqual(fnames[0],
                         "/tmp/2016/11/07/" +
                         "2016_11_07_12_00_asd.png")


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestUtils))

    return mysuite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
