"""Classes for generating image composites for Trollflow based Trollduction"""

import logging
import yaml
import time

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils
from trollflow.utils import acquire_lock, release_lock


class Resampler(AbstractWorkflowComponent):

    """Creates resampled local area scenes."""

    logger = logging.getLogger("Resampler")

    def __init__(self):
        super(Resampler, self).__init__()

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
            self.logger.debug("Resampler acquires lock of previous worker: %s",
                              str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        glbl = context["content"]
        with open(context["product_list"], "r") as fid:
            product_config = yaml.load(fid)

        # Handle config options
        try:
            precompute = context["precompute"]
            self.logger.debug("Setting precompute to %s", str(precompute))
        except KeyError:
            precompute = False
        try:
            nprocs = context["nprocs"]
            self.logger.debug("Using %d CPUs for resampling.", nprocs)
        except KeyError:
            nprocs = 1
        try:
            proj_method = context["proj_method"]
            self.logger.debug("Using resampling method: '%s'.", proj_method)
        except KeyError:
            proj_method = "nearest"
        try:
            radius = context["radius"]
        except (AttributeError, KeyError):
            radius = None

        if radius is None:
            self.logger.debug("Using default search radius.")
        else:
            self.logger.debug("Using search radius %d meters.", int(radius))

        prod_list = product_config["product_list"]
        for area_id in prod_list:
            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Resampler acquires own lock %s",
                                  str(context["lock"]))
                acquire_lock(context["lock"])
            if area_id not in glbl.info["areas"]:
                release_lock(context["lock"])
                continue

            # Reproject only needed channels
            channels = utils.get_prerequisites_yaml(glbl,
                                                    prod_list,
                                                    [area_id, ])
            if area_id == "satproj":
                self.logger.info("Using satellite projection")
                lcl = glbl
            else:
                self.logger.info("Resampling to area %s", area_id)
                lcl = glbl.project(area_id, channels=channels,
                                   precompute=precompute,
                                   mode=proj_method, radius=radius,
                                   nprocs=nprocs)
            lcl.info["area_id"] = area_id
            lcl.info["products"] = prod_list[area_id]['products']
            context["output_queue"].put(lcl)
            del lcl
            lcl = None
            if release_lock(context["lock"]):
                self.logger.debug("Resampler releases own lock %s",
                                  str(context["lock"]))
                # Wait 1 second to ensure next worker has time to acquire the
                # lock
                time.sleep(1)

        # Wait until the lock has been released downstream
        if self.use_lock:
            acquire_lock(context["lock"])
            release_lock(context["lock"])

        # After all the items have been processed, release the lock for
        # the previous step
        self.logger.debug("Resampler releses lock of previous worker: %s",
                          str(context["prev_lock"]))
        release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass
