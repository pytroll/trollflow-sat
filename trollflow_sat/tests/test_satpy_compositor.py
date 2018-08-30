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

from trollflow_sat.satpy_compositor import SceneLoader


class TestSceneLoader(unittest.TestCase):

    loader = SceneLoader()

    def test_init(self):
        self.assertFalse(self.loader.use_lock)
        self.assertFalse(self.loader.slots)

    def test_pre_invoke(self):
        self.assertIsNone(self.loader.pre_invoke())

    def test_invoke(self):
        from threading import Lock
        lock = Lock()
        prev_lock = Lock()
        context = {'lock': lock, 'prev_lock': prev_lock}
        self.assertIsNone(self.loader.invoke(context))

    def test_post_invoke(self):
        self.assertIsNone(self.loader.post_invoke())


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestSceneLoader))

    return mysuite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
