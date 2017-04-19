"""Classes for handling file fetching for Trollflow based Trollduction"""

import logging
import time
from tempfile import gettempdir
from urlparse import urlsplit

from posttroll.message import Message
from trollflow.utils import acquire_lock, release_lock
from trollflow.workflow_component import AbstractWorkflowComponent


class Fetcher(AbstractWorkflowComponent):

    """Fetch files from the network if needed, and sanitize the pathname."""

    logger = logging.getLogger("Fetcher")

    def __init__(self):
        super(Fetcher, self).__init__()

    def pre_invoke(self):
        """Pre-invoke."""
        pass

    def invoke(self, context):
        """Invoke."""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in Fetcher: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("Fetcher acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        self.logger.info("Fetching files.")
        message = fetch_files(context["content"], context.get("destination",
                                                              gettempdir()))
        context["output_queue"].put(message)

        if self.use_lock:
            self.logger.debug("Fetcher releases own lock %s",
                              str(context["lock"]))
            release_lock(context["lock"])
            # Wait 1 second to ensure next worker has time to acquire the
            # lock
            time.sleep(1)

        # Wait until the lock has been released downstream
        if self.use_lock:
            acquire_lock(context["lock"])
            release_lock(context["lock"])

        # After all the items have been processed, release the lock for
        # the previous step
        self.logger.debug("Fetcher releases lock of previous worker")
        release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass


def fetch_files(message, destination):
    """Fetch files from the network"""
    new_message = Message(rawstr=str(message))
    if new_message.type == "dataset":
        for dset in new_message.data["dataset"]:
            dset["uri"] = fetch_file(dset["uri"], destination)
    elif new_message.type == "collection":
        raise NotImplementedError
    else:
        new_message.data["uri"] = fetch_file(new_message.data["uri"],
                                             destination)
    return new_message


def fetch_file(uri, destination):
    """Fetch a single file into `destination` and return its pathname."""
    url = urlsplit(uri)
    if url.scheme is None or url.scheme == 'file':
        return url.path
    else:
        del destination
        raise NotImplementedError("Don't know how to fetch over " + url.scheme)
