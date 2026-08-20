"""Tests for custom validators."""

from django.test import TestCase
from nautobot.apps.models import ComplianceError
from nautobot.extras.models import Contact

from ..my_data_compliance_rules import ValidateContacts


class ValidateContactsTest(TestCase):
    """ValidateContacts Test Case."""

    def setUp(self):
        self.contact1 = Contact.objects.create(name="First", phone="888-555-6111", email="c1@example.com")
        self.contact2 = Contact.objects.create(name="First Last", phone="888-555-6112", email="c2@example.com")

    def test_contact_no_lastname_not_allowed(self):
        validator = ValidateContacts(self.contact1)
        with self.assertRaisesMessage(ComplianceError, "{'Name': ['Contact must be first and last.']}"):
            validator.audit()

    def test_contact_first_last_allowed(self):
        validator = ValidateContacts(self.contact2)
        validator.audit()
