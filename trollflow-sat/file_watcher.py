"""Plugin for noticing new files."""

import logging
import Queue
from threading import Thread
import time
import pyinotify
from collections import deque, OrderedDict
import os.path
import datetime as dt

from posttroll.message import Message
from trollsift import parse

class FileWatcherContainer(object):

    """Thread container for FileWatcher instance"""

    logger = logging.getLogger("FileWatcherContainer")

    def __init__(self, config):
        self.worker = None
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a worker instance
        self.worker = FileWatcher(self.input_queue, self.output_queue, config)

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

    def __setstate__(self, state):
        self.__init__(**state)

    def stop(self):
        """Stop gatherer."""
        self.logger.debug("Stopping FileWatcher.")
        self.worker.stop()
        self.thread.join()
        self.logger.debug("Worker FileWatcher.")
        self.thread = None


class FileWatcher(Thread):

    """Template for a threaded worker."""

    logger = logging.getLogger("FileWatcher")

    def __init__(self, input_queue, output_queue, config):
        Thread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.config = config
        self._loop = False
        self._notifier = self._create_notifier()

    def _create_notifier(self):
        """Create new notifier."""
        wm_ = pyinotify.WatchManager()
        self._notifier = pyinotify.Notifier(wm_)
        #for 
        wm_.add_watch('/tmp', pyinotify.ALL_EVENTS)
        # asdasdasd

    def run(self):
        """Run the worker"""
        self._notifier.start()
        while self._loop:
            if self.input_queue is not None:
                try:
                    data = self.input_queue.get(True, 1)
                except Queue.Empty:
                    continue
                self.logger.info("New file received.")
                res = do_stuff(data)
                self.output_queue.put(res)
            else:
                time.sleep(1)

    def stop(self):
        """Stop Worker"""
        self._loop = False
        self._notifier.stop()

    @property
    def loop(self):
        """Loop property"""
        return self._loop


class ProcessFileEvent(pyinotify.ProcessEvent):

    """Process the inotify event"""

    def __init__(self, queue, config, logger):
        pyinotify.ProcessEvent.__init__(self)
        self.logger = logger
        self._queue = queue
        self._config = config
        self._patterns = config["patterns"]
        self._aliases = config["aliases"]
        self.info = OrderedDict()
        self._deque = deque([], config.get("history", 0))
        self._tbus_orbit = config.get("tbus_orbit", False)

    def process_IN_MODIFY(self, event):
        """Process modified file"""
        self._process(event)

    def process_IN_MOVED_TO(self, event):
        """Process moved file"""
        self._process(event)

    def process_IN_CLOSE_WRITE(self, event):
        """Process closed file."""
        self._process(event)

    def process_default(self, event):
        """For other events, do nothing."""
        pass

    def _process(self, event):
        """Process the received event."""
        # New file created and closed
        if not event.dir:
            self.logger.debug("Processing %s", event.pathname)
            # parse information and create self.info OrderedDict{}
            self.parse_file_info(event)
            if len(self.info) > 0:
                # Check if this file has been recently dealt with
                if event.pathname not in self._deque:
                    self._deque.append(event.pathname)
                    message = self.create_message()
                    self.logger.info("Publishing message %s", str(message))
                    self._queue.put(str(message))
                else:
                    self.logger.info("Data has been published recently, "
                                     "skipping.")
            self.clean()

    def clean(self):
        '''Clean instance attributes.
        '''
        self.info = OrderedDict()

    def create_message(self):
        """Create broadcasted message
        """
        return Message("/placeholder", 'file', dict(self.info))

    def parse_file_info(self, event):
        '''Parse satellite and orbit information from the filename.
        Message is sent, if a matching filepattern is found.
        '''
        try:
            self.logger.debug("filter: %s\t event: %s",
                              str(self._patterns), event.pathname)
            self.clean()
            # Check all parsers, use first succesfull
            info = None
            for pattern in self._patterns:
                try:
                    info = parse(pattern, os.path.basename(event.pathname))
                    break
                except ValueError:
                    pass
            if info is not None:
                self.logger.debug("Extracted: %s", str(info))
                self.info.update(info)
            else:
                raise ValueError
        except ValueError:
            # Filename didn't match pattern, so empty the info dict
            self.logger.info("Couldn't extract any usefull information")
            self.clean()
        else:
            self.info['uri'] = event.pathname
            self.info['uid'] = os.path.basename(event.pathname)
            self.info['sensor'] = self._config["metadata"]["instruments"]
            self.logger.debug("self.info['sensor']: %s",
                              str(self.info['sensor']))

            if self._tbus_orbit and "orbit_number" in self.info:
                self.logger.info("Changing orbit number by -1!")
                self.info["orbit_number"] -= 1

            # replace values with corresponding aliases, if any are given
            if "aliases" in self._config:
                info = self.info.copy()
                for key in info:
                    if key in self._config["aliases"]:
                        self.info['orig_'+key] = self.info[key]
                        self.info[key] = \
                            self._config["aliases"][key][str(self.info[key])]

            # add start_time and end_time if not present
            try:
                base_time = self.info["time"]
            except KeyError:
                try:
                    base_time = self.info["nominal_time"]
                except KeyError:
                    base_time = self.info["start_time"]
            if "start_time" not in self.info:
                self.info["start_time"] = base_time
            if "start_date" in self.info:
                self.info["start_time"] = \
                    dt.datetime.combine(self.info["start_date"].date(),
                                        self.info["start_time"].time())
                if "end_date" not in self.info:
                    self.info["end_date"] = self.info["start_date"]
                del self.info["start_date"]
            if "end_date" in self.info:
                self.info["end_time"] = \
                    dt.datetime.combine(self.info["end_date"].date(),
                                        self.info["end_time"].time())
                del self.info["end_date"]
            granule_length = self._config.get("granule_length", 0)
            if "end_time" not in self.info and granule_length > 0:
                self.info["end_time"] = \
                        base_time + dt.timedelta(seconds=granule_length)

            if "end_time" in self.info:
                while self.info["start_time"] > self.info["end_time"]:
                    self.info["end_time"] += dt.timedelta(days=1)

            # Replace/add static metadata
            for key in self._config["metadata"]:
                self.info[key] = self._config["metadata"][key]
