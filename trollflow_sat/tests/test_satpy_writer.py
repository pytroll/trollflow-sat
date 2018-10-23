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

"""Unit tests for SatPy writer plugin"""

import unittest
try:
    from unittest.mock import patch, Mock, call
except ImportError:
    from mock import patch, Mock, call

from trollflow_sat.satpy_writer import DataWriter, DataWriterContainer


class TestDataWriter(unittest.TestCase):

    def setUp(self):
        import six.moves.queue as queue
        self.queue = queue.Queue()

    def tearDown(self):
        pass

    def test_init(self):
        writer = DataWriter(queue=self.queue)
        self.assertEqual(writer.queue, self.queue)
        writer = DataWriter(nameservers='a')
        self.assertEqual(writer._nameservers, ['a'])
        writer = DataWriter(nameservers=['a', 'b'])
        self.assertEqual(writer._nameservers, ['a', 'b'])

    # The run() method is tested via DataWriterContainer so it can be
    # stopped easily
    def test_run(self):
        pass


class TestDataWriterContainer(unittest.TestCase):

    def setUp(self):
        import six.moves.queue as queue
        self.queue = queue.Queue()
        self.writer = DataWriterContainer()

    def tearDown(self):
        self.writer.stop()

    @patch('trollflow_sat.satpy_writer.DataWriterContainer._init_writer')
    def test_init(self, init_writer):
        writer = DataWriterContainer()
        self.assertIsNone(writer.topic)
        self.assertIsNone(writer._input_queue)
        self.assertIsNone(writer.output_queue)
        self.assertIsNone(writer.thread)
        self.assertFalse(writer.use_lock)
        self.assertEqual(writer._save_settings, {})
        self.assertIsNone(writer._topic)
        self.assertEqual(writer._port, 0)
        self.assertIsNone(writer._nameservers)
        self.assertIsNone(writer._publish_vars)
        self.assertTrue(init_writer.called)

    def test_init_writer(self):
        self.assertTrue(self.writer.thread.isAlive())

    def test_input_queue(self):
        self.assertIsNone(self.writer.input_queue)
        self.writer.input_queue = 'foo'
        self.assertEqual(self.writer.input_queue, 'foo')
        self.assertEqual(self.writer.writer.queue, 'foo')

    def test_prev_lock(self):
        self.assertIsNone(self.writer.prev_lock)
        self.writer.prev_lock = 'foo'
        self.assertIsNone(self.writer.prev_lock)
        self.writer.use_lock = True
        self.writer.prev_lock = 'foo'
        self.assertEqual(self.writer.prev_lock, 'foo')
        self.assertEqual(self.writer.writer.prev_lock, 'foo')

    def test_stop(self):
        self.writer.stop()
        self.assertFalse(self.writer.writer._loop)
        self.assertIsNone(self.writer.thread)

    def test_restart(self):
        self.writer.restart()
        self.writer.writer.stop()
        self.writer.writer = None
        self.assertIsNone(self.writer.writer)
        self.writer.restart()
        self.assertIsNotNone(self.writer.writer)

    def test_is_alive(self):
        self.assertTrue(self.writer.is_alive())
        self.writer.writer.stop()
        self.writer.thread.join()
        self.assertFalse(self.writer.is_alive())

    @patch('trollflow_sat.satpy_writer.DataWriter._process')
    @patch('trollflow_sat.satpy_writer.DataWriter._compute')
    @patch('trollflow_sat.satpy_writer.Publish')
    def test_datawriter_run_mock_process(self, Publish, compute, process):
        import six.moves.queue as queue
        import time
        queue = queue.Queue()
        self.writer.writer.queue = queue
        self.writer.writer.data.append('foo')
        self.writer.writer.messages.append('foo')
        # Add terminator to the queue
        queue.put(None)
        # Wait for the queue to be read
        time.sleep(1)
        self.assertTrue(compute.called)
        # data and message lists should be empty
        self.assertEqual(self.writer.writer.data, [])
        self.assertEqual(self.writer.writer.messages, [])
        queue.put('foo')
        time.sleep(1)
        self.assertTrue(process.called)

    @patch('trollflow_sat.satpy_writer.DataWriter._create_message')
    @patch('trollflow_sat.satpy_writer.utils.get_format_settings')
    @patch('trollflow_sat.satpy_writer.utils.create_fnames')
    @patch('trollflow_sat.satpy_writer.utils.release_locks')
    @patch('trollflow_sat.satpy_writer.utils.acquire_lock')
    @patch('trollflow_sat.satpy_writer.Publish')
    def test_datawriter_run_mock_scene(self, Publish, acquire_lock,
                                       release_locks, create_fnames,
                                       get_format_settings,
                                       create_message):
        import six.moves.queue as queue
        import time
        from trollflow_sat.tests.utils import (METADATA_FILE, MockScene,
                                               PRODUCT_LIST)

        create_fnames.return_value = (['overview.png'], 'overview')
        get_format_settings.return_value = [{'fill_value': 0,
                                             'writer': 'foo'}]
        create_message.return_value = 'msg'
        self.writer.use_lock = True
        self.writer.prev_lock = 'foo'
        queue = queue.Queue()
        self.writer.writer.queue = queue
        scene = MockScene(attrs=METADATA_FILE)
        scene.attrs['area_id'] = 'area1'
        scene.load(['overview'])
        prod_list = PRODUCT_LIST['product_list']['area1']['products']
        # Add a missing product
        prod_list['missing'] = {}
        meta = {'product_config': PRODUCT_LIST, 'products': prod_list}
        queue.put({'scene': scene, 'extra_metadata': meta})
        time.sleep(1)

        self.assertTrue(create_fnames.called)
        self.assertTrue(get_format_settings)
        self.assertTrue(get_format_settings)
        # acquire_lock.assert_called_with(call(self.writer.prev_lock))
        self.assertTrue(acquire_lock.called)
        self.assertTrue(release_locks.called)

    @patch('trollflow_sat.satpy_writer.DataWriter._add_overviews')
    @patch('trollflow_sat.satpy_writer.DataWriter._send_messages')
    @patch('trollflow_sat.satpy_writer.compute_writer_results')
    def test_compute(self, compute_writer_results, send_messages,
                     add_overviews):
        self.writer._save_settings['overviews'] = None
        self.writer.writer.data = 'foo'
        self.writer.writer._compute()
        self.assertTrue(compute_writer_results.called)
        self.assertTrue(send_messages.called)
        self.assertTrue(add_overviews.called)

    @patch('trollflow_sat.utils.add_overviews')
    def test_add_overviews(self, add_overviews):
        logger = Mock()
        class mock_msg(object):
            def __init__(self, uri):
                self.data = {'uri': uri}
        msg1 = mock_msg('uri1')
        msg2 = mock_msg('uri2')
        self.writer._save_settings['overviews'] = None
        self.writer.writer.logger = logger
        self.writer.writer.messages = [msg1, msg2]
        self.writer.writer._add_overviews()
        add_overviews.assert_has_calls([call(['uri1', 'uri2'], None,
                                             logger=logger)])

    def test_send_messages(self):
        pub = Mock()
        self.writer.writer.pub = pub
        self.writer.writer.messages = [1, 2]
        self.writer.writer._send_messages()
        pub.send.assert_has_calls([call('1'), call('2')])

    @patch('trollflow_sat.satpy_writer.Message')
    def test_create_message(self, Message):
        from trollflow_sat.tests.utils import METADATA_FILE
        Message.return_value = 'message'
        # No topic set, should return imediately
        self.writer.writer._create_message(None, None, None, None)

        # Commong values
        self.writer.writer._topic = 'topic'
        fname = 'fname'
        scn_metadata = METADATA_FILE.copy()
        productname = 'productname'

        # missing area metadata
        area = 'area'
        self.writer.writer._create_message(area, fname, scn_metadata,
                                           productname)
        self.assertEqual(len(self.writer.writer.messages), 1)
        self.assertTrue('message' in self.writer.writer.messages)

        area = Mock(name='name', area_id='area_id', proj_id='proj_id',
                    proj4_string='proj4_string', x_size='x_size',
                    y_size='y_size')
        self.writer.writer._create_message(area, fname, scn_metadata,
                                           productname)
        self.assertEqual(len(self.writer.writer.messages), 2)
        self.assertTrue('message' in self.writer.writer.messages)


def suite():
    """The suite for test_utils
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestDataWriter))
    mysuite.addTest(loader.loadTestsFromTestCase(TestDataWriterContainer))

    return mysuite


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
