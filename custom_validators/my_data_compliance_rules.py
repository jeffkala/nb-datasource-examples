import re
from nautobot.apps.models import DataComplianceRule, ComplianceError

class ValidateContacts(DataComplianceRule):
    model = "extras.contact" # Ex: 'dcim.device'
    enforce = False # True/False enforce flag

    def audit_name_first_and_last(self):
        # Your logic to determine if this function has succeeded or failed
        if len(self.context["object"].name.split()) <= 1:
            raise ComplianceError({"Name": "Contact must be first and last."})

    def audit(self):
        messages = {}
        for fn in [self.audit_name_first_and_last]: # Add audit functions here
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)


class DeviceDataComplianceRules(DataComplianceRule):
    model = "dcim.device"
    enforce = True
    
    # Checks if a device name contains any special characters other than a dash (-), underscore (_), or period (.) using regex
    def audit_device_name_chars(self):
        if not re.match("^[a-zA-Z0-9._-]+$", self.context["object"].name):
            raise ComplianceError({"name": "Device name contains unallowed special characters."})
    
    def audit(self):
        messages = {}
        for fn in [self.audit_device_name_chars]:
            try:
                fn()
            except ComplianceError as ex:
                messages.update(ex.message_dict)
        if messages:
            raise ComplianceError(messages)
