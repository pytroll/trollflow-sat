"""Classes for generating image composites for Trollflow based Trollduction"""

import logging
import yaml

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils


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
        glbl = context["content"]
        with open(context["product_list"]["content"], "r") as fid:
            product_config = yaml.load(fid)

        # Handle config options
        try:
            precompute = context["precompute"]["content"]
            self.logger.debug("Setting precompute to %s", str(precompute))
        except KeyError:
            precompute = False
        try:
            nprocs = context["nprocs"]["content"]
            self.logger.debug("Using %d CPUs for resampling.", nprocs)
        except KeyError:
            nprocs = 1
        try:
            proj_method = context["proj_method"]["content"]
            self.logger.debug("Using resampling method: '%s'.", proj_method)
        except KeyError:
            proj_method = "nearest"
        try:
            area = glbl.area.area_id
            area_config = product_config["product_list"][area]
            radius = area_config.get("srch_radius",
                                     context["radius"]["content"])
        except (AttributeError, KeyError):
            radius = None

        if radius is None:
            self.logger.debug("Using default search radius.")
        else:
            self.logger.debug("Using search radius %d meters.", int(radius))

        prod_list = product_config["product_list"]
        for area_name in prod_list:
            # Reproject only needed channels
            channels = utils.get_prerequisites_yaml(glbl,
                                                    prod_list,
                                                    [area_name, ])
            self.logger.info("Resampling to area %s", area_name)
            lcl = glbl.project(area_name, channels=channels,
                               precompute=precompute,
                               mode=proj_method, radius=radius, nprocs=nprocs)
            lcl.info["areaname"] = area_name
            lcl.info["products"] = prod_list[area_name]['products']
            context["output_queue"].put(lcl)
            del lcl
            lcl = None

    def post_invoke(self):
        """Post-invoke"""
        pass
