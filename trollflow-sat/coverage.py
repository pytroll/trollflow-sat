"""Classes for handling XYZ for Trollflow based Trollduction"""

import logging

from trollflow.workflow_component import AbstractWorkflowComponent

class CoverageCheck(AbstractWorkflowComponent):

    """Check scene coverage"""

    logger = logging.getLogger("TemplateClass")

    def __init__(self):
        super(TemplateClass, self).__init__()

    def pre_invoke(self):
        """Pre-invoke"""
        pass

    def invoke(self, context):
        """Invoke"""
        self.logger.info("Checking coverage.")
        scene = context["content"]
        try:
area_def = context[""]
        try:
            min_coverage = context["min_coverage"]["content"]
        except KeyError:
            contest["output_queue"].put(scene)
            return
        if coverage_check(scene, min_coverage):
            context["output_queue"].put(scene)
        else:
            return

    def post_invoke(self):
        """Post-invoke"""
        pass

def covers(scene, area_item):
    try:
        area_def = get_area_def(area_item.attrib['id'])
        min_coverage = float(area_item.attrib.get('min_coverage', 0))
        if min_coverage == 0 or scene is None:
            return True
        min_coverage /= 100.0
        coverage = scene.area_coverage(area_def)
        if coverage <= min_coverage:
            self.logger.info("Coverage too small %.1f%% (out of %.1f%%) "
                             "with %s",
                             coverage * 100, min_coverage * 100,
                             area_item.attrib['name'])
            return False
        else:
            self.logger.info("Coverage %.1f%% with %s",
                             coverage * 100, area_item.attrib['name'])

    except AttributeError:
        self.logger.warning("Can't compute area coverage with %s!",
                            area_item.attrib['name'])
    return True
