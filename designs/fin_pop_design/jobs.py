"""Initial data required for core sites."""
from nautobot.extras.jobs import ChoiceVar, StringVar
from nautobot_design_builder.design_job import DesignJob

from .choices import PopSizeChoice
from .context import InitialFinDesignContext


class InitialFinDesign(DesignJob):
    """Initialize the database with default values needed by the core site designs."""

    class Meta:
        """Metadata needed to implement the backbone site design."""

        name = "Initial FIN Design"
        commit_default = True
        design_file = "designs/0001_design.yaml.j2"
        context_class = InitialFinDesignContext
        nautobot_version = ">=2"

    pop_name = StringVar(regex=r"\w{3}\d+")

    size = ChoiceVar(choices=PopSizeChoice)
