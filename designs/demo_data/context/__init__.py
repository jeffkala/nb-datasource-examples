"""Context file for Demo Data Design."""

from nautobot_design_builder.context import Context
from nautobot_design_builder.errors import DesignValidationError
from nautobot_design_builder.context import context_file

@context_file("demo_context.yml")
class DemoDataDesignContext(Context):
    """Render context for Service Deployment Design."""
