"""Initial data required for core sites."""
from nautobot.extras.jobs import ChoiceVar, StringVar
from nautobot_design_builder.design_job import DesignJob
from nautobot_design_builder.choices import DesignModeChoices

from .choices import PopSizeChoice
from .context import PopDesignContext


class PopDesign(DesignJob):
    """New POP Deployment."""

    class Meta:
        """Metadata needed to implement pop deployment design."""

        name = "New POP Deployment"
        commit_default = True
        design_file = "designs/0001_design.yaml.j2"
        context_class = PopDesignContext
        nautobot_version = ">=2"
        design_mode = DesignModeChoices.DEPLOYMENT

    pop_name = StringVar(regex=r"\w{3}\d+")

    pop_size = ChoiceVar(choices=PopSizeChoice)
