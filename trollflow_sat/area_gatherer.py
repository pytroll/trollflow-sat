"""Classes for handling area gathering for Trollflow based Trollduction"""

import logging
import Queue
from threading import Thread
import time
import datetime as dt

from posttroll import message

from trollduction.collectors import region_collector


class AreaGathererContainer(object):

    """Container for area gatherer."""

    logger = logging.getLogger("AreaGathererContainer")

    def __init__(self, config):
        self.gatherer = None
        self._input_queue = None
        self.output_queue = Queue.Queue()
        self.thread = None

        # Create a AreaGatherer instance
        self.gatherer = AreaGatherer(config, self.input_queue,
                                     self.output_queue)

        # Start AreaGatherer into a new daemonized thread.
        self.thread = Thread(target=self.gatherer.run)
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
        self.gatherer.input_queue = queue

    def __setstate__(self, state):
        self.__init__(**state)

    def stop(self):
        """Stop gatherer."""
        self.logger.debug("Stopping AreaGatherer.")
        self.gatherer.stop()
        self.thread.join()
        self.logger.debug("AreaGatherer stopped.")
        self.thread = None


class AreaGatherer(Thread):

    """Class for gathering segments together to cover a given area."""

    logger = logging.getLogger("AreaGatherer")

    def __init__(self, config, input_queue, output_queue):
        Thread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._loop = False

        self.timeliness = dt.timedelta(minutes=config["timeliness"])
        self._pattern = config["pattern"]

        try:
            self._min_coverage = config["min_coverage"] / 100.0
        except KeyError:
            self._min_coverage = 0.0
        try:
            self._duration = dt.timedelta(seconds=config["duration"])
        except KeyError:
            self._duration = None

        if config["aliases"] is not None:
            self._aliases = config["aliases"]
        else:
            self._aliases = {}
        if config["metadata"] is not None:
            self._metadata = config["metadata"]
        else:
            self._metadata = {}

        self._platform_names = config["platform_names"]
        self._regions = config["regions"]

        self.collectors = {}
        self.create_collectors()

    def create_collectors(self):
        """Create area collectors for each platform."""
        for platform in self._platform_names:
            self.collectors[platform] = \
                [region_collector.RegionCollector(region,
                                                  self._timeliness,
                                                  self._duration) for
                 region in self._regions]

    @property
    def loop(self):
        """Loop property"""
        return self._loop

    def _check_timeouts(self):
        """Check if timeouts have happened."""
        for platform in self._platforms:
            timeouts = [(collector, collector.timeout)
                        for collector in self.collectors[platform]
                        if collector.timeout is not None]
            if timeouts:
                next_timeout = min(timeouts, key=(lambda x: x[1]))
                if (next_timeout[1] and
                        (next_timeout[1] < dt.datetime.utcnow())):
                    self.logger.warning("Timeout detected, terminating "
                                        "collector")
                    self.logger.debug("Area: %s, timeout: %s",
                                      next_timeout[0].region,
                                      str(next_timeout[1]))
                    self.terminator(next_timeout[0].finish())
                else:
                    self.logger.debug("Waiting %s seconds until timeout",
                                      str(total_seconds(next_timeout[1] -
                                                        dt.datetime.utcnow())))

    def terminator(self, metadata):
        """Dummy terminator function.
        """
        sorted_mda = sorted(metadata, key=lambda x: x["start_time"])

        mda = metadata[0].copy()

        mda['end_time'] = sorted_mda[-1]['end_time']
        mda['collection_area_id'] = sorted_mda[-1]['collection_area_id']
        mda['collection'] = []

        is_correct = False
        for meta in sorted_mda:
            new_mda = {}
            if "uri" in meta or 'dataset' in meta:
                is_correct = True
            for key in ['dataset', 'uri', 'uid']:
                if key in meta:
                    new_mda[key] = meta[key]
                new_mda['start_time'] = meta['start_time']
                new_mda['end_time'] = meta['end_time']
            mda['collection'].append(new_mda)

        for key in ['dataset', 'uri', 'uid']:
            if key in mda:
                del mda[key]

        if is_correct:
            msg = message.Message("/placeholder", "collection",
                                  mda)
            self.logger.info("Collection ready %s", str(msg))
            self.output_queue.put(msg)
        else:
            self.logger.warning("Malformed metadata, no key: %s", "uri")

    def run(self):
        """Run SegmentGatherer"""
        self._loop = True
        while self._loop:
            msg = None
            if self.input_queue is not None:
                # Check timeouts
                self._check_timeouts()

                try:
                    # Get new message from the queue
                    msg = self.input_queue.get(True, 1)
                    metadata = msg.data
                    # Replace aliases
                    for key, aliases in self._aliases.items():
                        if key in metadata:
                            metadata[key] = aliases.get(metadata[key],
                                                        metadata[key])
                    for collector in self.collectors["platform_name"]:
                        res = collector(metadata)
                        if res:
                            msg = self.terminator(res)
                            self.output_queue.put(msg)
                except KeyboardInterrupt:
                    self.stop()
                    continue
                except Queue.Empty:
                    continue
            else:
                time.sleep(1)
                continue

    def stop(self):
        """Stop gatherer."""
        self.logger.info("Stopping AreaGatherer.")
        self._loop = False


def total_seconds(tdef):
    """Calculate total time in seconds.
    """
    return ((tdef.microseconds +
             (tdef.seconds + tdef.days * 24 * 3600) * 10 ** 6) / 10.0 ** 6)
