
import Queue
from threading import Thread
import logging
import time
import os.path

from posttroll.publisher import Publish
from posttroll.message import Message
from trollflow_sat import utils
from trollflow.utils import acquire_lock, release_lock
from trollsift import compose


class DataWriterContainer(object):

    '''Container for DataWriter instance
    '''

    logger = logging.getLogger("DataWriterContainer")

    def __init__(self, topic=None, port=0, nameservers=None,
                 save_settings=None, use_lock=False):
        self.topic = topic
        self._input_queue = None
        self.output_queue = None  # Queue.Queue()
        self.thread = None
        self._prev_lock = None
        self.use_lock = use_lock

        # Create a Writer instance
        self.writer = DataWriter(queue=self.input_queue,
                                 save_settings=save_settings,
                                 topic=topic,
                                 port=port,
                                 nameservers=nameservers,
                                 prev_lock=self._prev_lock)
        # Start Writer instance into a new daemonized thread.
        self.thread = Thread(target=self.writer.run)
        self.thread.setDaemon(True)
        self.thread.start()

    @property
    def input_queue(self):
        """Property writer"""
        return self._input_queue

    @input_queue.setter
    def input_queue(self, queue):
        """Set writer queue"""
        self._input_queue = queue
        self.writer.queue = queue

    @property
    def prev_lock(self):
        """Property writer"""
        return self._prev_lock

    @prev_lock.setter
    def prev_lock(self, lock):
        """Set lock of the previous worker"""
        if self.use_lock:
            self._prev_lock = lock
            self.writer.prev_lock = lock

    def __setstate__(self, state):
        self.__init__(**state)

    def restart(self):
        '''Restart writer after configuration update.
        '''
        if self.writer is not None:
            if self.writer.loop:
                self.stop()
        self.__init__()

    def stop(self):
        '''Stop writer.'''
        self.logger.debug("Stopping writer.")
        self.writer.stop()
        self.thread.join()
        self.logger.debug("Writer stopped.")
        self.thread = None


class DataWriter(Thread):

    """Writes data to disk.
    """

    logger = logging.getLogger("DataWriter")

    def __init__(self, queue=None, save_settings=None,
                 topic=None, port=0, nameservers=None, prev_lock=None):
        Thread.__init__(self)
        self.queue = queue
        self._loop = False
        self._save_settings = save_settings
        self._port = port
        if nameservers is None:
            self._nameservers = []
        else:
            if type(nameservers) not in (list, tuple, set):
                nameservers = [nameservers, ]
            self._nameservers = nameservers
        self._topic = topic
        self.prev_lock = prev_lock

    def run(self):
        """Run the thread."""
        self._loop = True
        # Parse settings for saving
        compression = self._save_settings.get('compression', 6)
        tags = self._save_settings.get('tags', None)
        fformat = self._save_settings.get('fformat', None)
        gdal_options = self._save_settings.get('gdal_options', None)
        blocksize = self._save_settings.get('blocksize', None)

        kwargs = {'compression': compression,
                  'tags': tags,
                  'fformat': fformat,
                  'gdal_options': gdal_options,
                  'blocksize': blocksize}

        # Initialize publisher context
        with Publish("l2producer", port=self._port,
                     nameservers=self._nameservers) as pub:

            while self._loop:
                if self.queue is not None:
                    try:
                        lcl = self.queue.get(True, 1)
                        if self.prev_lock is not None:
                            self.logger.debug("Writer acquires lock of "
                                              "previous worker: %s",
                                              str(self.prev_lock))
                            acquire_lock(self.prev_lock)
                        self.queue.task_done()
                    except Queue.Empty:
                        # After all the items have been processed, release the
                        # lock for the previous worker
                        continue
                    info = lcl.info.copy()
                    time_name = utils.find_time_name(info)
                    product_config = lcl.info["product_config"]
                    products = lcl.info["products"]
                    dataset_ids = lcl.info["dataset_ids"]

                    for i, prod in enumerate(products):
                        fnames, _ = utils.create_fnames(info,
                                                        product_config,
                                                        prod)
                        # Some of the files might have specific
                        # writers, use them if configured
                        writers = utils.get_writer_names(product_config, prod,
                                                         info["area_id"])

                        for j, fname in enumerate(fnames):
                            if writers[j]:
                                self.logger.info("Saving %s with writer %s",
                                                 fname, writers[j])
                            else:
                                self.logger.info(
                                    "Saving %s with default writer", fname)

                            lcl.save_dataset(dataset_ids[i],
                                             filename=fname,
                                             writer=writers[j],
                                             **kwargs)

                            self.logger.info("Saved %s", fname)

                            area = lcl[prod].info["area"]
                            try:
                                area_data = {"name": area.name,
                                             "area_id": area.area_id,
                                             "proj_id": area.proj_id,
                                             "proj4": area.proj4_string,
                                             "shape": (area.x_size,
                                                       area.y_size)
                                             }
                            except AttributeError:
                                area_data = None

                            to_send = {"nominal_time": info["time_slot"],
                                       "uid": os.path.basename(fname),
                                       "uri": os.path.abspath(fname),
                                       "area": area_data,
                                       "productname": info["productname"]
                                       }

                            if self._topic is not None:
                                topic = self._topic
                                if area_data is not None:
                                    topic = compose(topic,  area_data)
                                else:
                                    topic = compose(topic,
                                                    {'area_id': 'satproj'})

                                msg = Message(self._topic, "file", to_send)
                                pub.send(str(msg))
                                self.logger.debug("Sent message: %s", str(msg))

                    del lcl
                    lcl = None
                    # After all the items have been processed, release the
                    # lock for the previous worker
                    if self.prev_lock is not None:
                        self.logger.debug("Writer releses lock of "
                                          "previous worker: %s",
                                          str(self.prev_lock))
                        release_lock(self.prev_lock)
                else:
                    time.sleep(1)

    def stop(self):
        """Stop writer."""
        self._loop = False

    @property
    def loop(self):
        """Property loop"""
        return self._loop
