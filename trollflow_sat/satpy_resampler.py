"""Classes for generating image composites for Trollflow based
Trollduction using satpy"""

import logging
import time

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils
from trollflow.utils import ordered_load
try:
    from trollsched.satpass import Pass
except ImportError:
    Pass = None


class Resampler(AbstractWorkflowComponent):

    """Creates resampled local area scenes."""

    logger = logging.getLogger("Resampler")

    def __init__(self):
        super(Resampler, self).__init__()
        self.use_lock = False

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in resampler: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("Compositor acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            utils.acquire_lock(context["prev_lock"])

        # Check for terminator
        if context["content"] is None:
            context["output_queue"].put(None)
        else:
            # Process the scene
            self._process(context)

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_locks([context["prev_lock"]], log=self.logger.debug,
                            log_msg="Resampler releses lock of previous " +
                            "worker: %s" % str(context["prev_lock"]))

    def _process(self, context):
        """Process a context."""

        glbl = context["content"]["scene"]
        extra_metadata = context["content"]["extra_metadata"]

        with open(context["product_list"], "r") as fid:
            product_config = ordered_load(fid)

        # Handle config options
        kwargs = {}

        kwargs['mask_area'] = context.get('mask_area', True)
        self.logger.debug("Setting area masking to %s",
                          str(kwargs['mask_area']))

        kwargs['nprocs'] = context.get('nprocs', 1)
        self.logger.debug("Using %d CPUs for resampling.", kwargs['nprocs'])

        kwargs['resampler'] = context.get('resampler', "nearest")
        self.logger.debug("Using resampling method: '%s'.",
                          kwargs['resampler'])

        try:
            kwargs['cache_dir'] = context['cache_dir']
            self.logger.debug("Setting projection cache dir to %s",
                              kwargs['cache_dir'])
        except (AttributeError, KeyError):
            pass

        prod_list = product_config["product_list"]

        # Overpass for coverage calculations
        scn_metadata = glbl.attrs
        if product_config['common'].get('coverage_check', True) and Pass:
            overpass = Pass(scn_metadata['platform_name'],
                            scn_metadata['start_time'],
                            scn_metadata['end_time'],
                            instrument=scn_metadata['sensor'][0])
        else:
            overpass = None

        # Get the area ID from metadata dict
        area_id = extra_metadata['area_id']

        # Check for area coverage
        if overpass is not None:
            min_coverage = prod_list[area_id].get("min_coverage", 0.0)
            if not utils.covers(overpass, area_id, min_coverage,
                                self.logger):
                return

        kwargs['radius_of_influence'] = None
        try:
            area_config = product_config["product_list"][area_id]
            kwargs['radius_of_influence'] = \
                area_config.get("srch_radius", context["radius"])
        except (AttributeError, KeyError):
            kwargs['radius_of_influence'] = 10000.

        if kwargs['radius_of_influence'] is None:
            self.logger.debug("Using default search radius.")
        else:
            self.logger.debug("Using search radius %d meters.",
                              int(kwargs['radius_of_influence']))
        # Set lock if locking is used
        if self.use_lock:
            self.logger.debug("Resampler acquires own lock %s",
                              str(context["lock"]))
            utils.acquire_lock(context["lock"])

        if area_id == "satproj":
            self.logger.info("Using satellite projection")
            lcl = glbl
        else:
            metadata = glbl.attrs
            self.logger.info("Resampling time slot %s to area %s",
                             metadata["start_time"], area_id)
            lcl = glbl.resample(area_id, **kwargs)

        # Add area ID to the scene attributes so everything needed
        # in filename composing is in the same dictionary
        lcl.attrs["area_id"] = area_id

        metadata = extra_metadata.copy()
        metadata["product_config"] = product_config
        metadata["products"] = prod_list[area_id]['products']

        self.logger.debug("Inserting lcl (area: %s, start_time: %s) "
                          "to writer's queue",
                          area_id, str(scn_metadata["start_time"]))
        context["output_queue"].put({'scene': lcl,
                                     'extra_metadata': metadata})

        if utils.release_locks([context["lock"]]):
            self.logger.debug("Resampler releases own lock %s",
                              str(context["lock"]))
            # Wait 1 second to ensure next worker has time to acquire the
            # lock
            time.sleep(1)

        # Wait until the lock has been released downstream
        if self.use_lock:
            utils.acquire_lock(context["lock"])
            utils.release_locks([context["lock"]])

        del lcl
        lcl = None

    def post_invoke(self):
        """Post-invoke"""
        pass
