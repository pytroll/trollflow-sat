"""Class for reading satellite data for Trollflow based Trollduction
using satpy"""

import logging
import yaml

from trollflow_sat import utils
from trollflow.workflow_component import AbstractWorkflowComponent
from satpy import Scene


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
        with open(context["product_list"]["content"], "r") as fid:
            product_config = yaml.load(fid)
        msg = context['content']

        # Set locking status, default to False
        self.use_lock = context.get("use_lock", {'content': False})['content']
        self.logger.debug("Locking is used in resampler: %s",
                          str(self.use_lock))

        global_data = self.create_scene_from_message(msg)
        if global_data is None:
            return

        # use_extern_calib = product_config["common"].get("use_extern_calib",
        #                                                 "False")

        for group in product_config["groups"]:
            composites = utils.get_satpy_group_composite_names(product_config,
                                                               group)
            prev_reqs = {itm.name for itm in global_data.datasets}
            reqs_to_unload = prev_reqs - composites
            if len(reqs_to_unload) > 0:
                self.logger.debug("Unloading unnecessary channels: %s",
                                  str(sorted(reqs_to_unload)))
                global_data.unload(list(reqs_to_unload))
            self.logger.info("Loading required data for this group: %s",
                             ', '.join(sorted(composites)))
            # use_extern_calib=use_extern_calib
            global_data.load(composites)

            context["output_queue"].put(global_data)

            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Resampler acquires lock")
                utils.acquire_lock(context["lock"])
                self.logger.debug("Resampler lock was released")

        del global_data
        global_data = None

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_lock(context["prev_lock"])

    def post_invoke(self):
        """Post-invoke"""
        pass

    def create_scene_from_message(self, msg):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data, msg.type)

    def create_scene_from_mda(self, mda, msg_type):
        """Read the metadata *mda* and return a corresponding MPOP scene.
        """
        start_time = (mda.get('start_time') or
                      mda.get('nominal_time') or
                      None)
        end_time = mda.get('end_time') or None

        platform_name = mda["platform_name"]

        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        if msg_type == "dataset":
            filenames = []
            for dset in mda["dataset"]:
                filenames.append(dset["uri"])
        elif msg_type == "collection":
            raise NotImplementedError
        else:
            filenames = mda['uri']

        if not isinstance(filenames, (list, set, tuple)):
            filenames = [filenames]

        # Create satellite scene
        global_data = Scene(platform_name=platform_name,
                            sensor=sensor,
                            start_time=start_time,
                            end_time=end_time,
                            filenames=filenames)

        global_data.info.update(mda)

        self.logger.debug("SCENE: %s", str(global_data.info))

        return global_data
