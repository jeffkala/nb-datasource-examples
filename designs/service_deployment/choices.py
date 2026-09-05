"""Choicesets for Service Designs."""

from nautobot.core.choices import ChoiceSet


class ServiceTemplateChoice(ChoiceSet):  # pylint: disable=too-few-public-methods
    """Choiceset used by IPAM Site Design."""

    INTERNET_CIRCUIT = "internet-circuit"

    CHOICES = ((INTERNET_CIRCUIT, "New Internet Circuit"),)
