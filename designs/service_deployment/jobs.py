"""Initial data required for service deployments."""

import nautobot.core.forms as utilities_forms
from nautobot.apps.jobs import register_jobs
from nautobot.dcim.models import Location
from nautobot.extras.jobs import ChoiceVar, ObjectVar
from nautobot_design_builder.choices import DesignModeChoices
from nautobot_design_builder.design_job import DesignJob

from .choices import ServiceTemplateChoice
from .context import ServiceDeploymentDesignContext


class ServiceDeploymentDesign(DesignJob):
    """Service Deployment Design."""

    site_name = ObjectVar(
        model=Location,
        label="Location",
        description="Location to establish service deployment.",
        required=True,
    )
    service_template = ChoiceVar(
        choices=ServiceTemplateChoice,
        required=True,
        widget=utilities_forms.StaticSelect2(),
    )

    class Meta:
        """Metadata needed to create a service deployment."""

        name = "Service Deployment"
        description = "Deploy objects and configuration based on a service template."
        commit_default = False
        design_file = "designs/0001_service_deployment.yaml.j2"
        context_class = ServiceDeploymentDesignContext
        nautobot_version = ">=2"
        design_mode = DesignModeChoices.DEPLOYMENT

    def run(self, dryrun: bool, **kwargs):
        """Run the job."""
        super().run(dryrun, **kwargs)


register_jobs(ServiceDeploymentDesign)
