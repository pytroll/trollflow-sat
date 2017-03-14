
"""Class for reading satellite data for Trollflow based Trollduction"""

import logging
import yaml
import time
from urlparse import urlparse
from struct import error as StructError

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

        instruments = context.get("instruments", None)
        if instruments is None:
            self.logger.error("No instruments configured!")
            release_lock(context["lock"])
            release_lock(context["prev_lock"])
            return

        with open(context["product_list"], "r") as fid:
            product_config = yaml.load(fid)

        # Read message
        msg = context['content']

        global_data = self.create_scene_from_message(msg, instruments)

        if global_data is None:
            release_lock(context["lock"])
            release_lock(context["prev_lock"])
            self.logger.info("Unable to create Scene, skipping data")
            return

        fnames = get_data_fnames(msg)
        use_extern_calib = product_config["common"].get("use_extern_calib",
                                                        "False")
        keywords = {'use_extern_calib': use_extern_calib,
                    'load_again': True}
        if fnames is not None:
            keywords['filename'] = fnames
            self.logger.debug("Loading from files: %s", str(fnames))

        for group in product_config["groups"]:
            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Scene loader acquires own lock %s",
                                  str(context["lock"]))
                acquire_lock(context["lock"])

            if "collection_area_id" in msg.data:
                if group != msg.data["collection_area_id"]:
                    self.logger.debug("Collection not for this area, skipping")
                    release_lock(context["lock"])
                    continue

            grp_area_def_names = product_config["groups"][group]

            self.logger.debug("Loading data for group %s with areas %s",
                              group, str(grp_area_def_names))

            reqs = utils.get_prerequisites_yaml(global_data,
                                                product_config["product_list"],
                                                grp_area_def_names)

            self.logger.info("Loading required channels for this group: %s",
                             str(sorted(reqs)))

            try:
                if "satproj" in grp_area_def_names:
                    try:
                        del keywords["area_def_names"]
                    except KeyError:
                        pass
                    global_data.load(reqs, **keywords)
                else:
                    keywords["area_def_names"] = grp_area_def_names
                    global_data.load(reqs, **keywords)
            except (StructError, IOError):
                self.logger.error("Data could not be read!")
                release_lock(context["lock"])
                continue

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

    def create_scene_from_message(self, msg, instruments):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data, instruments)

    def create_scene_from_mda(self, mda, instruments):
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

        if sensor not in instruments:
            self.logger.debug("Unknown sensor, skipping data.")
            return None

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


def get_data_fnames(msg):
    """Get input data filenames from the message"""
    # Add list of filenames to info dictionary
    data_fnames = None

    if "uri" in msg.data:
        data_fnames = [urlparse(msg.data["uri"]).path, ]
    elif "dataset" in msg.data:
        data_fnames = \
            [urlparse(itm["uri"]).path for itm in msg.data["dataset"]]
    elif "collection" in msg.data:
        if "uri" in msg.data["collection"][0]:
            data_fnames = \
                [urlparse(itm["uri"]).path for itm in msg.data["collection"]]
        elif "dataset" in msg.data["collection"][0]:
            data_fnames = []
            for dset in msg.data["collection"]:
                for itm in dset["dataset"]:
                    data_fnames.append(urlparse(itm["uri"]).path)

    return data_fnames
