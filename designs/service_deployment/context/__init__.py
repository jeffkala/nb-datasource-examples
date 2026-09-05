"""Context file for Service Deployment Design."""

from nautobot_design_builder.context import Context
from nautobot_design_builder.errors import DesignValidationError


class ServiceDeploymentDesignContext(Context):
    """Render context for Service Deployment Design."""

    site_name: str
    service_template: str

    def validate_site_name(self):
        """Simple validations for Site."""
        if not self.device:
            raise DesignValidationError("Site Name cannot be empty.")
