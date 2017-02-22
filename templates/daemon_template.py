"""Template for trollflow daemons showing the necessary parts. Rename
everything having 'Template' in the name, and also rename 'Worker'
class."""

import logging
import Queue
from threading import Thread
import time

from trollflow_sat import utils


class TemplateContainer(object):

    """Thread container for Worker instance"""

    logger = logging.getLogger("TemplateContainer")

    def __init__(self):
        self.worker = None
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None
        self._prev_lock = None

        # Create a worker instance
        self.worker = Worker(self.input_queue, self.output_queue,
                             prev_lock=self._prev_lock)

        # Start the Worker into a new daemonized thread.
        self.thread = Thread(target=self.worker.run)
        self.thread.setDaemon(True)
        self.thread.start()

    @property
    def input_queue(self):
        """Input queue property"""
        return self._input_queue

    @input_queue.setter
    def input_queue(self, queue):
        """Setter for input queue property"""
        self._input_queue = queue
        self.worker.input_queue = queue

    @property
    def prev_lock(self):
        """Property writer"""
        return self._prev_lock

    @prev_lock.setter
    def prev_lock(self, lock):
        """Set lock of the previous worker"""
        self._prev_lock = lock
        self.writer.prev_lock = lock

    def __setstate__(self, state):
        self.__init__(**state)

    def stop(self):
        """Stop gatherer."""
        self.logger.debug("Stopping Worker.")
        self.worker.stop()
        self.thread.join()
        self.logger.debug("Worker stopped.")
        self.thread = None


class Worker(Thread):

    """Template for a threaded worker."""

    logger = logging.getLogger("Worker")

    def __init__(self, input_queue, output_queue, prev_lock=None):
        Thread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._loop = False
        self.prev_lock = prev_lock

    def run(self):
        """Run the worker"""
        self._loop = True
        while self._loop:
            if self.input_queue is not None:
                try:
                    data = self.input_queue.get(True, 1)
                except Queue.Empty:
                    # After all the items have been processed, release the
                    # lock for the previous worker
                    utils.release_lock(self.prev_lock)
                    continue
                self.logger.info("New data received.")
                res = do_stuff(data)
                self.output_queue.put(res)
            else:
                time.sleep(1)

    def stop(self):
        """Stop Worker"""
        self._loop = False

    @property
    def loop(self):
        """Loop property"""
        return self._loop


def do_stuff(data):
    """Do something"""
    return data
