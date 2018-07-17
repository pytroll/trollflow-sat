"""Class for reading satellite data for Trollflow based Trollduction
using satpy"""

import logging
import time
from copy import deepcopy

import yaml

from satpy import Scene
from trollflow.workflow_component import AbstractWorkflowComponent
from trollflow_sat import utils


class SceneLoader(AbstractWorkflowComponent):

    """Creates a scene object from a message and loads the required channels.
    """

    logger = logging.getLogger("SceneLoader")

    def __init__(self):
        super(SceneLoader, self).__init__()

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
            product_config = yaml.load(fid)
        msg = deepcopy(context['content'])
        for key, val in context.items():
            if key.startswith('ignore_') and val is True:
                msg.data.pop(key[7:], None)

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

        # use_extern_calib = product_config["common"].get("use_extern_calib",
        #                                                 "False")

        for group in product_config["groups"]:
            extra_metadata = {}
            # Set lock if locking is used
            if self.use_lock:
                self.logger.debug("Compositor acquires own lock %s",
                                  str(context["lock"]))
                utils.acquire_lock(context["lock"])

            if "collection_area_id" in msg.data:
                if group != msg.data["collection_area_id"]:
                    utils.release_locks([context["lock"]],
                                        log=self.logger.debug,
                                        log_msg="Collection not for this " +
                                        "area, skipping")
                    continue

            all_composites = \
                utils.get_satpy_group_composite_names(product_config,
                                                      group)

            # Check solar elevations and remove those composites that
            # are outside of their specified ranges
            composites = set()

            start_time = global_data.attrs['start_time']

            for composite in all_composites:
                if utils.bad_sunzen_range_satpy(
                        product_config,
                        group, composite,
                        start_time):
                    self.logger.info("Removing composite '%s'; out of "
                                     "valid solar angle range", composite)
                else:
                    composites.add(composite)

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
            try:
                extra_metadata['products'] = composites
            except AttributeError:
                extra_metadata['products'] = composites
            context["output_queue"].put({'scene': global_data,
                                         'extra_metadata': extra_metadata})

        # Add "terminator" to the queue
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
            monitor_metadata["status"] = "completed"
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
        start_time = (mda.get('start_time') or
                      mda.get('nominal_time') or
                      None)
        end_time = mda.get('end_time') or None

        platform_name = mda["platform_name"]

        if isinstance(mda['sensor'], (list, tuple, set)):
            sensor = mda['sensor'][0]
        else:
            sensor = mda['sensor']

        if sensor not in instruments:
            self.logger.debug("Unknown sensor, skipping data.")
            return None

        if msg_type == "dataset":
            filenames = []
            for dset in mda["dataset"]:
                filenames.append(dset["uri"])
        elif msg_type == "collection":
            filenames = []
            for col in mda['collection']:
                if 'dataset' in col:
                    for dset in col['dataset']:
                        filenames.append(dset["uri"])
                else:
                    filenames.append(col["uri"])
        else:
            filenames = mda['uri']

        if not isinstance(filenames, (list, set, tuple)):
            filenames = [filenames]

        # Create satellite scene

        # There can be several readers configured for one instance, so
        # try which matches.  If there's a reader specified in the
        # incoming message, use that.
        readers = list(mda.get('reader') or readers)
        for reader in readers:
            try:
                self.logger.debug("Trying reader %s", reader)
                global_data = Scene(filenames=filenames, reader=reader)
                self.logger.debug("Reader selected.")
                break
            except ValueError:
                continue

        try:
            global_data.attrs.update(mda)
            self.logger.debug("SCENE: %s", str(global_data.attrs))
        except AttributeError:
            global_data.info.update(mda)
            self.logger.debug("SCENE: %s", str(global_data.info))

        return global_data
