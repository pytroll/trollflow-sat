"""Classes for generating image composites for Trollflow based Trollduction"""

import logging
import yaml
import time

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils
from trollflow.utils import acquire_lock, release_lock


class CompositeGenerator(AbstractWorkflowComponent):

    """Creates composites from a product config."""

    logger = logging.getLogger("Compositor")

    def __init__(self):
        super(CompositeGenerator, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in compositor: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("Compositor acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        data = context["content"]
        with open(context["product_list"], "r") as fid:
            product_config = yaml.load(fid)

        for prod in data.info["products"]:
            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Compositor acquires own lock %s",
                                  str(context["lock"]))
                acquire_lock(context["lock"])

            self.logger.info("Creating composite %s", prod)
            try:
                func = getattr(data.image, prod)
                img = func()
                if img is None:
                    release_lock(context["lock"])
                    continue
                img.info.update(data.info)
            except (AttributeError, KeyError):
                self.logger.warning("Invalid composite, skipping")
                release_lock(context["lock"])
                continue

            # Get filename and product name from product config
            fnames, productname = utils.create_fnames(
                data.info, product_config, prod)

            if fnames is None:
                self.logger.error("Could not generate valid filename(s), "
                                  "product not saved!")
            else:
                img.info["fnames"] = fnames
                img.info["productname"] = productname
                context["output_queue"].put(img)
            del img
            img = None

            if self.use_lock:
                self.logger.debug("Compositor releases own lock %s",
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
        self.logger.debug("Compositor releses lock of previous worker: %s",
                          str(context["prev_lock"]))
        release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass
