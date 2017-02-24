"""Classes for handling XYZ for Trollflow based Trollduction"""

import logging
import time

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow.utils import acquire_lock, release_lock


class TemplateClass(AbstractWorkflowComponent):

    """Do something"""

    logger = logging.getLogger("TemplateClass")

    def __init__(self):
        super(TemplateClass, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in TemplatePlugin: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("TemplatePlugin acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        self.logger.info("Doing something.")
        something = do_something_with_content(context["content"])
        context["output_queue"].put(something)

        if self.use_lock:
            self.logger.debug("TemplatePlugin releases own lock %s",
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
        self.logger.debug("Scene loader releses lock of previous worker")
        release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass


def do_something_with_content(something):
    """Do something"""
    return 2 * something
