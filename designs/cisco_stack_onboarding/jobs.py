"""Initial data required for stacks."""

from nautobot_design_builder.design_job import DesignJob

from .context import CiscoStackDesignContext


class CiscoStackDesign(DesignJob):
    """Cisco Stack Design."""

    class Meta:
        """Metadata needed to create a new Cisco stack."""

        name = "Onboard Cisco Stack"
        description = "Find Stacked devices and create the stack as virtual chassis."
        commit_default = False
        design_file = "designs/0001_stack_design.yaml.j2"
        # design_files = [
        #     "designs/0001_stack_design.yaml.j2",
        #     "designs/0002_stack_design.yaml.j2",
        # ]
        context_class = CiscoStackDesignContext
        nautobot_version = ">=2"

    def run(self, dryrun: bool, **kwargs):
        """Run the job."""
        super().run(dryrun, **kwargs)
