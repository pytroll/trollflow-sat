import os.path

from trollsift import compose

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

def create_fnames(info, prod_list, prod_id):
    """Create filename for product *prod*"""
    area_name = info["areaname"]

    products = prod_list["product_list"][area_name]["products"]
    try:
        out_dir = products[prod_id]["out_dir"]
    except KeyError:
        try:
            out_dir = prod_list["common"]["out_dir"]
        except KeyError:
            out_dir = ""
    pattern = os.path.join(out_dir, products[prod_id]["fname_pattern"])
    prod_name = products[prod_id]["productname"]
    formats = products[prod_id].get("formats", ["",])
    info["productname"] = prod_name
    if pattern is not None:
        fnames = []
        for fmt in formats:
            info["format"] = fmt
            fnames.append(compose(pattern, info))
        return (fnames, prod_name)
    else:
        return ([], prod_name)
