"""Classes for generating image composites for Trollflow based
Trollduction using satpy"""

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
        kwargs = {}
        try:
            kwargs['precompute'] = context["precompute"]["content"]
        except KeyError:
            kwargs['precompute'] = False
        self.logger.debug(
            "Setting precompute to %s", str(kwargs['precompute']))
        try:
            kwargs['nprocs'] = context["nprocs"]["content"]
        except KeyError:
            kwargs['nprocs'] = 1
        self.logger.debug("Using %d CPUs for resampling.", kwargs['nprocs'])
        try:
            kwargs['resampler'] = context["proj_method"]["content"]
        except KeyError:
            kwargs['resampler'] = "nearest"
        self.logger.debug(
            "Using resampling method: '%s'.", kwargs['resampler'])
        try:
            area = glbl.area.area_id
            area_config = product_config["product_list"][area]
            kwargs['radius_of_influence'] = \
                area_config.get("srch_radius", context["radius"]["content"],
                                10000.)
        except (AttributeError, KeyError):
            kwargs['radius_of_influence'] = 10000.

        if kwargs['radius_of_influence'] is None:
            self.logger.debug("Using default search radius.")
        else:
            self.logger.debug("Using search radius %d meters.",
                              int(kwargs['radius_of_influence']))

        prod_list = product_config["product_list"]
        for area_name in prod_list:
            # Reproject only needed channels
            dataset_names = \
                utils.get_satpy_area_composite_names(product_config, area_name)
            dataset_ids = [ds_id for ds_id in glbl.datasets.keys()
                           if ds_id.name in dataset_names]
            self.logger.info("Resampling time slot %s to area %s",
                             glbl.info["start_time"], area_name)
            lcl = glbl.resample(area_name, datasets=dataset_ids,
                                **kwargs)
            lcl.info["product_config"] = product_config
            lcl.info["areaname"] = area_name
            lcl.info["products"] = prod_list[area_name]['products']
            lcl.info["dataset_ids"] = dataset_ids
            self.logger.debug(
                "Inserting lcl (area: %s, start_time: %s) to writer's queue",
                              area_name, str(lcl.info["start_time"]))
            context["output_queue"].put(lcl)
            del lcl
            lcl = None

    def post_invoke(self):
        """Post-invoke"""
        pass
