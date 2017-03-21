import os.path
import logging

from trollsift import compose
from trollsift.parser import _extract_parsedef as extract_parsedef
try:
    from pyorbital import astronomy
except ImportError:
    astronomy = None
from posttroll.publisher import Publish
from posttroll.message import Message
from trollflow.utils import release_lock

PATTERN = "{time:%Y%m%d_%H%M}_{platform_name}_{areaname}_{productname}.png"
FORMAT = "png"

LOGGER = logging.getLogger(__name__)


def get_prerequisites_yaml(global_data, prod_list, area_list):
    """Get composite prerequisite channels for a list of areas"""
    reqs = set()
    for area in area_list:
        for prod_id in prod_list[area]["products"]:
            try:
                composite = getattr(global_data.image, prod_id)
            except AttributeError:
                continue
            reqs |= composite.prerequisites
    return reqs


def create_fnames(info, product_config, prod_id):
    """Create filename for product *prod*"""
    area_id = info["area_id"]

    # List of products
    products = product_config["product_list"][area_id]["products"]

    # Get area name
    info["areaname"] = product_config["product_list"][area_id]["areaname"]

    # Find output directory
    output_dir = products[prod_id].get("output_dir", "")
    if output_dir == "":
        output_dir = product_config["common"].get("output_dir", "")

    if output_dir == "":
        LOGGER.warning("No output directory specified, "
                       "saving to current directory!")

    # Find filename pattern
    pattern = products[prod_id].get("fname_pattern", "")
    if pattern == "":
        pattern = product_config["common"].get("fname_pattern", "")

    if pattern == "":
        LOGGER.warning("No pattern was given, using built-in default: %s",
                       PATTERN)
        pattern = PATTERN

    # Join output dir and filename pattern
    pattern = os.path.join(output_dir, pattern)

    # Find output formats
    formats = products[prod_id].get("formats", ["", ])
    if formats[0] == "":
        formats = product_config["common"].get("formats", [{"format": FORMAT,
                                                            "writer": None}])

    prod_name = products[prod_id]["productname"]
    info["productname"] = prod_name

    # Find the name of the available 'nominal_time'
    time_name = None
    for key in info:
        if "time" in key and "end" not in key and "proc" not in key:
            time_name = key
            LOGGER.debug("metadata time name is '%s'", time_name)
            break

    if time_name is None and "time" in pattern:
        return None

    # Adjust filename pattern so that time_name is present.
    # Get parse definitions and try to figure out if there's
    # an item for time
    parsedefs, _ = extract_parsedef(pattern)
    for itm in parsedefs:
        if isinstance(itm, dict):
            key, val = itm.items()[0]
            if val is None:
                continue
            # Need to exclude 'end_time' and 'proc_time' / 'processing_time'
            if ("time" in key or "%" in val) and \
               "end" not in key and key != time_name:
                LOGGER.debug("Updating pattern from '%s' ...", pattern)

                while '{' + key in pattern:
                    pattern = pattern.replace('{' + key,
                                              '{' + time_name)
                LOGGER.debug("... to '%s'", pattern)

    fnames = []
    for fmt in formats:
        info["format"] = fmt["format"]
        # Ensure non-unicode filename
        fnames.append(str(compose(pattern, info)))

    return (fnames, prod_name)


def get_writer_names(product_config, prod_id, area_id):
    """Get writer names for the """
    products = product_config["product_list"][area_id]["products"]
    formats = products[prod_id].get("formats", ["", ])
    if formats[0] == "":
        formats = product_config["common"].get("formats", [{"format": FORMAT,
                                                            "writer": None}])
    writers = []
    for fmt in formats:
        writers.append(fmt.get("writer", None))

    return writers


def get_satpy_group_composite_names(product_config, group):
    """Parse composite names from the product config for the given
    group."""
    composites = set()
    prod_list = product_config['product_list']
    for group in product_config['groups'][group]:
        composites.update(set(prod_list[group]['products'].keys()))
    return composites


def get_satpy_area_composite_names(product_config, area_id):
    """Parse composite names from the product config for the given
    group."""
    prod_list = product_config['product_list']
    return prod_list[area_id]['products'].keys()


def find_time_name(info):
    """Try to find the name for 'nominal' time"""
    for key in info:
        if "time" in key and "end" not in key and "proc" not in key:
            return key
    return None


def bad_sunzen_range(area, product_config, area_id, prod, time_slot):
    """Check if Sun zenith angle is valid at the configured location."""
    product_conf = product_config["product_list"][area_id]["products"][prod]

    if ("sunzen_night_minimum" not in product_conf and
            "sunzen_day_maximum" not in product_conf):
        return False

    if astronomy is None:
        LOGGER.warning("Pyorbital not installed, unable to calculate "
                       "Sun zenith angles!")
        return False

    if area.lons is None:
        area.lons, area.lats = area.get_lonlats()

    lon, lat = None, None

    try:
        lon = product_conf["sunzen_lon"]
        lat = product_conf["sunzen_lat"]
    except KeyError:
        pass

    if lon is None or lat is None:
        try:
            x_idx = product_conf["sunzen_x_idx"]
            y_idx = product_conf["sunzen_y_idx"]
            lon = area.lons[x_idx]
            lat = area.lats[y_idx]
        except KeyError:
            pass

    if lon is None or lat is None:
        LOGGER.info("Using area center for Sun zenith angle calculation")
        y_idx = int(area.y_size / 2)
        x_idx = int(area.x_size / 2)
        lon, lat = area.get_lonlat(y_idx, x_idx)

    sunzen = astronomy.sun_zenith_angle(time_slot, lon, lat)
    LOGGER.debug("Sun zenith angle is %.2f degrees", sunzen)

    try:
        limit = product_conf["sunzen_night_minimum"]
        if sunzen < limit:
            return True
        else:
            return False
    except KeyError:
        pass

    try:
        limit = product_conf["sunzen_day_maximum"]
        if sunzen > limit:
            return True
        else:
            return False
    except KeyError:
        pass


def send_message(topic, msg_type, msg_data, nameservers=None, port=0):
    """Send monitoring message"""
    if nameservers is None:
        nameservers = []
    if not isinstance(nameservers, list):
        nameservers = [nameservers]

    with Publish("trollflow-sat", port=port,
                 nameservers=nameservers) as pub:
        msg = Message(topic, msg_type, msg_data)
        pub.send(str(msg))


def _get_data_time_from_message_data(msg_data):
    """Get data timestamp from message data"""
    if "nominal_time" in msg_data:
        data_time = msg_data["nominal_time"]
    elif "start_time" in msg_data:
        data_time = msg_data["start_time"]
    elif "time" in msg_data:
        data_time = msg_data["time"]
    else:
        data_time = None

    return data_time


def _get_orbit_number_from_message_data(msg_data):
    """Get orbit number from message data"""
    if "orbit_number" in msg_data:
        return msg_data["orbit_number"]
    else:
        return None


def get_monitor_metadata(msg, status=None):
    """Collect metadata for monitoring message"""
    data = {"message_time": msg.time,
            "data_time": _get_data_time_from_message_data(msg.data),
            "platform_name": msg.data["platform_name"],
            "sensor": msg.data["sensor"],
            "orbit_number": _get_orbit_number_from_message_data(msg.data),
            "status": status}

    return data


def relese_locks(locks, log=None, log_msg=None):
    """Release locks and optionnally send log message to *log* function"""
    if not isinstance(locks, list):
        locks = [locks]
    if log is not None and log_msg is not None:
        log(log_msg)
    ret_vals = []
    for lock in locks:
        ret_vals.append(release_lock(lock))

    return max(ret_vals)
