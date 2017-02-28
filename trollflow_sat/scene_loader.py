
"""Class for reading satellite data for Trollflow based Trollduction"""

import logging
import yaml
import time

from trollflow_sat import utils
from trollflow.utils import acquire_lock, release_lock
from trollflow.workflow_component import AbstractWorkflowComponent
from mpop.satellites import GenericFactory as GF


class SceneLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message and loads the required channels.
    """

    logger = logging.getLogger("SceneLoader")

    def __init__(self):
        super(SceneLoader, self).__init__()

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
            self.logger.debug("Scene loader acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            acquire_lock(context["prev_lock"])

        with open(context["product_list"], "r") as fid:
            product_config = yaml.load(fid)

        # Read message
        msg = context['content']

        global_data = self.create_scene_from_message(msg)
        if global_data is None:
            release_lock(context["lock"])
            return

        use_extern_calib = product_config["common"].get("use_extern_calib",
                                                        "False")

        for group in product_config["groups"]:
            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Scene loader acquires own lock %s",
                                  str(context["lock"]))
                acquire_lock(context["lock"])
            grp_area_def_names = product_config["groups"][group]

            self.logger.debug("Loading data for group %s with areas %s",
                              group, str(grp_area_def_names))

            reqs = utils.get_prerequisites_yaml(global_data,
                                                product_config["product_list"],
                                                grp_area_def_names)

            self.logger.info("Loading required channels for this group: %s",
                             str(sorted(reqs)))

            if "satproj" in grp_area_def_names:
                global_data.load(reqs, load_again=True,
                                 use_extern_calib=use_extern_calib)
            else:
                global_data.load(reqs, load_again=True,
                                 area_def_names=grp_area_def_names,
                                 use_extern_calib=use_extern_calib)

            global_data.info["areas"] = grp_area_def_names
            context["output_queue"].put(global_data)

            if release_lock(context["lock"]):
                self.logger.debug("Scene loader releases own lock %s",
                                  str(context["lock"]))
                # Wait 1 second to ensure next worker has time to acquire the
                # lock
                time.sleep(1)

        del global_data
        global_data = None

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

    def create_scene_from_message(self, msg):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data)

    def create_scene_from_mda(self, mda):
        """Read the metadata *mda* and return a corresponding MPOP scene.
        """
        time_slot = (mda.get('start_time') or
                     mda.get('nominal_time') or
                     mda.get('end_time'))

        # orbit is not given for GEO satellites, use None
        if 'orbit_number' not in mda:
            mda['orbit_number'] = None

        platform = mda["platform_name"]

        self.logger.debug("platform %s time %s", str(platform), str(time_slot))

        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        # Create satellite scene
        global_data = GF.create_scene(satname=str(platform),
                                      satnumber='',
                                      instrument=str(sensor),
                                      time_slot=time_slot,
                                      orbit=mda['orbit_number'],
                                      variant=mda.get('variant', ''))
        self.logger.info("Creating scene for satellite %s and time %s",
                         str(platform), str(time_slot))

        # Update missing information to global_data.info{}
        # TODO: this should be fixed in mpop.
        global_data.info.update(mda)
        global_data.info['time'] = time_slot

        return global_data
