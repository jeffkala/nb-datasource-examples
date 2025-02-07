from nautobot.dcim.models import Location
from nautobot_design_builder.context import Context, context_file
from nautobot_design_builder.errors import DesignValidationError


@context_file("context.yml")
class PopDesignContext(Context):
    """Render context for basic design"""

    pop_name: str
    pop_size: str

    def validate_new_pop(self):
        try:
            Location.objects.get(name__iexact=str(self.pop_name))
            raise DesignValidationError(f"Another site exist with the name {self.pop_name}")
        except Location.DoesNotExist:
            return
