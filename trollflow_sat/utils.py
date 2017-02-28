import os.path
import logging

from trollsift import compose
from trollsift.parser import _extract_parsedef as extract_parsedef

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
