"""Classes for generating image composites for Trollflow based Trollduction"""

import logging
import yaml

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils


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
        data = context["content"]
        with open(context["product_list"]["content"], "r") as fid:
            product_config = yaml.load(fid)

        # Set locking status, default to False
        self.use_lock = context.get("use_lock", {'content': False})['content']
        self.logger.debug("Locking is used in compositor: %s",
                          str(self.use_lock))

        for prod in data.info["products"]:
            self.logger.info("Creating composite %s", prod)
            try:
                func = getattr(data.image, prod)
                img = func()
                if img is None:
                    continue
                img.info.update(data.info)
            except (AttributeError, KeyError):
                self.logger.warning("Invalid composite, skipping")
                continue

            # Get filename and product name from product config
            data.info["areaname"] = data.area.area_id
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

            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Compositor acquires lock")
                utils.acquire_lock(context["lock"])
                self.logger.debug("Compositor lock was released")

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass
