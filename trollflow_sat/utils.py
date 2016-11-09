import os.path
import logging

from trollsift import compose

PATTERN = "{time:%Y%m%d_%H%M}_{platform_name}_{areaname}_{productname}.png"
FORMAT = "png"


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
    area_name = info["areaname"]

    # List of products
    products = product_config["product_list"][area_name]["products"]

    # Find output directory
    output_dir = products[prod_id].get("output_dir", "")
    if output_dir == "":
        output_dir = product_config["common"].get("output_dir", "")

    if output_dir == "":
        logging.warning("No output directory specified, "
                        "saving to current directory!")

    # Find filename pattern
    pattern = products[prod_id].get("fname_pattern", "")
    if pattern == "":
        pattern = product_config["common"].get("fname_pattern", "")

    if pattern == "":
        logging.warning("No pattern was given, using built-in default: %s",
                        PATTERN)
        pattern = PATTERN

    # Join output dir and filename pattern
    pattern = os.path.join(output_dir, pattern)

    # Find output formats
    formats = products[prod_id].get("formats", ["", ])
    if formats[0] == "":
        formats = product_config["common"].get("formats", [FORMAT, ])

    prod_name = products[prod_id]["productname"]
    info["productname"] = prod_name

    fnames = []
    for fmt in formats:
        info["format"] = fmt
        fnames.append(compose(pattern, info))
    return (fnames, prod_name)
