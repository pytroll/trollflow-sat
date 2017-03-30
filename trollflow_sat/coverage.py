"""Class for handling area coverage checks for Trollflow based Trollduction"""

import logging
import time

from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils
from mpop.projector import get_area_def
from trollsched.satpass import Pass


class CoverageCheck(AbstractWorkflowComponent):

    """Check scene coverage"""

    logger = logging.getLogger("Coverage")

    def __init__(self):
        super(CoverageCheck, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in coverage checker: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("Scene loader acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            utils.acquire_lock(context["prev_lock"])

        scene = context["content"]
        overpass = Pass(scene.info["platform_name"],
                        scene.info['start_time'],
                        scene.info['end_time'],
                        instrument=scene.info["sensor"][0])
        areas = []
        for area_name in scene.info["areas"]:
            self.logger.info("Checking coverage of %s", area_name)

            try:
                min_coverage = context["min_coverage"][area_name]
            except KeyError:
                self.logger.warning("No minimum coverage given, "
                                    "assuming 0 % coverage needed")
                areas.append(area_name)
                continue

            if covers(overpass, area_name, min_coverage, self.logger):
                areas.append(area_name)
            else:
                self.logger.info("Area coverage too low, skipping %s",
                                 area_name)
                continue

        if len(areas) > 0:
            scene.info["areas"] = areas
            context["output_queue"].put(scene)
        else:
            self.logger.info("No areas with enough coverage")

        if utils.release_locks([context["lock"]]):
            self.logger.debug("Scene loader releases own lock %s",
                              str(context["lock"]))
            time.sleep(1)

        # Wait until the lock has been released downstream
        if self.use_lock:
            utils.acquire_lock(context["lock"])
            utils.release_locks([context["lock"]])

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_locks([context["prev_lock"]], log=self.logger.debug,
                            log_msg="Scene loader releases lock of " +
                            "previous worker")

    def post_invoke(self):
        """Post-invoke"""
        pass


def covers(overpass, area_name, min_coverage, logger):
    try:
        area_def = get_area_def(area_name)
        if min_coverage == 0 or overpass is None:
            return True
        min_coverage /= 100.0
        coverage = overpass.area_coverage(area_def)
        if coverage <= min_coverage:
            logger.info("Coverage too small %.1f%% (out of %.1f%%) "
                        "with %s",
                        coverage * 100, min_coverage * 100,
                        area_name)
            return False
        else:
            logger.info("Coverage %.1f%% with %s",
                        coverage * 100, area_name)

    except AttributeError:
        logger.warning("Can't compute area coverage with %s!",
                       area_name)
    return True
