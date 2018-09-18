"""Class for reading satellite data for Trollflow based Trollduction
using satpy"""

import logging
import time
from copy import deepcopy

from six.moves.urllib.parse import urlparse

from satpy import Scene
from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils
from trollflow.utils import ordered_load


class SceneLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message and loads the required channels.
    """

    logger = logging.getLogger("SceneLoader")

    def __init__(self):
        super(SceneLoader, self).__init__()
        self.use_lock = False

    def pre_invoke(self):
        """Pre-invoke."""
        pass

    def invoke(self, context):
        """Invoke."""
        # Set locking status, default to False
        self.use_lock = context.get("use_lock", False)
        self.logger.debug("Locking is used in compositor: %s",
                          str(self.use_lock))
        if self.use_lock:
            self.logger.debug("Compositor acquires lock of previous "
                              "worker: %s", str(context["prev_lock"]))
            utils.acquire_lock(context["prev_lock"])

        instruments = context.get("instruments", None)
        if instruments is None:
            utils.release_locks([context["lock"], context["prev_lock"]],
                                log=self.logger.error,
                                log_msg="No instruments configured!")
            return

        readers = context.get("readers", None)

        with open(context["product_list"], "r") as fid:
            product_config = ordered_load(fid)
        msg = deepcopy(context['content'])
        for key, val in context.items():
            if key.startswith('ignore_') and val is True:
                msg.data.pop(key[7:], None)

        # Rename the instrument in the message if an alias is given for it
        instrument_aliases = context.get("instrument_aliases", {})
        if instrument_aliases:
            orig_sensor = msg.data['sensor']
            if isinstance(orig_sensor, list):
                orig_sensor = orig_sensor[0]
            sensor = instrument_aliases.get(orig_sensor, orig_sensor)
            if sensor != orig_sensor:
                msg.data['sensor'] = sensor
                self.logger.info(
                    "Adjusted message instrument name from %s to %s",
                orig_sensor, sensor)

        global_data = self.create_scene_from_message(msg, instruments,
                                                     readers=readers)
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

        # TODO: add usage of external calibration coefficients
        # use_extern_calib = product_config["common"].get("use_extern_calib",
        #                                                 "False")

        process_by_area = product_config["common"].get("process_by_area",
                                                       True)
        # Set lock if locking is used
        if self.use_lock:
            self.logger.debug("Compositor acquires own lock %s",
                              str(context["lock"]))
            utils.acquire_lock(context["lock"])

        for area_id in product_config["product_list"]:
            extra_metadata = {}

            # Check if the data was collected for specific area
            if "collection_area_id" in msg.data:
                if area_id != msg.data["collection_area_id"]:
                    utils.release_locks([context["lock"]],
                                        log=self.logger.debug,
                                        log_msg="Collection not for this " +
                                        "area, skipping")
                    continue

            # Load and unload composites for this area
            composites = self.load_composites(global_data, product_config,
                                              area_id)

            extra_metadata['products'] = composites
            extra_metadata['area_id'] = area_id
            context["output_queue"].put({'scene': global_data,
                                         'extra_metadata': extra_metadata})
            if process_by_area:
                context["output_queue"].put(None)


        # Add "terminator" to the queue to trigger computations for
        # this global scene, if not already done
        if not process_by_area:
            context["output_queue"].put(None)

        if utils.release_locks([context["lock"]]):
            self.logger.debug("Compositor releases own lock %s",
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
            monitor_metadata = utils.get_monitor_metadata(msg.data,
                                                          status="completed",
                                                          service=service)
            utils.send_message(monitor_topic,
                               "monitor",
                               monitor_metadata,
                               nameservers=nameservers,
                               port=port)

        # After all the items have been processed, release the lock for
        # the previous step
        utils.release_locks([context["prev_lock"]], log=self.logger.debug,
                            log_msg="Compositor releases lock of previous "
                            "worker")

    def post_invoke(self):
        """Post-invoke"""
        pass

    def create_scene_from_message(self, msg, instruments, readers=None):
        """Parse the message *msg* and return a corresponding MPOP scene.
        """
        if msg.type in ["file", 'collection', 'dataset']:
            return self.create_scene_from_mda(msg.data, msg.type, instruments,
                                              readers=readers)

    def create_scene_from_mda(self, mda, msg_type, instruments, readers=None):
        """Read the metadata *mda* and return a corresponding MPOP scene.
        """
        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        if sensor not in instruments:
            self.logger.debug("Unknown sensor, skipping data.")
            return None

        filenames = []
        if msg_type == "dataset":
            for dset in mda["dataset"]:
                filenames.append(urlparse(dset["uri"]).path)
        elif msg_type == "collection":
            for col in mda['collection']:
                if 'dataset' in col:
                    for dset in col['dataset']:
                        filenames.append(urlparse(dset["uri"]).path)
                else:
                    filenames.append(urlparse(col["uri"]).path)
        else:
            filenames.append(urlparse(mda['uri']).path)

        # Create satellite scene

        # There can be several readers configured for one instance, so
        # try which matches.  If there's a reader specified in the
        # incoming message, use that.
        readers = mda.get('reader') or readers
        if not isinstance(readers, list):
            readers = [readers]

        global_data = None
        for reader in readers:
            try:
                self.logger.debug("Trying reader %s", reader)
                global_data = Scene(filenames=filenames, reader=reader)
                self.logger.debug("Reader selected.")
                break
            except ValueError:
                continue

        if global_data is not None:
            self.logger.debug("SCENE: %s", str(global_data.attrs))
            global_data.attrs.update(mda)
        else:
            self.logger.warning("Scene not created.")

        return global_data

    def load_composites(self, global_data, product_config, area_id):
        """Get a set of composites for an area"""
        all_composites = \
            set(product_config["product_list"][area_id]['products'].keys())

        # Check solar elevations and remove those composites that
        # are outside of their specified ranges
        composites = set()

        start_time = global_data.attrs['start_time']

        # Check for Sun zenith angle limits
        for composite in all_composites:
            if utils.bad_sunzen_range(
                    product_config,
                    area_id, composite,
                    start_time):
                self.logger.info("Removing composite '%s'; out of "
                                 "valid solar angle range", composite)
            else:
                composites.add(composite)

        # Unload possible pre-existing composites that are not used
        prev_reqs = {itm.name for itm in global_data.datasets}
        reqs_to_unload = prev_reqs - composites
        if len(reqs_to_unload) > 0:
            self.logger.debug("Unloading unnecessary channels: %s",
                              str(sorted(reqs_to_unload)))
            global_data.unload(list(reqs_to_unload))

        self.logger.info("Loading required data for area %s: %s",
                         area_id,
                         ', '.join(sorted(composites)))
        global_data.load(composites)
