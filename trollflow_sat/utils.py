import logging
import os.path

from posttroll.message import Message
from posttroll.publisher import Publish
from trollflow.utils import acquire_lock as trollflow_acquire_lock
from trollflow.utils import release_lock
from trollsift import compose
from trollsift.parser import get_convert_dict

from satpy.resample import get_area_def

try:
    from pyorbital import astronomy
except ImportError:
    astronomy = None

try:
    import dpath.util
    DPATH_AVAILABLE = True
except ImportError:
    DPATH_AVAILABLE = False

PATTERN = "{time:%Y%m%d_%H%M}_{platform_name}_{areaname}_{productname}.png"

FORMAT_DEFAULTS = {'writer': 'geotiff',
                   'format': 'tif',
                   'fill_value': None}

LOGGER = logging.getLogger(__name__)


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
    formats = products[prod_id].get("formats", None)
    if formats is None:
        formats = product_config["common"].get("formats", [FORMAT_DEFAULTS])

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
        return None, None

    # Adjust filename pattern so that time_name is present.
    # Get parse definitions and try to figure out if there's
    # an item for time
    convert_dict = get_convert_dict(pattern)
    for key, val in convert_dict.items():
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


def get_format_settings(product_config, prod_id, area_id):
    """Get all the format settings for this product"""
    products = product_config["product_list"][area_id]["products"]
    formats = products[prod_id].get("formats", [{}])

    settings = []
    for fmt in formats:
        tmp = {}
        for key in FORMAT_DEFAULTS.keys():
            val = fmt.get(key, None) or FORMAT_DEFAULTS[key]
            tmp[key] = val
        settings.append(tmp)

    return settings


def bad_sunzen_range(product_config, area_id, composite, start_time):
    """Check if Sun zenith angle is valid at the configured location.
    SatPy version.
    """
    product_conf = \
        product_config["product_list"][area_id]["products"][composite]

    if ("sunzen_night_minimum" not in product_conf and
            "sunzen_day_maximum" not in product_conf):
        return False

    if astronomy is None:
        LOGGER.warning("Pyorbital not installed, unable to calculate "
                       "Sun zenith angles!")
        return False

    if "sunzen_lon" not in product_conf and "sunzen_lat" not in product_conf:
        LOGGER.warning("No 'sunzen_lon' or 'sunzen_lat' configured, "
                       "can\'t check Sun elevation.")
        return False

    lon = product_conf["sunzen_lon"]
    lat = product_conf["sunzen_lat"]
    sunzen = astronomy.sun_zenith_angle(start_time, lon, lat)
    LOGGER.debug("Sun zenith angle is %.2f degrees", sunzen)

    try:
        limit = product_conf["sunzen_night_minimum"]
        if sunzen < limit:
            return True
        else:
            return False
    except KeyError:
        pass

    limit = product_conf["sunzen_day_maximum"]
    if sunzen > limit:
        return True
    else:
        return False


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


def get_monitor_metadata(msg, status=None, service=None):
    """Collect metadata for monitoring message"""
    data = {"message_time": msg.time,
            "data_time": _get_data_time_from_message_data(msg.data),
            "platform_name": msg.data["platform_name"],
            "sensor": msg.data["sensor"],
            "orbit_number": _get_orbit_number_from_message_data(msg.data),
            "status": status,
            "service": service}

    return data


def release_locks(locks, log=None, log_msg=None):
    """Release locks and optionnally send log message to *log* function"""
    if not isinstance(locks, list):
        locks = [locks]
    if log is not None and log_msg is not None:
        log(log_msg)
    ret_vals = []
    for lock in locks:
        ret_vals.append(release_lock(lock))

    return max(ret_vals)


def acquire_lock(lock):
    """Acquire the given lock"""
    return trollflow_acquire_lock(lock)


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


def select_dict_items(src_dict, selection):
    """Creates a new dictionary containing elements listed in selection"""
    to_send = dict(src_dict) if '*' in selection else {}

    for dest_key in selection:
        if dest_key != '*':
            if isinstance(selection, dict):
                val = selection[dest_key]
                if '/' in val:
                    if not DPATH_AVAILABLE:
                        LOGGER.error("path expressions in publish_var but no dpath available")
                    else:
                        # use dpath for path expressions
                        info_without_empty_keys = \
                            {k: v for k, v in src_dict.items() if k}
                        if '*' in val:
                            # returns list
                            to_send[dest_key] = \
                                dpath.util.values(info_without_empty_keys, val)
                        else:
                            # returns single value
                            to_send[dest_key] = \
                                dpath.util.get(info_without_empty_keys, val)
                else:
                    to_send[dest_key] = src_dict.get(val)
            else:
                to_send[dest_key] = dest_key
    return to_send


def add_overviews(fnames, overviews, logger=None):
    """Add overviews to given files."""
    try:
        import rasterio
        from rasterio.enums import Resampling
    except ImportError:
        if logger is not None:
            logger.error("Can't add overviews, install rasterio")
        return

    if logger is not None:
        logger.info("Adding overviews")

    for fname in fnames:
        try:
            with rasterio.open(fname, 'r+') as dst:
                dst.build_overviews(overviews, Resampling.average)
                dst.update_tags(ns='rio_overview', resampling='average')
        except rasterio.RasterioIOError:
            pass


def read_writer_config(product_config, single_product_config, product, scn_metadata):
    """Execute writer config callback to add extra kwargs to the writer
        :Parameters:
            product_config: dict
                products config parameters
            single_product_config: dict
                config parameters of the current product
            product: str
                current product name
            scn_metadata: dict
                extra metadata

        :Returns:
            extra kwargs: dict
    """

    if "writer_config" in product_config['common']:
        func = product_config['common']['writer_config']['method']
        config_fname = product_config['common']['writer_config']['config_filename']
        return func(config_fname, product, single_product_config, scn_metadata)
    else:
        return dict()
