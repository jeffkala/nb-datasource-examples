"""Context file for Cisco Stack Discovery."""

import logging

from django.core.exceptions import ObjectDoesNotExist
from nautobot.dcim.models import Device
from nautobot.extras.choices import LogLevelChoices
from nautobot.extras.models import JobResult
from nautobot_design_builder.context import Context


LOGGER = logging.getLogger(__name__)


def merge_switch_data(context, inventory_list, switch_status_list):
    """
    Merge switch inventory data with switch status data and filter out non-ready switches.

    This function combines switch inventory information with switch status information,
    matching switches by name or switch ID. It then filters out any switches that are
    not in a "Ready" state.

    Args:
        context: Job context object containing debug settings and job result for logging.
        inventory_list (list): List of dictionaries containing switch inventory data.
            Each dictionary should have a "name" key.
        switch_status_list (list): List of dictionaries containing switch status data.
            Each dictionary should have a "switch" key for the switch ID and a "state" key.

    Returns:
        dict: A dictionary mapping switch IDs to merged switch data dictionaries.
            Only includes switches with state "Ready". Each merged dictionary contains
            both inventory and status information for the switch.

    Note:
        - Switches are matched when inventory item name equals "Switch {swid}" or just "{swid}"
        - Non-ready switches are logged at debug level if context.debug is enabled
    """

    switch_status_map = {item["switch"]: item for item in switch_status_list}
    for swid in switch_status_map:
        for item in inventory_list:
            merged_item = item.copy()
            if item["name"] == f"Switch {swid}" or item["name"] == swid:
                switch_status_map[swid].update(merged_item)
    # Remove switches that are not Ready from the data
    non_ready_switches = []
    for swid, switch_data in switch_status_map.items():
        if switch_data.get("state") != "Ready":
            if context.debug:
                context.job_result.log(
                    level_choice=LogLevelChoices.LOG_DEBUG,
                    message=f"Removing switch from returned data: {switch_data} - Not Ready.",
                )
            non_ready_switches.append(swid)
    for swid in non_ready_switches:
        del switch_status_map[swid]
    return switch_status_map


