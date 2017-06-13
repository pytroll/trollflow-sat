"""Classes for handling file fetching for Trollflow based Trollduction"""

import logging
import os
import socket
import time
from tempfile import gettempdir
from urlparse import urlparse, urlsplit

import netifaces

from posttroll.message import Message
from trollflow.utils import acquire_lock, release_lock
from trollflow.workflow_component import AbstractWorkflowComponent

logger = logging.getLogger(__name__)


def get_local_ips():
    inet_addrs = [netifaces.ifaddresses(iface).get(netifaces.AF_INET)
                  for iface in netifaces.interfaces()]
    ips = []
    for addr in inet_addrs:
        if addr is not None:
            for add in addr:
                ips.append(add['addr'])
    return ips


def is_uri_on_server(uri, strict=False):
    """Check if the *uri* is designating a place on the server.

    If *strict* is True, the hostname has to be specified in the *uri* for the
    path to be considered valid.
    """
    url = urlparse(uri)
    try:
        url_ip = socket.gethostbyname(url.hostname)
    except (socket.gaierror, TypeError):
        if strict:
            return False
        try:
            os.stat(url.path)
        except OSError:
            return False
    else:
        if url.hostname == '':
            if strict:
                return False
            try:
                os.stat(url.path)
            except OSError:
                return False
        elif url_ip not in get_local_ips():
            return False
        else:
            try:
                os.stat(url.path)
            except OSError:
                return False
    return True


def check_uri(uri):
    """Check that the provided *uri* is on the local host and return the
    file path.
    """
    if isinstance(uri, (list, set, tuple)):
        paths = [check_uri(ressource) for ressource in uri]
        return paths
    url = urlparse(uri)
    try:
        if url.hostname:
            url_ip = socket.gethostbyname(url.hostname)

            if url_ip not in get_local_ips():
                try:
                    os.stat(url.path)
                except OSError:
                    raise IOError(
                        "Data file %s unaccessible from this host" % uri)

    except socket.gaierror:
        logger.warning("Couldn't check file location, running anyway")

    return url.path


class Fetcher(AbstractWorkflowComponent):

    """Fetch files from the network if needed, and sanitize the pathname."""

    def __init__(self):
        super(Fetcher, self).__init__()

    def pre_invoke(self):
        """Pre-invoke."""
        pass

    def invoke(self, context):
        """Invoke."""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        logger.debug("Locking is used in Fetcher: %s",
                     str(self.use_lock))
        if self.use_lock:
            logger.debug("Fetcher acquires lock of previous "
                         "worker: %s", str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        logger.info("Fetching files.")
        message = fetch_files(context["content"], context.get("destination",
                                                              gettempdir()))
        context["output_queue"].put(message)

        if self.use_lock:
            logger.debug("Fetcher releases own lock %s",
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
        logger.debug("Fetcher releases lock of previous worker")
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
    try:
        return check_uri(uri)
    except IOError:
        del destination
        raise NotImplementedError("Don't know how to fetch non local files")
