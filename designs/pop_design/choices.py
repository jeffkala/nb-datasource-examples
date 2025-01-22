"""Choicesets for golden config."""
from nautobot.core.choices import ChoiceSet


class PopSizeChoice(ChoiceSet):
    """Choiceset used by ComplianceRule."""

    SIZE_SMALL = "small"
    SIZE_LARGE = "large"

    CHOICES = (
        (SIZE_SMALL, "SMALL"),
        (SIZE_LARGE, "LARGE"),
    )
