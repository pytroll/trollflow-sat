"""Classes for handling XYZ for Trollflow based Trollduction"""

import logging

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow import utils


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
        self.use_lock = context.get("use_lock", {'content': False})['content']
        self.logger.debug("Locking is used in resampler: %s",
                          str(self.use_lock))

        self.logger.info("Doing something.")
        something = do_something_with_content(context["content"])
        context["output_queue"].put(something)

        # Set lock if locking is used
        if self.use_lock:
            self.logger.debug("TemplateClass acquires lock")
            utils.acquire_lock(context["lock"])
            self.logger.debug("TemplateClass lock was released")

        # After all the items have been processed, release the lock for
        # the previous worker
        utils.release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass


def do_something_with_content(something):
    """Do something"""
    return 2 * something
