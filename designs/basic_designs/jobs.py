"""Cisco stack discovery and virtual chassis creation job for Nautobot."""

from nautobot.apps.jobs import BooleanVar

from nautobot_design_builder.choices import DesignModeChoices

# from nautobot.dcim.models import LocationType
# from nautobot.extras.models import Role
from nautobot_design_builder.design_job import DesignJob

from .context import BasicDataDesignContext

name = "Basic Test"


class BasicDesign(DesignJob):
    """Basic Design."""

    debug = BooleanVar(
        default=False,
        description="Enable for more verbose logging.",
    )

    class Meta:
        """Metadata needed to create a new Cisco stack."""

        name = "Create Location Type"
        description = "Job to create a new Location Type in Nautobot."
        commit_default = False
        design_file = "designs/basic_design.yaml.j2"
        context_class = BasicDataDesignContext
        nautobot_version = ">=2"
        has_sensitive_variables = False
        # design_mode = DesignModeChoices.CLASSIC
        design_mode = DesignModeChoices.DEPLOYMENT
