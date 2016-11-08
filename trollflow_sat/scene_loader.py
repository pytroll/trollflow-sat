
"""Class for reading satellite data for Trollflow based Trollduction"""

import logging
import yaml

from trollflow_sat import utils
from trollflow.workflow_component import AbstractWorkflowComponent
from mpop.satellites import GenericFactory as GF


class SceneLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message and loads the required channels."""

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
        global_data = self.create_scene_from_message(msg)
        if global_data is None:
            return

        use_extern_calib = product_config["common"].get("use_extern_calib",
                                                        "False")

        for group in product_config["groups"]:
            grp_area_def_names = product_config["groups"][group]
            reqs = utils.get_prerequisites_yaml(global_data,
                                                product_config["product_list"],
                                                grp_area_def_names)
            prev_reqs = {itm.name for itm in global_data.loaded_channels()}
            reqs_to_unload = prev_reqs - reqs
            if len(reqs_to_unload) > 0:
                self.logger.debug("Unloading unnecessary channels: %s",
                                  str(sorted(reqs_to_unload)))
                global_data.unload(reqs_to_unload)
            self.logger.info("Loading required channels for this group: %s",
                             str(sorted(reqs)))
            global_data.load(reqs, area_def_names=grp_area_def_names,
                             use_extern_calib=use_extern_calib)

            context["output_queue"].put(global_data)
        del global_data
        global_data = None

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