class CiscoStackDesignContext(Context):
    """
    Render context for Cisco stack discovery design.
    
    This class handles the management and configuration of Cisco switch stacks,
    including retrieving stack data from devices, managing virtual chassis
    relationships, and providing utilities for stack member identification.
    
    Attributes:
        stack_data (list): Stack data retrieved from devices or sample data
        
    Methods:
        get_master_data(hostname): Retrieves Nautobot device object for master device
        get_master_device_member_number(get_stack_data_instance): Finds master device member number
        get_stack_data(): Retrieves stack information from devices or returns sample data
        clear_vc_members(get_stack_data_instance): Clears virtual chassis members from stack
        
    The class supports both live device data collection via Nornir and sample data
    for testing purposes. It processes Cisco switch stack information including
    member roles, MAC addresses, serial numbers, and stack topology.
    """

    def __init__(self, data: dict = None, job_result: JobResult = None):
        """Initialize the Cisco stack onboarding context."""
        super().__init__(data=data, job_result=job_result)

        self.stack_data = None  # Stack data retrieved from devices

    def get_master_data(self, hostname):
        """Get the Nautobot device object with the hostname matching the master device."""
        return Device.objects.get(name=hostname)

    def get_master_device_member_number(self, get_stack_data_instance):
        """Iterate through the stack data to find the master device member number."""
        master_device_hostname = list(get_stack_data_instance.keys())[0]
        for member_number, member_data in get_stack_data_instance[master_device_hostname].items():
            if member_data["role"].lower() in ["active", "master"]:
                if self.debug:
                    self.job_result.log(
                        level_choice=LogLevelChoices.LOG_DEBUG,
                        message=f"Found new master device member number: {member_number}",
                    )
                return member_number
        raise ValueError(f"No master device found in stack data for {master_device_hostname}")

    def _get_stack_data(self):
        """Static Stack Data for Testing."""
        return [
            {
                "WFCSL4W1": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "d4ad.bd02.5980",
                        "priority": "15",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "2",
                        "neighbor2": "6",
                        "name": "Switch 1",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326U0AY",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Member",
                        "mac_address": "d4ad.bd7a.b480",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "3",
                        "neighbor2": "1",
                        "name": "Switch 2",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326G0B2",
                    },
                    "3": {
                        "switch": "3",
                        "role": "Member",
                        "mac_address": "308b.b2ce.9f00",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "4",
                        "neighbor2": "2",
                        "name": "Switch 3",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326X05K",
                    },
                    "4": {
                        "switch": "4",
                        "role": "Member",
                        "mac_address": "d4ad.bd02.6e80",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "5",
                        "neighbor2": "3",
                        "name": "Switch 4",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326U0B1",
                    },
                    "5": {
                        "switch": "5",
                        "role": "Member",
                        "mac_address": "d4ad.bd7a.b680",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "6",
                        "neighbor2": "4",
                        "name": "Switch 5",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326C0B2",
                    },
                    "6": {
                        "switch": "6",
                        "role": "Member",
                        "mac_address": "308b.b2fc.a200",
                        "priority": "10",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "1",
                        "neighbor2": "5",
                        "name": "Switch 6",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2325U11L",
                    },
                }
            },
            {
                "WFCSL5E1": {
                    "1": {
                        "switch": "1",
                        "role": "Active",
                        "mac_address": "d4ad.bd29.a880",
                        "priority": "15",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "2",
                        "neighbor2": "4",
                        "name": "Switch 1",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326W0BR",
                    },
                    "2": {
                        "switch": "2",
                        "role": "Member",
                        "mac_address": "308b.b214.e980",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "3",
                        "neighbor2": "1",
                        "name": "Switch 2",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326G0AM",
                    },
                    "3": {
                        "switch": "3",
                        "role": "Member",
                        "mac_address": "308b.b2ce.cc00",
                        "priority": "5",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "4",
                        "neighbor2": "2",
                        "name": "Switch 3",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FOC2326X08P",
                    },
                    "4": {
                        "switch": "4",
                        "role": "Standby",
                        "mac_address": "d4ad.bd7a.7100",
                        "priority": "10",
                        "version": "V02",
                        "state": "Ready",
                        "status1": "OK",
                        "status2": "OK",
                        "neighbor1": "1",
                        "neighbor2": "3",
                        "name": "Switch 4",
                        "descr": "C9300-48P",
                        "pid": "C9300-48P",
                        "vid": "V02 ",
                        "sn": "FCW2326D05D",
                    },
                }
            },
        ]

    def get_stack_data(self):
        """Login to device and retrieve stack information."""
        if self.use_sample_data:
            self.job_result.log("Using sample data, skipping logging into devices.")
            # Store stack data for use in post_implementation
            self.stack_data = self._get_stack_data()
            return self.stack_data

    def clear_vc_members(self, get_stack_data_instance):
        """Clear the virtual chassis members from the stack data."""
        master_device_hostname = list(get_stack_data_instance.keys())[0]
        if len(get_stack_data_instance[master_device_hostname]) == 1:
            return  # Nothing to do if only 1 switch in the stack
        try:
            device = Device.objects.get(name=master_device_hostname)
            device.virtual_chassis = None
            device.save()
            self.job_result.log(
                level_choice=LogLevelChoices.LOG_DEBUG,
                message=f"Cleared virtual chassis for {master_device_hostname}",
            )
        except ObjectDoesNotExist:
            pass
        except Exception as e:
            self.job_result.log(
                level_choice=LogLevelChoices.LOG_ERROR,
                message=f"Error clearing virtual chassis for {master_device_hostname} - {e}",
            )
        for member_number in get_stack_data_instance[master_device_hostname].keys():
            try:
                device = Device.objects.get(name=f"{master_device_hostname}:{member_number}")
                device.virtual_chassis = None
                device.save()
                self.job_result.log(
                    level_choice=LogLevelChoices.LOG_DEBUG,
                    message=f"Cleared virtual chassis for {master_device_hostname}:{member_number}",
                )
            except ObjectDoesNotExist:
                pass
            except Exception as e:
                self.job_result.log(
                    level_choice=LogLevelChoices.LOG_ERROR,
                    message=f"Error clearing virtual chassis for {master_device_hostname}:{member_number} - {e}",
                )
        return True
