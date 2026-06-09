import re
# from nautobot_data_validation_engine.custom_validators import DataComplianceRule, ComplianceError
from nautobot.data_validation.custom_validators import ComplianceError, DataComplianceRule
# class ValidateContacts(DataComplianceRule):
#     model = "extras.contact" # Ex: 'dcim.device'
#     enforce = False # True/False enforce flag

#     def audit_name_first_and_last(self):
#         # Your logic to determine if this function has succeeded or failed
#         if len(self.context["object"].name.split()) <= 1:
#             raise ComplianceError({"Name": "Contact must be first and last."})

#     # def audit_desired_name_two(self):
#     #     # Your logic to determine if this function has succeeded or failed
#     #     if "undesired_value" in self.context["object"].desired_attribute:
#     #         raise ComplianceError({"desired_attribute": "Desired message why it's invalid."})

#     def audit(self):
#         messages = {}
#         for fn in [self.audit_name_first_and_last]: # Add audit functions here
#             try:
#                 fn()
#             except ComplianceError as ex:
#                 messages.update(ex.message_dict)
#         if messages:
#             raise ComplianceError(messages)

class DeviceDataComplianceRules(DataComplianceRule):
    model = "dcim.device"
    enforce = False
    
    # Checks if a device name contains any special characters other than a dash (-), underscore (_), or period (.) using regex
    def audit_device_name_chars(self):
        if not re.match("^[a-zA-Z0-9\-_.]+$", self.context["object"].name):
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
