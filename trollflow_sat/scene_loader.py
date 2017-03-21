
"""Class for reading satellite data for Trollflow based Trollduction"""

import logging
import yaml
import time
from urlparse import urlparse
from struct import error as StructError

from trollflow_sat import utils
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
            utils.acquire_lock(context["prev_lock"])

        instruments = context.get("instruments", None)
        if instruments is None:
            utils.release_locks([context["lock"], context["prev_lock"]],
                                log=self.logger.error,
                                log_msg="No instruments configured!")
            return

        with open(context["product_list"], "r") as fid:
            product_config = yaml.load(fid)

        # Read message
        msg = context['content']

        global_data = self.create_scene_from_message(msg, instruments)

        if global_data is None:
            utils.release_locks([context["lock"], context["prev_lock"]],
                                log=self.logger.info,
                                log_msg="Unable to create Scene, " +
                                "skipping data")
            return

        monitor_topic = context.get("monitor_topic", None)
        if monitor_topic is not None:
            nameservers = context.get("nameservers", None)
            port = context.get("port", 0)
            service = context.get("service", None)
            monitor_metadata = utils.get_monitor_metadata(msg.data,
                                                          status="start",
                                                          service=service)
            utils.send_message(monitor_topic,
                               "monitor",
                               monitor_metadata,
                               nameservers=nameservers, port=port)

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
                utils.acquire_lock(context["lock"])

            if "collection_area_id" in msg.data:
                if group != msg.data["collection_area_id"]:
                    utils.release_locks([context["lock"]],
                                        log=self.logger.debug,
                                        log_msg="Collection not for this " +
                                        "area, skipping")
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
                utils.release_locks([context["lock"]], log=self.logger.error,
                                    log_msg="Data could not be read!")
                continue

            global_data.info["areas"] = grp_area_def_names
            context["output_queue"].put(global_data)

            if utils.release_locks([context["lock"]]):
                self.logger.debug("Scene loader releases own lock %s",
                                  str(context["lock"]))
                # Wait 1 second to ensure next worker has time to acquire the
                # lock
                time.sleep(1)

        del global_data
        global_data = None

        # Wait until the lock has been released downstream
        if self.use_lock:
            utils.acquire_lock(context["lock"])
            utils.release_locks([context["lock"]])

        if monitor_topic is not None:
            monitor_metadata["status"] = "completed"
            utils.send_message(monitor_topic,
                               "monitor",
                               monitor_metadata,
                               nameservers=nameservers,
                               port=port)

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_lock([context["prev_lock"]], log=self.logger.debug,
                           log_msg="Scene loader releses lock of " +
                           "previous worker")

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
