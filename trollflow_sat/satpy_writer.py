
import logging
import os.path
from six.moves.queue import Empty as queue_empty
import time
from threading import Thread
from satpy.writers import compute_writer_results

from posttroll.message import Message
from posttroll.publisher import Publish
from trollflow_sat import utils
from trollsift import compose


class DataWriterContainer(object):

    '''Container for DataWriter instance
    '''

    logger = logging.getLogger("DataWriterContainer")
    _prev_lock = None

    def __init__(self, topic=None, port=0, nameservers=None,
                 save_settings=None, use_lock=False,
                 publish_vars=None):
        # store parameters for later writer restarts
        self.topic = topic
        self._input_queue = None
        self.output_queue = None
        self.thread = None
        self.use_lock = use_lock
        self._save_settings = save_settings or {}
        self._topic = topic
        self._port = port
        self._nameservers = nameservers
        self._publish_vars = publish_vars
        self._init_writer()

    def _init_writer(self):
        # Create a Writer instance
        self.writer = DataWriter(queue=self.input_queue,
                                 save_settings=self._save_settings,
                                 topic=self._topic,
                                 port=self._port,
                                 nameservers=self._nameservers,
                                 publish_vars=self._publish_vars,
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
        self._init_writer()

    def stop(self):
        '''Stop writer.'''
        self.logger.debug("Stopping writer.")
        self.writer.stop()
        if self.thread is not None:
            self.thread.join()
        self.logger.debug("Writer stopped.")
        self.thread = None

    def is_alive(self):
        """Return the thread status"""
        return self.thread.is_alive()


class DataWriter(Thread):

    """Writes data to disk.
    """

    logger = logging.getLogger("DataWriter")

    def __init__(self, queue=None, save_settings=None,
                 topic=None, port=0, nameservers=None, prev_lock=None,
                 publish_vars=None):
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
        self._publish_vars = publish_vars or {}
        self.data = []
        self.messages = []
        self.pub = None

    def run(self):
        """Run the thread."""
        self._loop = True
        # Get save settings
        kwargs = self._save_settings.copy()

        # Initialize publisher context
        with Publish("l2producer", port=self._port,
                     nameservers=self._nameservers) as self.pub:

            while self._loop:
                if self.queue is not None:
                    try:
                        data = self.queue.get(True, 1)
                        if self.prev_lock is not None:
                            self.logger.debug("Writer acquires lock of "
                                              "previous worker: %s",
                                              str(self.prev_lock))
                            utils.acquire_lock(self.prev_lock)
                        self.queue.task_done()
                    except queue_empty:
                        continue

                    if data is None:
                        self._compute()
                        self.data = []
                        self.messages = []
                    else:
                        self._process(data, **kwargs)

                    # After all the items have been processed, release the
                    # lock for the previous worker

                    if self.prev_lock is not None:
                        utils.release_locks([self.prev_lock],
                                            self.logger.debug,
                                            "Writer releses lock of "
                                            "previous worker: %s" %
                                            str(self.prev_lock))
                else:
                    time.sleep(1)

    def _compute(self):
        """Compute the data."""
        if self.data:
            self.logger.info("Processing and saving all data")
            compute_writer_results(self.data)
            if 'overviews' in self._save_settings:
                self._add_overviews()
            self._send_messages()

    def _add_overviews(self):
        """Add overviews (reduced resolution versions of image data) to the
        files.
        """
        fnames = [msg.data['uri'] for msg in self.messages]
        overviews = self._save_settings['overviews']
        utils.add_overviews(fnames, overviews, logger=self.logger)

    def _send_messages(self):
        """Send currently collected messages about completed datasets."""
        for msg in self.messages:
            self.pub.send(str(msg))
            self.logger.debug("Sent message: %s", str(msg))

    def _process(self, data, **kwargs):
        """Process the incoming data lazily"""
        lcl = data['scene']
        extra_metadata = data['extra_metadata']
        product_config = extra_metadata["product_config"]
        products = extra_metadata["products"]

        scn_metadata = lcl.attrs.copy()

        # Available composite names
        composite_names = [dset.name for dset in lcl.keys()]

        # Save all products in a delayed way
        for prod in products:
            # Skip the removed composites
            if prod not in composite_names:
                continue

            # Create output filenames for this product
            fnames, productname = \
                utils.create_fnames(scn_metadata,
                                    product_config,
                                    prod)
            # Some of the files might have specific format settings,
            # so read them from the config.  Use SatPy defaults if
            # nothing is given.
            fmts = utils.get_format_settings(product_config, prod,
                                             scn_metadata["area_id"])

            # Read writer specific kwargs 
            writer_kwargs = utils.read_writer_config(product_config, products[prod], prod, scn_metadata)
            kwargs.update(writer_kwargs)


            # Create delayed writer objects and messages
            for j, fname in enumerate(fnames):
                dset = lcl.save_datasets(datasets=[prod],
                                         filename=fname,
                                         writer=fmts[j]['writer'],
                                         fill_value=fmts[j]['fill_value'],
                                         compute=False,
                                         **kwargs)
                self.data.append(dset)

                # Create message for this file
                self._create_message(lcl[prod].attrs.get("area"),
                                     fname, scn_metadata, productname)

    def _create_message(self, area, fname, scn_metadata, productname):
        """Create a message and add it to self.messages"""
        # No messaging without a topic
        if self._topic is None:
            return

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

        # Create message metadata dictionary
        to_send = \
            utils.select_dict_items(scn_metadata,
                                    self._publish_vars)

        to_send_fix = {"nominal_time": scn_metadata["start_time"],
                       "uid": os.path.basename(fname),
                       "uri": os.path.abspath(fname),
                       "area": area_data,
                       "productname": productname
                       }
        to_send.update(to_send_fix)

        topic = self._topic
        # Compose the topic with area information
        if area_data is not None:
            tmp = to_send.copy()
            del tmp["area"]
            area_data.update(tmp)
            topic = compose(topic, area_data)
        else:
            topic = compose(topic,
                            {'area_id': 'satproj'})

        # Create message
        msg = Message(topic, "file", to_send)
        self.messages.append(msg)

    def stop(self):
        """Stop writer."""
        self._loop = False

    @property
    def loop(self):
        """Property loop"""
        return self._loop
