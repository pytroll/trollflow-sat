#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016 Panu Lahtinen

# Author(s):

#   Panu Lahtinen <pnuu+git@iki.fi>

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

"""Setup for trollflow-sat.
"""
from setuptools import setup
import imp

version = imp.load_source('trollflow_sat.version', 'trollflow_sat/version.py')

setup(name="trollflow_sat",
      version=version.__version__,
      description='Pytroll workflow plugins for satellite data',
      author='Panu Lahtinen',
      author_email='panu.lahtinen@fmi.fi',
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Science/Research",
                   "License :: OSI Approved :: GNU General Public License v3 " +
                   "or later (GPLv3+)",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Scientific/Engineering"],
      url="https://github.com/pytroll/trollflow-sat",
      packages=['trollflow_sat', ],
      scripts=[],
      data_files=[],
      zip_safe=False,
      install_requires=['pyyaml', 'trollflow', 'posttroll', 'trollsift',
                        'pykdtree', 'mipp', 'mpop'],
      tests_require=['trollflow'],
      test_suite='trollflow_sat.tests.suite',
      )
