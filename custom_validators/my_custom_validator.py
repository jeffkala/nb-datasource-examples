from nautobot.apps.models import CustomValidator


class DeviceSerialValidator(CustomValidator):
    model = 'dcim.device'
    def clean(self):
        instance = self.context["object"]
        if not instance.serial_number:
            self.validation_error("Serial number is required.")
        if not re.match(r'[A-Z0-9]{10}', instance.serial_number):
            self.validation_error("Serial number must be 10 alphanumeric characters.")


custom_validators = [DeviceSerialValidator]
