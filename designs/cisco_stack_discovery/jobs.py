"""Cisco stack discovery and virtual chassis creation job for Nautobot."""

from nautobot.apps.jobs import BooleanVar, MultiObjectVar, ObjectVar
from nautobot.dcim.models import Device, Location
from nautobot.extras.models import Role
from nautobot_design_builder.design_job import DesignJob

from .context import CiscoStackDesignContext

name = "Device Onboarding"


class CiscoStackDesign(DesignJob):
    """
    Cisco Stack Design.

    Nautobot job that checks for stackable switch neighbors and create a virtual switch
    to reflect all the member switches. This job connects to Cisco IOS-XE devices,
    issues commands to check for stack status, and uses a design template to create
    a virtual chassis in Nautobot using the name of the .
    Switch members are added using the discovered switch priorities using a suffix of :{{numeric}}.

    Attributes:
        debug (BooleanVar): Toggle for verbose logging.
        region (ObjectVar): Filter devices by region/country.
        locations (MultiObjectVar): Filter devices by specific locations.
        device_role (ObjectVar): Filter devices by role.
        devices (MultiObjectVar): Specific Cisco IOS-XE devices to check.

    Methods:
        run: Main job execution method that kicks off the design builder job.
        CiscoStackDesignContext: Creates a design for the Cisco stack based on the provided switch data.
    Requirements:
        - Devices must have a Secrets Group assigned with SSH credentials
        - Devices must be reachable via SSH
        - Devices must have a backup golden config available as the job checks for commands in the config
    """

    debug = BooleanVar(
        default=False,
        description="Enable for more verbose logging.",
    )
    use_sample_data = BooleanVar(
        default=False,
        description="Use static stack data for testing.",
    )

    region = ObjectVar(
        required=False,
        model=Location,
        query_params={"location_type": "Region"},
        description="Check devices belonging to the selected region/country.",
    )
    locations = MultiObjectVar(
        model=Location,
        query_params={"content_type": "dcim.device"},
        required=False,
        description="Check devices at selected locations.",
    )
    device_role = ObjectVar(
        model=Role,
        query_params={"content_types": "dcim.device"},
        required=False,
        description="Check devices with the selected role.",
    )
    devices = MultiObjectVar(
        model=Device,
        required=False,
        description="Select individual Cisco IOS-XE devices to check for stacking status.\nOverrides region, locations, and device role.",
        query_params={
            "platform": "cisco_xe",
            "status": "Deployed",
            "has_primary_ip": True,
        },
    )

    class Meta:
        """Metadata needed to create a new Cisco stack."""

        name = "Onboard Cisco Stack"
        description = (
            "Find Cisco IOS-XE stackable devices and create the stack as virtual chassis along with member switches."
        )
        commit_default = False
        design_file = "designs/0001_stack_design.yaml.j2"
        context_class = CiscoStackDesignContext
        nautobot_version = ">=2"
        has_sensitive_variables = False

    def __init__(self, *args, **kwargs):
        """Initialize the CiscoStackDesign job."""
        super().__init__(*args, **kwargs)
        self.stack_data = None

    def run(self, dryrun: bool, **kwargs):
        """Run the job."""
        super().run(dryrun, **kwargs)

    def post_implementation(self, context, environment):
        """Post-implementation actions."""
        for get_stack_data_instance in context.stack_data:
            self.cleanup_devices_post_re_election(get_stack_data_instance)

    def cleanup_devices_post_re_election(self, get_stack_data_instance):
        """
        Clean up old stack member devices after a stack master re-election.

        This method identifies and removes devices that share the same serial number
        as the current master device but have different hostnames. This cleanup is
        necessary after a stack re-election where device roles may have changed.

        Args:
            get_stack_data_instance (dict): Dictionary containing stack data where
                the first key represents the master device hostname.

        Raises:
            Exception: Re-raises any exception that occurs during the cleanup process
                after logging the error.

        Note:
            - The master device is identified as the first key in get_stack_data_instance
            - Old stack members are identified by matching serial numbers but different names
            - All matching old stack member devices are permanently deleted
        """
        master_device_hostname = list(get_stack_data_instance.keys())[0]
        try:
            master_device = Device.objects.get(name=master_device_hostname)
            old_stack_members = Device.objects.filter(serial=master_device.serial).exclude(name=master_device.name)
            if old_stack_members.exists():
                self.logger.info(f"Found old stack members {list(old_stack_members.values_list('name', flat=True))}")
                for device in old_stack_members:
                    device.delete()
                    self.logger.info(f"Deleted old stack member device: {device.name}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old stack members for {master_device_hostname}. ")
            raise e
